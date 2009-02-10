#
# Copyright (C) 2008  Canonical Ltd.
# Copyright (C) 2006  Robey Pointer <robey@lag.net>
# Copyright (C) 2006  Goffredo Baroncelli <kreijack@inwind.it>
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

import logging
import posixpath
import urllib

from paste.httpexceptions import HTTPServerError

from bzrlib.revision import is_null as is_null_rev

from loggerhead import util
from loggerhead.controllers import TemplatedBranchView


log = logging.getLogger("loggerhead.controllers")


def dirname(path):
    if path is not None:
        while path.endswith('/'):
            path = path[:-1]
        path = urllib.quote(posixpath.dirname(path))
    return path


class InventoryUI(TemplatedBranchView):

    template_path = 'loggerhead.templates.inventory'

    def get_filelist(self, inv, file_id, sort_type=None):
        """
        return the list of all files (and their attributes) within a given
        path subtree.
        """

        dir_ie = inv[file_id]
        path = inv.id2path(file_id)
        file_list = []

        revid_set = set()

        for filename, entry in dir_ie.children.iteritems():
            revid_set.add(entry.revision)

        change_dict = {}
        for change in self._history.get_changes(list(revid_set)):
            change_dict[change.revid] = change

        for filename, entry in dir_ie.children.iteritems():
            pathname = filename
            if entry.kind == 'directory':
                pathname += '/'
            if path == '':
                absolutepath = pathname
            else:
                absolutepath = urllib.quote(path + '/' + pathname)
            revid = entry.revision

            file = util.Container(
                filename=filename, executable=entry.executable,
                kind=entry.kind, absolutepath=absolutepath,
                file_id=entry.file_id, size=entry.text_size, revid=revid,
                change=change_dict[revid])
            file_list.append(file)

        if sort_type == 'filename' or sort_type is None:
            file_list.sort(key=lambda x: x.filename.lower()) # case-insensitive
        elif sort_type == 'size':
            file_list.sort(key=lambda x: x.size)
        elif sort_type == 'date':
            file_list.sort(key=lambda x: x.change.date)

        # Always sort by kind to get directories first
        file_list.sort(key=lambda x: x.kind != 'directory')

        return file_list

    def get_values(self, path, kwargs, headers):
        history = self._history
        revid = self.get_revid()

        try:
            rev_tree = history._branch.repository.revision_tree(revid)
        except:
            self.log.exception('Exception fetching changes')
            raise HTTPServerError('Could not fetch changes')

        file_id = kwargs.get('file_id', None)
        start_revid = kwargs.get('start_revid', None)
        sort_type = kwargs.get('sort', None)

        # no navbar for revisions
        navigation = util.Container()

        if path is not None:
            if not path.startswith('/'):
                path = '/' + path
            file_id = history.get_file_id(revid, path)
        else:
            path = rev_tree.id2path(file_id)

        # Are we at the top of the tree
        if path in ['/', '']:
            updir = None
        else:
            updir = dirname(path)[1:]

        # Directory Breadcrumbs
        directory_breadcrumbs = util.directory_breadcrumbs(
                self._branch.friendly_name,
                self._branch.is_root,
                'files')

        if not is_null_rev(revid):

            change = history.get_changes([ revid ])[0]
            # If we're looking at the tip, use head: in the URL instead
            if revid == history.last_revid:
                revno_url = 'head:'
            else:
                revno_url = history.get_revno(revid)
            # add parent & merge-point branch-nick info, in case it's useful
            history.get_branch_nicks([ change ])

            # Create breadcrumb trail for the path within the branch
            branch_breadcrumbs = util.branch_breadcrumbs(path, rev_tree, 'files')
            if file_id is None:
                file_id = rev_tree.inventory.root.file_id
            filelist = self.get_filelist(rev_tree.inventory, file_id, sort_type)
        else:
            inv = None
            start_revid = None
            sort_type = None
            change = None
            path = "/"
            updir = None
            revno_url = 'head:'
            branch_breadcrumbs = []
            filelist = []

        return {
            'branch': self._branch,
            'util': util,
            'revid': revid,
            'revno_url': revno_url,
            'change': change,
            'path': path,
            'updir': updir,
            'filelist': filelist,
            'history': history,
            'posixpath': posixpath,
            'navigation': navigation,
            'url': self._branch.context_url,
            'start_revid': start_revid,
            'fileview_active': True,
            'directory_breadcrumbs': directory_breadcrumbs,
            'branch_breadcrumbs': branch_breadcrumbs,
        }
