# A server that recreates (modulo cherrypy bugs :) the url parsing
# from the old, loggerhead.conf approach.

import logging
import os

from configobj import ConfigObj

from paste.request import path_info_pop
from paste import httpexceptions
from paste.wsgiwrappers import WSGIResponse

from turbosimpletal import TurboZpt

from loggerhead.apps.branch import BranchWSGIApp
from loggerhead.apps import static_app
from loggerhead.history import History
from loggerhead.templatefunctions import templatefunctions
from loggerhead import util

t = TurboZpt()
tt = t.load_template('loggerhead.templates.browse')

log = logging.getLogger("loggerhead.controllers")

from loggerhead.history import is_branch

class Project (object):
    def __init__(self, name, config, root_config):
        self.name = name
        self.friendly_name = config.get('name', name)
        self.description = config.get('description', '')
        self.long_description = config.get('long_description', '')
        self._config = config
        self._root_config = root_config

        self.views = []
        self.views_by_name = {}
        for view_name in config.sections:
            log.debug('Configuring (project %s) branch %s...', name, view_name)
            self._add_view(
                view_name, config[view_name], config[view_name].get('folder'))

        self._auto_folder = config.get('auto_publish_folder', None)
        self._auto_list = []
        if self._auto_folder is not None:
            self._recheck_auto_folders()

    def _recheck_auto_folders(self):
        if self._auto_folder is None:
            return
        auto_list = []
        # scan a folder for bazaar branches, and add them automatically
        for path, folders, filenames in os.walk(self._auto_folder):
            for folder in folders:
                folder = os.path.join(path, folder)
                if is_branch(folder):
                    auto_list.append(folder)
        auto_list.sort()
        if auto_list == self._auto_list:
            # nothing has changed; do nothing.
            return

        # rebuild views:
        log.debug('Rescanning auto-folder for project %s ...', self.name)
        self._views = []
        for folder in auto_list:
            view_name = os.path.basename(folder)
            log.debug('Auto-configuring (project %s) branch %s...', self.name, view_name)
            self._add_view(view_name, ConfigObj(), folder)
        self._auto_list = auto_list

    def _add_view(self, view_name, view_config, folder):
        h = History.from_folder(folder)
        friendly_name = view_config.get('branch_name', None)
        if friendly_name is None:
            friendly_name = h.get_config().get_nickname()
            if friendly_name is None:
                friendly_name = view_name
        view = BranchWSGIApp(h, friendly_name)
        view.name = view_name
        self.views.append(view)
        self.views_by_name[view_name] = view

    def call(self, environ, start_response):
        segment = path_info_pop(environ)
        if not segment:
            raise httpexceptions.HTTPNotFound()
        else:
            view = self.views_by_name.get(segment)
            if view is None:
                raise httpexceptions.HTTPNotFound()
            return view.app(environ, start_response)


class Root(object):

    def __init__(self, config):
        self.projects = []
        self.config = config
        self.projects_by_name = {}
        for project_name in self.config.sections:
            project = Project(
                project_name, self.config[project_name], self.config)
            self.projects.append(project)
            self.projects_by_name[project_name] = project

    def browse(self, response):
        for p in self.projects:
            p._recheck_auto_folders()
        class branch:
            @staticmethod
            def static_url(path):
                print '!!!', repr(self._static_url_base), repr(path)
                return self._static_url_base + path
        vals = {
            'projects': self.projects,
            'util': util,
            'title': self.config.get('title', None),
            'branch': branch,
        }
        vals.update(templatefunctions)
        response.headers['Content-Type'] = 'text/html'
        tt.expand_(response, **vals)

    def __call__(self, environ, start_response):
        self._static_url_base = environ['loggerhead.static.url'] = environ['SCRIPT_NAME']
        segment = path_info_pop(environ)
        if segment is None:
            raise httpexceptions.HTTPMovedPermanently(
                environ['SCRIPT_NAME'] + '/')
        elif segment == '':
            response = WSGIResponse()
            self.browse(response)
            return response(environ, start_response)
        elif segment == 'static':
            return static_app(environ, start_response)
        else:
            project = self.projects_by_name.get(segment)
            if project is None:
                raise httpexceptions.HTTPNotFound()
            return project.call(environ, start_response)
