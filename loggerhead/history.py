#
# Copyright (C) 2008  Canonical Ltd.
#                     (Authored by Martin Albisetti <argentina@gmail.com>)
# Copyright (C) 2006  Robey Pointer <robey@lag.net>
# Copyright (C) 2006  Goffredo Baroncelli <kreijack@inwind.it>
# Copyright (C) 2005  Jake Edge <jake@edge2.net>
# Copyright (C) 2005  Matt Mackall <mpm@selenic.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

#
# This file (and many of the web templates) contains work based on the
# "bazaar-webserve" project by Goffredo Baroncelli, which is in turn based
# on "hgweb" by Jake Edge and Matt Mackall.
#


import bisect
import datetime
import logging
import re
import textwrap
import threading
import time
import urllib
from StringIO import StringIO

from loggerhead import search
from loggerhead import util
from loggerhead.wholehistory import compute_whole_history_data

import bzrlib
import bzrlib.branch
import bzrlib.diff
import bzrlib.errors
import bzrlib.progress
import bzrlib.revision
import bzrlib.textfile
import bzrlib.tsort
import bzrlib.ui

# bzrlib's UIFactory is not thread-safe
uihack = threading.local()


class ThreadSafeUIFactory (bzrlib.ui.SilentUIFactory):

    def nested_progress_bar(self):
        if getattr(uihack, '_progress_bar_stack', None) is None:
            pbs = bzrlib.progress.ProgressBarStack(
                      klass=bzrlib.progress.DummyProgress)
            uihack._progress_bar_stack = pbs
        return uihack._progress_bar_stack.get_nested()

bzrlib.ui.ui_factory = ThreadSafeUIFactory()

def is_branch(folder):
    try:
        bzrlib.branch.Branch.open(folder)
        return True
    except:
        return False


def clean_message(message):
    """Clean up a commit message and return it and a short (1-line) version.

    Commit messages that are long single lines are reflowed using the textwrap
    module (Robey, the original author of this code, apparently favored this
    style of message).
    """
    message = message.lstrip().splitlines()

    if len(message) == 1:
        message = textwrap.wrap(message[0])

    if len(message) == 0:
        # We can end up where when (a) the commit message was empty or (b)
        # when the message consisted entirely of whitespace, in which case
        # textwrap.wrap() returns an empty list.
        return [''], ''

    # Make short form of commit message.
    short_message = message[0]
    if len(short_message) > 60:
        short_message = short_message[:60] + '...'

    return message, short_message


def rich_filename(path, kind):
    if kind == 'directory':
        path += '/'
    if kind == 'symlink':
        path += '@'
    return path


# from bzrlib


class _RevListToTimestamps(object):
    """This takes a list of revisions, and allows you to bisect by date"""

    __slots__ = ['revid_list', 'repository']

    def __init__(self, revid_list, repository):
        self.revid_list = revid_list
        self.repository = repository

    def __getitem__(self, index):
        """Get the date of the index'd item"""
        return datetime.datetime.fromtimestamp(self.repository.get_revision(
                   self.revid_list[index]).timestamp)

    def __len__(self):
        return len(self.revid_list)


class History (object):
    """Decorate a branch to provide information for rendering.

    History objects are expected to be short lived -- when serving a request
    for a particular branch, open it, read-lock it, wrap a History object
    around it, serve the request, throw the History object away, unlock the
    branch and throw it away.

    :ivar _file_change_cache: xx
    """

    def __init__(self, branch, whole_history_data_cache):
        assert branch.is_locked(), (
            "Can only construct a History object with a read-locked branch.")
        self._file_change_cache = None
        self._branch = branch
        self._inventory_cache = {}
        self._branch_nick = self._branch.get_config().get_nickname()
        self.log = logging.getLogger('loggerhead.%s' % self._branch_nick)

        self.last_revid = branch.last_revision()

        whole_history_data = whole_history_data_cache.get(self.last_revid)
        if whole_history_data is None:
            whole_history_data = compute_whole_history_data(branch)
            whole_history_data_cache[self.last_revid] = whole_history_data

        (self._revision_graph, self._full_history, self._revision_info,
         self._revno_revid, self._merge_sort, self._where_merged,
         ) = whole_history_data

    def use_file_cache(self, cache):
        self._file_change_cache = cache

    @property
    def has_revisions(self):
        return not bzrlib.revision.is_null(self.last_revid)

    def get_config(self):
        return self._branch.get_config()

    def get_revno(self, revid):
        if revid not in self._revision_info:
            # ghost parent?
            return 'unknown'
        (seq, revid, merge_depth,
         revno_str, end_of_merge) = self._revision_info[revid]
        return revno_str

    def get_revids_from(self, revid_list, start_revid):
        """
        Yield the mainline (wrt start_revid) revisions that merged each
        revid in revid_list.
        """
        if revid_list is None:
            revid_list = self._full_history
        revid_set = set(revid_list)
        revid = start_revid

        def introduced_revisions(revid):
            r = set([revid])
            seq, revid, md, revno, end_of_merge = self._revision_info[revid]
            i = seq + 1
            while i < len(self._merge_sort) and self._merge_sort[i][2] > md:
                r.add(self._merge_sort[i][1])
                i += 1
            return r
        while 1:
            if bzrlib.revision.is_null(revid):
                return
            if introduced_revisions(revid) & revid_set:
                yield revid
            parents = self._revision_graph[revid]
            if len(parents) == 0:
                return
            revid = parents[0]

    def get_short_revision_history_by_fileid(self, file_id):
        # FIXME: would be awesome if we could get, for a folder, the list of
        # revisions where items within that folder changed.i
        try:
            # FIXME: Workaround for bzr versions prior to 1.6b3.
            # Remove me eventually pretty please  :)
            w = self._branch.repository.weave_store.get_weave(
                    file_id, self._branch.repository.get_transaction())
            w_revids = w.versions()
            revids = [r for r in self._full_history if r in w_revids]
        except AttributeError:
            possible_keys = [(file_id, revid) for revid in self._full_history]
            get_parent_map = self._branch.repository.texts.get_parent_map
            # We chunk the requests as this works better with GraphIndex.
            # See _filter_revisions_touching_file_id in bzrlib/log.py
            # for more information.
            revids = []
            chunk_size = 1000
            for start in xrange(0, len(possible_keys), chunk_size):
                next_keys = possible_keys[start:start + chunk_size]
                revids += [k[1] for k in get_parent_map(next_keys)]
            del possible_keys, next_keys
        return revids

    def get_revision_history_since(self, revid_list, date):
        # if a user asks for revisions starting at 01-sep, they mean inclusive,
        # so start at midnight on 02-sep.
        date = date + datetime.timedelta(days=1)
        # our revid list is sorted in REVERSE date order,
        # so go thru some hoops here...
        revid_list.reverse()
        index = bisect.bisect(_RevListToTimestamps(revid_list,
                                                   self._branch.repository),
                              date)
        if index == 0:
            return []
        revid_list.reverse()
        index = -index
        return revid_list[index:]

    def get_search_revid_list(self, query, revid_list):
        """
        given a "quick-search" query, try a few obvious possible meanings:

            - revision id or # ("128.1.3")
            - date (US style "mm/dd/yy", earth style "dd-mm-yy", or \
iso style "yyyy-mm-dd")
            - comment text as a fallback

        and return a revid list that matches.
        """
        # FIXME: there is some silliness in this action.  we have to look up
        # all the relevant changes (time-consuming) only to return a list of
        # revids which will be used to fetch a set of changes again.

        # if they entered a revid, just jump straight there;
        # ignore the passed-in revid_list
        revid = self.fix_revid(query)
        if revid is not None:
            if isinstance(revid, unicode):
                revid = revid.encode('utf-8')
            changes = self.get_changes([revid])
            if (changes is not None) and (len(changes) > 0):
                return [revid]

        date = None
        m = self.us_date_re.match(query)
        if m is not None:
            date = datetime.datetime(util.fix_year(int(m.group(3))),
                                     int(m.group(1)),
                                     int(m.group(2)))
        else:
            m = self.earth_date_re.match(query)
            if m is not None:
                date = datetime.datetime(util.fix_year(int(m.group(3))),
                                         int(m.group(2)),
                                         int(m.group(1)))
            else:
                m = self.iso_date_re.match(query)
                if m is not None:
                    date = datetime.datetime(util.fix_year(int(m.group(1))),
                                             int(m.group(2)),
                                             int(m.group(3)))
        if date is not None:
            if revid_list is None:
                # if no limit to the query was given,
                # search only the direct-parent path.
                revid_list = list(self.get_revids_from(None, self.last_revid))
            return self.get_revision_history_since(revid_list, date)

    revno_re = re.compile(r'^[\d\.]+$')
    # the date regex are without a final '$' so that queries like
    # "2006-11-30 12:15" still mostly work.  (i think it's better to give
    # them 90% of what they want instead of nothing at all.)
    us_date_re = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d\d(\d\d?))')
    earth_date_re = re.compile(r'^(\d{1,2})-(\d{1,2})-(\d\d(\d\d?))')
    iso_date_re = re.compile(r'^(\d\d\d\d)-(\d\d)-(\d\d)')

    def fix_revid(self, revid):
        # if a "revid" is actually a dotted revno, convert it to a revid
        if revid is None:
            return revid
        if revid == 'head:':
            return self.last_revid
        try:
            if self.revno_re.match(revid):
                revid = self._revno_revid[revid]
        except KeyError:
            raise bzrlib.errors.NoSuchRevision(self._branch_nick, revid)
        return revid

    def get_file_view(self, revid, file_id):
        """
        Given a revid and optional path, return a (revlist, revid) for
        navigation through the current scope: from the revid (or the latest
        revision) back to the original revision.

        If file_id is None, the entire revision history is the list scope.
        """
        if revid is None:
            revid = self.last_revid
        if file_id is not None:
            # since revid is 'start_revid', possibly should start the path
            # tracing from revid... FIXME
            revlist = list(self.get_short_revision_history_by_fileid(file_id))
            revlist = list(self.get_revids_from(revlist, revid))
        else:
            revlist = list(self.get_revids_from(None, revid))
        return revlist

    def get_view(self, revid, start_revid, file_id, query=None):
        """
        use the URL parameters (revid, start_revid, file_id, and query) to
        determine the revision list we're viewing (start_revid, file_id, query)
        and where we are in it (revid).

            - if a query is given, we're viewing query results.
            - if a file_id is given, we're viewing revisions for a specific
              file.
            - if a start_revid is given, we're viewing the branch from a
              specific revision up the tree.

        these may be combined to view revisions for a specific file, from
        a specific revision, with a specific search query.

        returns a new (revid, start_revid, revid_list) where:

            - revid: current position within the view
            - start_revid: starting revision of this view
            - revid_list: list of revision ids for this view

        file_id and query are never changed so aren't returned, but they may
        contain vital context for future url navigation.
        """
        if start_revid is None:
            start_revid = self.last_revid

        if query is None:
            revid_list = self.get_file_view(start_revid, file_id)
            if revid is None:
                revid = start_revid
            if revid not in revid_list:
                # if the given revid is not in the revlist, use a revlist that
                # starts at the given revid.
                revid_list = self.get_file_view(revid, file_id)
                start_revid = revid
            return revid, start_revid, revid_list

        # potentially limit the search
        if file_id is not None:
            revid_list = self.get_file_view(start_revid, file_id)
        else:
            revid_list = None
        revid_list = search.search_revisions(self._branch, query)
        if revid_list and len(revid_list) > 0:
            if revid not in revid_list:
                revid = revid_list[0]
            return revid, start_revid, revid_list
        else:
            # XXX: This should return a message saying that the search could
            # not be completed due to either missing the plugin or missing a
            # search index.
            return None, None, []

    def get_inventory(self, revid):
        if revid not in self._inventory_cache:
            self._inventory_cache[revid] = (
                self._branch.repository.get_revision_inventory(revid))
        return self._inventory_cache[revid]

    def get_path(self, revid, file_id):
        if (file_id is None) or (file_id == ''):
            return ''
        path = self.get_inventory(revid).id2path(file_id)
        if (len(path) > 0) and not path.startswith('/'):
            path = '/' + path
        return path

    def get_file_id(self, revid, path):
        if (len(path) > 0) and not path.startswith('/'):
            path = '/' + path
        return self.get_inventory(revid).path2id(path)

    def get_merge_point_list(self, revid):
        """
        Return the list of revids that have merged this node.
        """
        if '.' not in self.get_revno(revid):
            return []

        merge_point = []
        while True:
            children = self._where_merged.get(revid, [])
            nexts = []
            for child in children:
                child_parents = self._revision_graph[child]
                if child_parents[0] == revid:
                    nexts.append(child)
                else:
                    merge_point.append(child)

            if len(nexts) == 0:
                # only merge
                return merge_point

            while len(nexts) > 1:
                # branch
                next = nexts.pop()
                merge_point_next = self.get_merge_point_list(next)
                merge_point.extend(merge_point_next)

            revid = nexts[0]

    def simplify_merge_point_list(self, revids):
        """if a revision is already merged, don't show further merge points"""
        d = {}
        for revid in revids:
            revno = self.get_revno(revid)
            revnol = revno.split(".")
            revnos = ".".join(revnol[:-2])
            revnolast = int(revnol[-1])
            if revnos in d.keys():
                m = d[revnos][0]
                if revnolast < m:
                    d[revnos] = (revnolast, revid)
            else:
                d[revnos] = (revnolast, revid)

        return [d[revnos][1] for revnos in d.keys()]

    def get_branch_nicks(self, changes):
        """
        given a list of changes from L{get_changes}, fill in the branch nicks
        on all parents and merge points.
        """
        fetch_set = set()
        for change in changes:
            for p in change.parents:
                fetch_set.add(p.revid)
            for p in change.merge_points:
                fetch_set.add(p.revid)
        p_changes = self.get_changes(list(fetch_set))
        p_change_dict = dict([(c.revid, c) for c in p_changes])
        for change in changes:
            # arch-converted branches may not have merged branch info :(
            for p in change.parents:
                if p.revid in p_change_dict:
                    p.branch_nick = p_change_dict[p.revid].branch_nick
                else:
                    p.branch_nick = '(missing)'
            for p in change.merge_points:
                if p.revid in p_change_dict:
                    p.branch_nick = p_change_dict[p.revid].branch_nick
                else:
                    p.branch_nick = '(missing)'

    def get_changes(self, revid_list):
        """Return a list of changes objects for the given revids.

        Revisions not present and NULL_REVISION will be ignored.
        """
        changes = self.get_changes_uncached(revid_list)
        if len(changes) == 0:
            return changes

        # some data needs to be recalculated each time, because it may
        # change as new revisions are added.
        for change in changes:
            merge_revids = self.simplify_merge_point_list(
                               self.get_merge_point_list(change.revid))
            change.merge_points = [
                util.Container(revid=r,
                revno=self.get_revno(r)) for r in merge_revids]
            if len(change.parents) > 0:
                change.parents = [util.Container(revid=r,
                    revno=self.get_revno(r)) for r in change.parents]
            change.revno = self.get_revno(change.revid)

        parity = 0
        for change in changes:
            change.parity = parity
            parity ^= 1

        return changes

    def get_changes_uncached(self, revid_list):
        # FIXME: deprecated method in getting a null revision
        revid_list = filter(lambda revid: not bzrlib.revision.is_null(revid),
                            revid_list)
        parent_map = self._branch.repository.get_graph().get_parent_map(
                         revid_list)
        # We need to return the answer in the same order as the input,
        # less any ghosts.
        present_revids = [revid for revid in revid_list
                          if revid in parent_map]
        rev_list = self._branch.repository.get_revisions(present_revids)

        return [self._change_from_revision(rev) for rev in rev_list]

    def _get_deltas_for_revisions_with_trees(self, revisions):
        """Produce a list of revision deltas.

        Note that the input is a sequence of REVISIONS, not revision_ids.
        Trees will be held in memory until the generator exits.
        Each delta is relative to the revision's lefthand predecessor.
        (This is copied from bzrlib.)
        """
        required_trees = set()
        for revision in revisions:
            required_trees.add(revision.revid)
            required_trees.update([p.revid for p in revision.parents[:1]])
        trees = dict((t.get_revision_id(), t) for
                     t in self._branch.repository.revision_trees(
                         required_trees))
        ret = []
        for revision in revisions:
            if not revision.parents:
                old_tree = self._branch.repository.revision_tree(
                    bzrlib.revision.NULL_REVISION)
            else:
                old_tree = trees[revision.parents[0].revid]
            tree = trees[revision.revid]
            ret.append(tree.changes_from(old_tree))
        return ret

    def _change_from_revision(self, revision):
        """
        Given a bzrlib Revision, return a processed "change" for use in
        templates.
        """
        commit_time = datetime.datetime.fromtimestamp(revision.timestamp)

        parents = [util.Container(revid=r,
                   revno=self.get_revno(r)) for r in revision.parent_ids]

        message, short_message = clean_message(revision.message)

        try:
            authors = revision.get_apparent_authors()
        except AttributeError:
            authors = [revision.get_apparent_author()]

        entry = {
            'revid': revision.revision_id,
            'date': commit_time,
            'authors': authors,
            'branch_nick': revision.properties.get('branch-nick', None),
            'short_comment': short_message,
            'comment': revision.message,
            'comment_clean': [util.html_clean(s) for s in message],
            'parents': revision.parent_ids,
        }
        return util.Container(entry)

    def get_file_changes_uncached(self, entries):
        delta_list = self._get_deltas_for_revisions_with_trees(entries)

        return [self.parse_delta(delta) for delta in delta_list]

    def get_file_changes(self, entries):
        if self._file_change_cache is None:
            return self.get_file_changes_uncached(entries)
        else:
            return self._file_change_cache.get_file_changes(entries)

    def add_changes(self, entry):
        changes = self.get_file_changes([entry])[0]
        entry.changes = changes

    def get_file(self, file_id, revid):
        "returns (path, filename, data)"
        inv = self.get_inventory(revid)
        inv_entry = inv[file_id]
        rev_tree = self._branch.repository.revision_tree(inv_entry.revision)
        path = inv.id2path(file_id)
        if not path.startswith('/'):
            path = '/' + path
        return path, inv_entry.name, rev_tree.get_file_text(file_id)

    def parse_delta(self, delta):
        """
        Return a nested data structure containing the changes in a delta::

            added: list((filename, file_id)),
            renamed: list((old_filename, new_filename, file_id)),
            deleted: list((filename, file_id)),
            modified: list(
                filename: str,
                file_id: str,
            ),
            text_changes: list((filename, file_id)),
        """
        added = []
        modified = []
        renamed = []
        removed = []
        text_changes = []

        for path, fid, kind in delta.added:
            added.append(util.Container(
                filename=rich_filename(path, kind), file_id=fid, kind=kind))
            if kind == 'file':
                text_changes.append(util.Container(
                    filename=rich_filename(path, kind), file_id=fid))

        for path, fid, kind, text_modified, meta_modified in delta.modified:
            modified.append(util.Container(
                filename=rich_filename(path, kind), file_id=fid))
            if text_modified:
                text_changes.append(util.Container(
                    filename=rich_filename(path, kind), file_id=fid))

        for old_path, new_path, fid, kind, text_modified, meta_modified in \
                delta.renamed:
            renamed.append(util.Container(
                old_filename=rich_filename(old_path, kind),
                new_filename=rich_filename(new_path, kind), file_id=fid,
                text_modified=text_modified))
            if text_modified:
                text_changes.append(util.Container(
                    filename=rich_filename(new_path, kind), file_id=fid))

        for path, fid, kind in delta.removed:
            removed.append(util.Container(
                filename=rich_filename(path, kind), file_id=fid, kind=kind))
            if kind == 'file':
                text_changes.append(util.Container(
                    filename=rich_filename(path, kind), file_id=fid))

        text_changes.sort()

        return util.Container(
            added=added, renamed=renamed, removed=removed, modified=modified,
            text_changes=text_changes)
