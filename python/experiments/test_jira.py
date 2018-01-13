from __future__ import print_function

import unittest

from click.testing import CliRunner
from jira import JIRA

from cbjiracli import topcli

TEST_URL = 'http://localhost:8080'
TEST_USERNAME = 'admin'
TEST_PASSWORD = 'admin'


class TestComponents(unittest.TestCase):
    def setUp(self):
        self.jira = JIRA(options=dict(server=TEST_URL, verify=False), basic_auth=(TEST_USERNAME, TEST_PASSWORD))
        self.purge_test_components()

    def tearDown(self):
        self.purge_test_components()

    def get_component(self, name):
        components = [_ for _ in self.jira.project_components('KB') if _.name == 'test-1']
        return components[0] if len(components) == 1 else None

    def purge_test_components(self):
        for _ in self.jira.project_components('KB'):
            if _.name.startswith('test-'):
                _.delete()

    def test_create_component(self):
        result = CliRunner().invoke(topcli, ['component', 'create', 'KB', 'test-1', '-d', 'Some description'])
        self.assertEqual(result.exit_code, 0)

    def test_delete_component(self):
        result = CliRunner().invoke(topcli, ['component', 'create', 'KB', 'test-1'])
        self.assertEqual(result.exit_code, 0)
        self.assertIsNotNone(self.get_component('test-1'))
        result = CliRunner().invoke(topcli, ['component', 'delete', 'KB', 'test-1'])
        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(self.get_component('test-1'))

    def test_update_component(self):
        result = CliRunner().invoke(topcli, ['component', 'create', 'KB', 'test-1', '-d', 'before'])
        before = self.get_component('test-1')
        self.assertEqual(before.description, 'before')
        result = CliRunner().invoke(topcli, ['component', 'update', 'KB', 'test-1', '-d', 'after'])
        self.assertEqual(result.exit_code, 0)
        after = self.get_component('test-1')
        self.assertEqual(after.description, 'after')

    def test_search_component(self):
        result = CliRunner().invoke(topcli, ['component', 'create', 'KB', 'test-1', '-d', 'Some description'])
        result = CliRunner().invoke(topcli, ['component', 'search', 'KB'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('test-1', result.output)
        self.assertIn('Some description', result.output)


class TestIssues(unittest.TestCase):
    def setUp(self):
        self.jira = JIRA(options=dict(server=TEST_URL, verify=False), basic_auth=(TEST_USERNAME, TEST_PASSWORD))
        self.issue1 = self.jira.create_issue(
            project='KB',
            summary='Test-1',
            issuetype={'name': 'Bug'},
        )
        self.issue2 = self.jira.create_issue(
            project='KB',
            summary='Test-2',
            issuetype={'name': 'Bug'},
        )

    def tearDown(self):
        issues = self.jira.search_issues('project = "KB" AND summary ~ "Test*"', fields=['key'])
        for _ in issues:
            _.delete()

    def assert_single_attachment(self):
        # TODO - Find how to test this automatically
        pass

    def assert_single_comment_with(self, text):
        comments = self.jira.comments(self.issue1.key)
        self.assertEqual(len(comments), 1)
        self.assertIn(text, comments[0].body)

    def test_new(self):
        result = CliRunner().invoke(topcli, ['issue', 'new', 'KB', 'task', 'Test-new'])
        self.assertEqual(result.exit_code, 0)
        issues = self.jira.search_issues('project = "KB" AND summary ~ "Test-new"', fields=['key', 'summary'])
        self.assertEqual(len(issues), 1)
        self.assertIn(issues[0].key, result.output)

    def test_transition(self):
        result = CliRunner().invoke(topcli, ['issue', 'transition', self.issue1.key, 'Done'])
        self.assertEqual(result.exit_code, 0)

    def test_assign(self):
        result = CliRunner().invoke(topcli, ['issue', 'assign', self.issue1.key, TEST_USERNAME])
        self.assertEqual(result.exit_code, 0)
        assignee = self.jira.issue(self.issue1.key, fields=['assignee']).fields.assignee
        self.assertEqual(assignee.key, TEST_USERNAME)

    def test_unassign(self):
        result = CliRunner().invoke(topcli, ['issue', 'assign', self.issue1.key, TEST_USERNAME])
        result = CliRunner().invoke(topcli, ['issue', 'unassign', self.issue1.key])
        self.assertEqual(result.exit_code, 0)
        assignee = self.jira.issue(self.issue1.key, fields=['assignee']).fields.assignee
        self.assertIsNone(assignee)

    def test_attach_file(self):
        with CliRunner().isolated_filesystem() as dir_path:
            with open('data.txt', 'w') as f:
                print('abc', file=f)
            result = CliRunner().invoke(topcli, ['issue', 'attach', self.issue1.key, 'data.txt'])
            self.assertEqual(result.exit_code, 0)
            self.assert_single_attachment()

    def test_comment_args(self):
        result = CliRunner().invoke(topcli, ['issue', 'comment', self.issue1.key, 'Comment', 'from args'])
        self.assertEqual(result.exit_code, 0)
        self.assert_single_comment_with('Comment from args')

    def test_comment_file(self):
        with CliRunner().isolated_filesystem() as dir_path:
            with open('comment.txt', 'w') as f:
                print('Comment from file', file=f)
            result = CliRunner().invoke(topcli, ['issue', 'comment', self.issue1.key, 'comment.txt'])
            self.assertEqual(result.exit_code, 0)
            self.assert_single_comment_with('Comment from file')

    def test_comment_prompt(self):
        result = CliRunner().invoke(topcli, ['issue', 'comment', self.issue1.key], input='Comment from prompt\n')
        self.assertEqual(result.exit_code, 0)
        self.assert_single_comment_with('Comment from prompt')

    def test_comment_stdin(self):
        result = CliRunner().invoke(topcli, ['issue', 'comment', self.issue1.key, '-'], input='Comment\nfrom\nstdin')
        self.assertEqual(result.exit_code, 0)
        self.assert_single_comment_with('Comment\nfrom\nstdin')

    def test_link(self):
        result = CliRunner().invoke(topcli, ['issue', 'link', self.issue1.key, self.issue2.key, '-t', 'duplicates'])
        self.assertEqual(result.exit_code, 0)
        links = self.jira.issue(self.issue1.key, fields=['issuelinks']).fields.issuelinks
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].outwardIssue.key, self.issue2.key)
        self.assertEqual(links[0].type.outward, 'duplicates')

    def test_unlink(self):
        result = CliRunner().invoke(topcli, ['issue', 'link', self.issue1.key, self.issue2.key, '-t', 'duplicates'])
        self.assertEqual(result.exit_code, 0)
        result = CliRunner().invoke(topcli, ['issue', 'unlink', self.issue1.key, self.issue2.key])
        links = self.jira.issue(self.issue1.key, fields=['issuelinks']).fields.issuelinks
        self.assertEqual(len(links), 0)

    def test_search_issue(self):
        result = CliRunner().invoke(topcli, ['issue', 'search'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('KB-1', result.output)
        self.assertIn('KB-2', result.output)
        self.assertIn('KB-3', result.output)


class TestMeta(unittest.TestCase):
    def test_fields(self):
        result = CliRunner().invoke(topcli, ['meta', 'fields'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('status', result.output)

    def test_issue_link_types(self):
        result = CliRunner().invoke(topcli, ['meta', 'issue-link-types'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Blocks', result.output)

    def test_issue_types(self):
        result = CliRunner().invoke(topcli, ['meta', 'issue-types'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Task', result.output)

    def test_priorities(self):
        result = CliRunner().invoke(topcli, ['meta', 'priorities'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Highest', result.output)

    def test_resolutions(self):
        result = CliRunner().invoke(topcli, ['meta', 'resolutions'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Done', result.output)

    def test_statuses(self):
        result = CliRunner().invoke(topcli, ['meta', 'statuses'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('In Progress', result.output)

    def test_transitions(self):
        result = CliRunner().invoke(topcli, ['meta', 'transitions', 'KB-1'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('In Progress', result.output)


class TestProjects(unittest.TestCase):
    def test_info_project(self):
        result = CliRunner().invoke(topcli, ['project', 'info', '-p', 'KB'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('KB', result.output)

    def test_search_project(self):
        result = CliRunner().invoke(topcli, ['project', 'search'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('KB', result.output)


class TestUsers(unittest.TestCase):
    def setUp(self):
        self.jira = JIRA(options=dict(server=TEST_URL, verify=False), basic_auth=(TEST_USERNAME, TEST_PASSWORD))
        self.purge_test_users()

    def tearDown(self):
        self.purge_test_users()

    def get_user(self, username):
        users = [_ for _ in self.jira.search_users(user=username) if _.name == username]
        return users[0] if len(users) == 1 else None

    def purge_test_users(self):
        users = [_ for _ in self.jira.search_users(user='test-') if _.name.startswith('test-')]
        for _ in users:
            _.delete()

    def test_create_user(self):
        self.assertIsNone(self.get_user('test-1'))
        result = CliRunner().invoke(topcli, ['user', 'create', 'test-1', 'test-1' + '@gmail.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertIsNotNone(self.get_user('test-1'))

    def test_delete_user(self):
        result = CliRunner().invoke(topcli, ['user', 'create', 'test-1', 'test-1' + '@gmail.com'])
        self.assertEqual(result.exit_code, 0)
        self.assertIsNotNone(self.get_user('test-1'))
        result = CliRunner().invoke(topcli, ['user', 'delete', 'test-1'])
        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(self.get_user('test-1'))

    def test_update_user(self):
        result = CliRunner().invoke(topcli, ['user', 'create', 'test-1', 'before@gmail.com'])
        before = self.get_user('test-1')
        self.assertEqual(before.emailAddress, 'before@gmail.com')
        result = CliRunner().invoke(topcli, ['user', 'update', 'test-1', '-e', 'after@gmail.com'])
        self.assertEqual(result.exit_code, 0)
        after = self.get_user('test-1')
        self.assertEqual(after.emailAddress, 'after@gmail.com')

    def test_search_user(self):
        result = CliRunner().invoke(topcli, ['user', 'create', 'test-1', 'test-1' + '@gmail.com'])
        result = CliRunner().invoke(topcli, ['user', 'search'])
        self.assertEqual(result.exit_code, 0)
        before = len(result.output.strip().split('\n'))
        self.assertGreater(before, 1)
        result = CliRunner().invoke(topcli, ['user', 'search', '-f', 'test-1'])
        self.assertEqual(result.exit_code, 0)
        after = len(result.output.strip().split('\n'))
        self.assertEqual(after, 1)


class TestVersions(unittest.TestCase):
    def setUp(self):
        self.jira = JIRA(options=dict(server=TEST_URL, verify=False), basic_auth=(TEST_USERNAME, TEST_PASSWORD))
        self.purge_test_versions()

    def tearDown(self):
        self.purge_test_versions()

    def get_version(self, name):
        versions = [_ for _ in self.jira.project_versions('KB') if _.name == 'test-1']
        return versions[0] if len(versions) == 1 else None

    def purge_test_versions(self):
        for _ in self.jira.project_versions('KB'):
            if _.name.startswith('test-'):
                _.delete()

    def test_create_version(self):
        result = CliRunner().invoke(topcli, ['version', 'create', 'KB', 'test-1', '-d', 'Some description'])
        self.assertEqual(result.exit_code, 0)

    def test_delete_version(self):
        result = CliRunner().invoke(topcli, ['version', 'create', 'KB', 'test-1'])
        self.assertEqual(result.exit_code, 0)
        self.assertIsNotNone(self.get_version('test-1'))
        result = CliRunner().invoke(topcli, ['version', 'delete', 'KB', 'test-1'])
        self.assertEqual(result.exit_code, 0)
        self.assertIsNone(self.get_version('test-1'))

    def test_update_version(self):
        result = CliRunner().invoke(topcli, ['version', 'create', 'KB', 'test-1', '-d', 'before'])
        before = self.get_version('test-1')
        self.assertEqual(before.description, 'before')
        result = CliRunner().invoke(topcli, ['version', 'update', 'KB', 'test-1', '-d', 'after'])
        self.assertEqual(result.exit_code, 0)
        after = self.get_version('test-1')
        self.assertEqual(after.description, 'after')

    def test_search_version(self):
        result = CliRunner().invoke(topcli, ['version', 'create', 'KB', 'test-1', '-d', 'Some description'])
        result = CliRunner().invoke(topcli, ['version', 'search', 'KB'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('test-1', result.output)
        self.assertIn('Some description', result.output)
