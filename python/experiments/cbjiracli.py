from __future__ import print_function

import csv
import getpass
import os

import cbclick

x = cbclick
import click
import sys
from operator import attrgetter, itemgetter
from cbjira import JiraFacade


def default_server():
    return 'http://localhost:8080'


def default_user():
    return 'admin'
    user = getpass.getuser()
    return user


def to_ascii(text):
    if not isinstance(text, (str, unicode)):
        return text
    if text is None:
        return None
    text = text.replace(u'\u2019', '\'')
    text = text.replace(u'\u2013', '-')
    text = text.replace(u'\u2022', '*')
    text = text.replace(u'\u03a3', 'Sum')
    return text


def safe_get(raw, path):
    items = list(reversed(path.split('.')))
    curr = raw
    while curr and items:
        curr = curr.get(items.pop())
    return curr


def dump(raw, depth=0, indent='    '):
    def no_urls(v):
        if type(v) is dict:
            return {k: no_urls(v) for k, v in v.items() if not str(v).startswith('http')}
        else:
            return v

    if type(raw) is dict:
        for k, v in sorted(no_urls(raw).items()):
            if type(v) in (dict, list):
                print('{}{} = '.format(indent * depth, k))
                dump(v, depth + 1, indent)
            else:
                print('{}{} = {}'.format(indent * depth, k, v))
    elif type(raw) is list:
        for _ in raw:
            print('{}{}'.format(indent * depth, no_urls(_)))


def print_items(values, keys, sort_key=None):
    w = csv.writer(sys.stdout)
    w.writerow(keys)
    for dict_ in sorted(values, key=itemgetter(sort_key or keys[0])):
        w.writerow(tuple(to_ascii(dict_.get(_)) for _ in keys))


def print_attrs(values, attrs, sort_attr=None):
    w = csv.writer(sys.stdout)
    w.writerow(attrs)
    for res in sorted(values, key=attrgetter(sort_attr or attrs[0])):
        w.writerow(tuple(getattr(res, _) for _ in attrs))


def get_attachment(file):
    if file == '-':
        return sys.stdin
    else:
        return open(file, 'rb')


def get_text(args, message):
    if len(args) == 0:
        return click.prompt(message)
    elif len(args) == 1 and args[0] == '-':
        return ''.join(sys.stdin.readlines())
    elif os.path.isfile(args[0]):
        with open(args[0], 'r') as f:
            return ''.join(f.readlines())
    else:
        return ' '.join(args)


# =====================================================================================================================
# Top level group.
# =====================================================================================================================

@click.group(context_settings=dict(terminal_width=200), help='A command line tool for interacting with JIRA.')
@click.option('-S', '--server', default=default_server(), show_default=True, envvar='JIRA_SERVER',
              help='The URL to connect to.')
@click.option('-U', '--username', default=default_user(), show_default=True, envvar='JIRA_USER',
              help='The username to connect with.')
@click.option('-P', '--password', prompt=True, hide_input=True, envvar='JIRA_PASSWORD',
              help='The password to connect with (or set JIRA_PASSWORD).')
@click.pass_context
def topcli(ctx, server, username, password):
    ctx.obj = JiraFacade(server, username, password)


@topcli.command(help='Print the full help.')
@click.pass_context
def help(ctx):
    separator = '\n' + '-' * 79 + '\n'
    print(ctx.parent.get_help())
    for name, cmd in sorted(ctx.parent.command.commands.items()):
        print(separator)
        print(cmd.get_help(ctx).replace('support.py help', 'support.py ' + name))


# =====================================================================================================================
# Component sub-commands.
# =====================================================================================================================

@topcli.group(name='component', help='Component related sub-commands.')
@click.pass_context
def componentcli(ctx):
    pass


@componentcli.command(name='create', help='Add a new component to a project.')
@click.argument('project', nargs=1)
@click.argument('name', nargs=1)
@click.option('-d', '--description', help='The description.')
@click.pass_obj
def create_component(jf, project, name, description):
    jf.create_component(project, name, description)


@componentcli.command(name='delete', help='Delete a component from a project.')
@click.argument('project', nargs=1)
@click.argument('name', nargs=1)
@click.pass_obj
def delete_component(jf, project, name):
    jf.delete_component(project, name)


@componentcli.command(name='update', help='Edit an existing component of a project.')
@click.argument('project', nargs=1)
@click.argument('name', nargs=1)
@click.option('-d', '--description', help='The description.')
@click.pass_obj
def update_component(jf, project, name, description):
    jf.update_component(project, name, description)


@componentcli.command(name='search', help='List the components of a project.')
@click.argument('project', nargs=1)
@click.pass_obj
def search_components(jf, project):
    components = jf.search_components(project)

    w = csv.writer(sys.stdout)
    w.writerow(('name', 'description'))
    for _ in components:
        w.writerow([_.name, _.description])


# =====================================================================================================================
# Issue sub-commands.
# =====================================================================================================================

@topcli.group(name='issue', help='Issue related sub-commands.')
@click.pass_context
def issuecli(ctx):
    pass


@issuecli.command(name='new', help='Create a new issue.')
@click.argument('project', nargs=1)
@click.argument('type', nargs=1, type=click.Choice(['bug', 'task', 'epic']))
@click.argument('summary', nargs=1)
@click.pass_obj
def new_issue(jf, project, type, summary):
    resource = jf.new_issue(project, type, summary)
    print('Created issue', resource.key)


@issuecli.command(name='transition', help='Transition an issue.')
@click.argument('key', nargs=1)
@click.argument('transition', nargs=1)
@click.pass_obj
def transition_issue(jf, key, transition):
    jf.transition_issue(key, transition)


@issuecli.command(name='attach', help='Attach a file to an issue.')
@click.option('-n', '--name', help='The attachment name.')
@click.argument('key', nargs=1)
@click.argument('file', nargs=1)
@click.pass_obj
def attach_issue(jf, key, file, name):
    attachment = get_attachment(file)
    filename = name or attachment.name
    jf.create_attachment(key, attachment=attachment, filename=filename)


@issuecli.command(name='assign', help='Assign an issue to a user.')
@click.argument('key', nargs=1)
@click.argument('user', nargs=1)
@click.pass_obj
def assign_issue(jf, key, user):
    jf.assign_issue(key, user)


@issuecli.command(name='unassign', help='Unassign an issue.')
@click.argument('key', nargs=1)
@click.pass_obj
def unassign_issue(jf, key):
    jf.unassign_issue(key)


@issuecli.command(name='comment', help='Add a comment to an issue.')
@click.argument('key', nargs=1)
@click.argument('args', nargs=-1)
@click.pass_obj
def comment_issue(jf, key, args):
    jf.comment_issue(key, get_text(args, 'Comment'))


@issuecli.command(name='link', help='Link two issues.')
@click.option('-t', '--type', type=click.Choice(['blocks', 'clones', 'duplicates', 'relates to']), default='relates to',
              show_default=True, help='The link type.')
@click.argument('key-from', nargs=1)
@click.argument('key-to', nargs=1)
@click.pass_obj
def link_issue(jf, type, key_from, key_to):
    jf.link_issue(type, key_from, key_to)


@issuecli.command(name='unlink', help='Unlink two issues.')
@click.argument('key-from', nargs=1)
@click.argument('key-to', nargs=1)
@click.pass_obj
def unlink_issue(jf, key_from, key_to):
    jf.unlink_issue(key_from, key_to)


@issuecli.command(name='search', help='Find issues.')
@click.pass_obj
def search_issues(jf):
    issues = jf.search_issues()

    for _ in issues:
        summary = to_ascii(_.fields.summary)
        print(_.key, _.fields.assignee, _.fields.project, summary)


# =====================================================================================================================
# Meta sub-commands.
# =====================================================================================================================

@topcli.group(name='meta', help='Meta related sub-commands.')
@click.pass_context
def metacli(ctx):
    pass


@metacli.command(name='fields', help='List all the possible fields.')
@click.pass_obj
def list_fields(jf):
    print_items(jf.meta_fields(), ('id', 'name', 'searchable', 'navigable', 'orderable', 'custom'), 'id')


@metacli.command(name='issue-link-types', help='List all the possible issue link types.')
@click.pass_obj
def list_issue_link_types(jf):
    print_attrs(jf.meta_issue_link_types(), ('id', 'name', 'inward', 'outward'), 'name')


@metacli.command(name='issue-types', help='List all the possible issue types.')
@click.pass_obj
def list_issue_types(jf):
    print_attrs(jf.meta_issue_types(), ('id', 'name', 'description', 'subtask'), 'name')


@metacli.command(name='priorities', help='List all the possible priorities.')
@click.pass_obj
def list_priorities(jf):
    print_attrs(jf.meta_priorities(), ('id', 'name', 'description'), 'name')


@metacli.command(name='resolutions', help='List all the possible resolutions.')
@click.pass_obj
def list_resolutions(jf):
    print_attrs(jf.meta_resolutions(), ('id', 'name', 'description'), 'name')


@metacli.command(name='statuses', help='List all the possible statuses.')
@click.pass_obj
def list_statuses(jf):
    print_attrs(jf.meta_statuses(), ('id', 'name', 'description'), 'name')


@metacli.command(name='transitions', help='List all the possible transitions for a given issue.')
@click.argument('key', nargs=1)
@click.pass_obj
def list_transitions(jf, key):
    print_items(jf.meta_transitions(key), ('id', 'name'), 'name')


# =====================================================================================================================
# Project sub-commands.
# =====================================================================================================================

@topcli.group(name='project', help='Project related sub-commands.')
@click.pass_context
def projectcli(ctx):
    pass


@projectcli.command(name='info', help='Display information about a single project.')
@click.option('-p', '--project', required=True, help='The project key (eg INS).')
@click.pass_obj
def info_project(jf, project):
    project = jf.info_project(project)
    dump(project.raw)


@projectcli.command(name='search', help='List the projects.')
@click.option('-f', '--filter', default=None, help='Show only the matching projects.')
@click.pass_obj
def search_projects(jf, filter):
    projects = jf.search_projects()

    w = csv.writer(sys.stdout)
    w.writerow(('KEY', 'NAME', 'DESCRIPTION', 'LEAD', 'PROJECT_TYPE'))
    for _ in sorted(projects, key=attrgetter('key')):
        if filter is None or (filter.upper() in _.key.upper() or filter.upper() in _.name.upper()):
            w.writerow((
                _.key,
                to_ascii(_.name),
                to_ascii(safe_get(_.raw, 'description')),
                to_ascii(safe_get(_.raw, 'lead.displayName')),
                to_ascii(safe_get(_.raw, 'projectTypeKey')),
            ))


# =====================================================================================================================
# User sub-commands.
# =====================================================================================================================

@topcli.group(name='user', help='User related sub-commands.')
@click.pass_context
def usercli(ctx):
    pass


@usercli.command(name='create', help='Add a new user.')
@click.argument('username', nargs=1)
@click.argument('email', nargs=1)
@click.option('-p', '--password', help='The password.')
@click.option('-n', '--fullname', help='The full name.')
@click.pass_obj
def create_user(jf, username, email, password, fullname):
    jf.create_user(username, email, password=password, fullname=fullname)


@usercli.command(name='delete', help='Delete a user.')
@click.argument('username', nargs=1)
@click.pass_obj
def delete_user(jf, username):
    jf.delete_user(username)


@usercli.command(name='update', help='Edit an existing user.')
@click.argument('username', nargs=1)
@click.option('-e', '--email', help='The email.')
@click.pass_obj
def update_version(jf, username, email):
    jf.update_user(username, email)


@usercli.command(name='search', help='List all the users matching the provided a string (username, full name, email).')
@click.option('-f', '--filter', help='Match on any part (username, full name, email)')
@click.pass_obj
def search_users(jf, filter):
    users = jf.search_users(filter)

    for _ in users:
        print(_.key, _.name, _.emailAddress, _)


# =====================================================================================================================
# Version sub-commands.
# =====================================================================================================================

@topcli.group(name='version', help='Version related sub-commands.')
@click.pass_context
def versioncli(ctx):
    pass


@versioncli.command(name='create', help='Add a new version to a project.')
@click.argument('project', nargs=1)
@click.argument('name', nargs=1)
@click.option('-d', '--description', help='The description.')
@click.pass_obj
def create_version(jf, project, name, description):
    jf.create_version(project, name, description)


@versioncli.command(name='delete', help='Delete a version from a project.')
@click.argument('project', nargs=1)
@click.argument('name', nargs=1)
@click.pass_obj
def delete_version(jf, project, name):
    jf.delete_version(project, name)


@versioncli.command(name='update', help='Edit a existing version of a project.')
@click.argument('project', nargs=1)
@click.argument('name', nargs=1)
@click.option('-d', '--description', help='The description.')
@click.pass_obj
def update_version(jf, project, name, description):
    jf.update_version(project, name, description)


@versioncli.command(name='search', help='List the versions of a project.')
@click.argument('project', nargs=1)
@click.option('-c', '--count', default=10, show_default=True, help='Display only the last N versions (0 = all).')
@click.pass_obj
def search_versions(jf, project, count):
    versions = jf.search_versions(project)

    w = csv.writer(sys.stdout)
    w.writerow(('version', 'released', 'releaseDate', 'name'))
    for _ in versions[-count:]:
        w.writerow([_.name, _.released, _.raw.get('releaseDate'), _.raw.get('description')])


if __name__ == '__main__':
    topcli()
