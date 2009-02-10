import cgi
import os
import tempfile
import shutil
import logging

import bzrlib.bzrdir
import bzrlib.osutils
from bzrlib.tests import TestCaseWithTransport
from bzrlib.util.configobj.configobj import ConfigObj

from loggerhead.apps.branch import BranchWSGIApp
from paste.fixture import TestApp


def test_config_root():
    from loggerhead.apps.config import Root
    config = ConfigObj()
    app = TestApp(Root(config))
    res = app.get('/')
    res.mustcontain('loggerhead branches')


class BasicTests(TestCaseWithTransport):


    def createBranch(self):
        self.tree = self.make_branch_and_tree('.')

    def setUpLoggerhead(self):
        app = TestApp(BranchWSGIApp(self.tree.branch, '').app)
        return app


class TestWithSimpleTree(BasicTests):

    def setUp(self):
        BasicTests.setUp(self)
        self.createBranch()

        self.filecontents = ('some\nmultiline\ndata\n'
                             'with<htmlspecialchars\n')
        self.build_tree_contents(
            [('myfilename', self.filecontents)])
        self.tree.add('myfilename')
        self.fileid = self.tree.path2id('myfilename')
        self.msg = 'a very exciting commit message <'
        self.revid = self.tree.commit(message=self.msg)

    def test_changes(self):
        app = self.setUpLoggerhead()
        res = app.get('/changes')
        res.mustcontain(cgi.escape(self.msg))

    def test_changes_search(self):
        app = self.setUpLoggerhead()
        res = app.get('/changes', params={'q': 'foo'})
        res.mustcontain('Sorry, no results found for your search.')

    def test_annotate(self):
        app = self.setUpLoggerhead()
        res = app.get('/annotate', params={'file_id': self.fileid})
        for line in self.filecontents.splitlines():
            res.mustcontain(cgi.escape(line))

    def test_inventory(self):
        app = self.setUpLoggerhead()
        res = app.get('/files')
        res.mustcontain('myfilename')

    def test_revision(self):
        app = self.setUpLoggerhead()
        res = app.get('/revision/1')
        res.mustcontain('myfilename')


class TestEmptyBranch(BasicTests):

    def setUp(self):
        BasicTests.setUp(self)
        self.createBranch()

    def test_changes(self):
        app = self.setUpLoggerhead()
        res = app.get('/changes')
        res.mustcontain('No revisions!')
    
    def test_inventory(self):
        app = self.setUpLoggerhead()
        res = app.get('/files')
        res.mustcontain('myfilename')

