"""The WSGI application for serving a Bazaar branch."""

import logging
import urllib
import sys

import bzrlib.branch
import bzrlib.lru_cache

from paste import request
from paste import httpexceptions

from loggerhead.apps import static_app
from loggerhead.controllers.annotate_ui import AnnotateUI
from loggerhead.controllers.atom_ui import AtomUI
from loggerhead.controllers.changelog_ui import ChangeLogUI
from loggerhead.controllers.diff_ui import DiffUI
from loggerhead.controllers.download_ui import DownloadUI
from loggerhead.controllers.filediff_ui import FileDiffUI
from loggerhead.controllers.inventory_ui import InventoryUI
from loggerhead.controllers.revision_ui import RevisionUI
from loggerhead.controllers.revlog_ui import RevLogUI
from loggerhead.controllers.search_ui import SearchUI
from loggerhead.history import History
from loggerhead import util


_DEFAULT = object()

class BranchWSGIApp(object):

    def __init__(self, branch, friendly_name=None, config={},
                 graph_cache=None, branch_link=None, is_root=False,
                 served_url=_DEFAULT, use_cdn=False):
        self.branch = branch
        self._config = config
        self.friendly_name = friendly_name
        self.branch_link = branch_link  # Currently only used in Launchpad
        self.log = logging.getLogger('loggerhead.%s' % friendly_name)
        if graph_cache is None:
            graph_cache = bzrlib.lru_cache.LRUCache()
        self.graph_cache = graph_cache
        self.is_root = is_root
        self.served_url = served_url
        self.use_cdn = use_cdn

    def get_history(self):
        _history = History(self.branch, self.graph_cache)
        cache_path = self._config.get('cachepath', None)
        if cache_path is not None:
            # Only import the cache if we're going to use it.
            # This makes sqlite optional
            try:
                from loggerhead.changecache import FileChangeCache
            except ImportError:
                self.log.debug("Couldn't load python-sqlite,"
                               " continuing without using a cache")
            else:
                _history.use_file_cache(
                    FileChangeCache(_history, cache_path))
        return _history

    def url(self, *args, **kw):
        if isinstance(args[0], list):
            args = args[0]
        qs = []
        for k, v in kw.iteritems():
            if v is not None:
                qs.append('%s=%s'%(k, urllib.quote(v)))
        qs = '&'.join(qs)
        return request.construct_url(
            self._environ, script_name=self._url_base,
            path_info=unicode('/'.join(args)).encode('utf-8'),
            querystring=qs)

    def context_url(self, *args, **kw):
        kw = util.get_context(**kw)
        return self.url(*args, **kw)

    def static_url(self, path):
        return self._static_url_base + path

    def yui_url(self, path):
        if self.use_cdn:
            base = 'http://yui.yahooapis.com/3.0.0pr2/build/'
        else:
            base = self.static_url('/static/javascript/yui/build/')
        return base + path

    controllers_dict = {
        '+filediff': FileDiffUI,
        '+revlog': RevLogUI,
        'annotate': AnnotateUI,
        'atom': AtomUI,
        'changes': ChangeLogUI,
        'diff': DiffUI,
        'download': DownloadUI,
        'files': InventoryUI,
        'revision': RevisionUI,
        'search': SearchUI,
        }

    def last_updated(self):
        h = self.get_history()
        change = h.get_changes([h.last_revid])[0]
        return change.date

    def branch_url(self):
        return self.branch.get_config().get_user_option('public_branch')

    def app(self, environ, start_response):
        self._url_base = environ['SCRIPT_NAME']
        self._static_url_base = environ.get('loggerhead.static.url')
        if self._static_url_base is None:
            self._static_url_base = self._url_base
        self._environ = environ
        if self.served_url is _DEFAULT:
            self.served_url = self.url([])
        path = request.path_info_pop(environ)
        if not path:
            raise httpexceptions.HTTPMovedPermanently(
                self._url_base + '/changes')
        if path == 'static':
            return static_app(environ, start_response)
        cls = self.controllers_dict.get(path)
        if cls is None:
            raise httpexceptions.HTTPNotFound()
        self.branch.lock_read()
        try:
            try:
                c = cls(self, self.get_history)
                return c(environ, start_response)
            except:
                environ['exc_info'] = sys.exc_info()
                environ['branch'] = self
                raise
        finally:
            self.branch.unlock()
