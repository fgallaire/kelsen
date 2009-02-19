from loggerhead.apps.branch import BranchWSGIApp
from loggerhead.controllers.inventory_ui import InventoryUI
from loggerhead.controllers.revision_ui import RevisionUI
from loggerhead.tests.test_simple import BasicTests
from loggerhead import util


class TestInventoryUI(BasicTests):

    def make_bzrbranch_and_inventory_ui_for_tree_shape(self, shape):
        tree = self.make_branch_and_tree('.')
        self.build_tree(shape)
        tree.smart_add([])
        tree.commit('')
        tree.branch.lock_read()
        self.addCleanup(tree.branch.unlock)
        branch_app = BranchWSGIApp(tree.branch)
        return tree.branch, InventoryUI(branch_app, branch_app.get_history)

    def test_get_filelist(self):
        bzrbranch, inv_ui = self.make_bzrbranch_and_inventory_ui_for_tree_shape(
            ['filename'])
        inv = bzrbranch.repository.get_inventory(bzrbranch.last_revision())
        self.assertEqual(1, len(inv_ui.get_filelist(inv, '')))


class TestRevisionUI(BasicTests):

    def make_bzrbranch_and_revision_ui_for_tree_shapes(self, shape1, shape2):
        tree = self.make_branch_and_tree('.')
        self.build_tree_contents(shape1)
        tree.smart_add([])
        tree.commit('')
        tree.smart_add([])
        self.build_tree_contents(shape2)
        tree.commit('')
        tree.branch.lock_read()
        self.addCleanup(tree.branch.unlock)
        branch_app = BranchWSGIApp(tree.branch)
        branch_app._environ = {
            'wsgi.url_scheme':'',
            'SERVER_NAME':'',
            'SERVER_PORT':'80',
            }
        branch_app._url_base = ''
        branch_app.friendly_name = ''
        return tree.branch, RevisionUI(branch_app, branch_app.get_history)

    def test_get_values(self):
        branch, rev_ui = self.make_bzrbranch_and_revision_ui_for_tree_shapes(
            [], [])
        rev_ui.args = ['2']
        util.set_context({})
        self.assertIsInstance(
            rev_ui.get_values('2', {}, []),
            dict)