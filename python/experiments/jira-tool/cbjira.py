from __future__ import print_function

import csv
import getpass
import sys
from operator import attrgetter

from click import group, option, pass_context, pass_obj
from jira import JIRA


def default_user():
    user = getpass.getuser()
    # TODO: Use client.cfg for this.
    if user == 'nbeney':
        user = 'beneyn'
    return user


def sanitize(text):
    if text is None: return None
    text = text.replace(u'\u2019', '\'')
    text = text.replace(u'\u2013', '-')
    text = text.replace(u'\u2022', '*')
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


@group(context_settings=dict(terminal_width=200), help='A command line tool for interacting with JIRA.')
@option('-S', '--server', default='https://jira.daiwa.global:8444', show_default=True, help='The URL to connect to.')
@option('-U', '--username', default=default_user(), show_default=True, help='The username to connect with.')
@option('-P', '--password', prompt=True, hide_input=True, envvar='JIRA_PASSWORD',
        help='The password to connect with (or set JIRA_PASSWORD).')
@pass_context
def cli(ctx, server, username, password):
    ctx.obj = dict(server=server, username=username, password=password)


@cli.command(help='Find issues.')
@pass_obj
def issues(conn):
    jira = JIRA(options=dict(server=conn['server'], verify=False), basic_auth=(conn['username'], conn['password']))
    issues = jira.search_issues(
        "status not in (Resolved, Closed, Cancelled) AND assignee not in (EMPTY) AND project in (INS, INSRELEASE) ORDER BY assignee ASC, project ASC, summary ASC",
        fields=['key', 'summary', 'assignee', 'project'])
    for _ in issues:
        summary = sanitize(_.fields.summary)
        print(_.key, _.fields.assignee, _.fields.project, summary)


@cli.command(help='Display information about a single project.')
@option('-p', '--project', required=True, help='The project key (eg INS).')
@pass_obj
def project(conn, project):
    jira = JIRA(options=dict(server=conn['server'], verify=False), basic_auth=(conn['username'], conn['password']))
    project = jira.project(project)
    dump(project.raw)


@cli.command(help='List the projects.')
@option('-f', '--filter', default=None, help='Show only the matching projects.')
@pass_obj
def projects(conn, filter):
    jira = JIRA(options=dict(server=conn['server'], verify=False), basic_auth=(conn['username'], conn['password']))
    projects = jira.projects()

    w = csv.writer(sys.stdout)
    w.writerow(('KEY', 'NAME', 'DESCRIPTION', 'LEAD', 'PROJECT_TYPE'))
    for _ in sorted(projects, key=attrgetter('key')):
        if filter is None or (filter.upper() in _.key.upper() or filter.upper() in _.name.upper()):
            w.writerow((
                _.key,
                sanitize(_.name),
                sanitize(safe_get(_.raw, 'description')),
                sanitize(safe_get(_.raw, 'lead.displayName')),
                sanitize(safe_get(_.raw, 'projectTypeKey')),
            ))
            #
            # print()
            # p = jira.project('INS')
            # for _ in sorted(p.raw.items()):
            #     print(_)


@cli.command(help='List the versions of a project.')
@option('-p', '--project', required=True, help='The project key (eg INS).')
@option('-c', '--count', default=10, show_default=True, help='Display only the last N versions (0 = all).')
@pass_obj
def versions(conn, project, count):
    jira = JIRA(options=dict(server=conn['server'], verify=False), basic_auth=(conn['username'], conn['password']))
    project = jira.project(project.upper())
    versions = jira.project_versions(project)

    w = csv.writer(sys.stdout)
    w.writerow(('version', 'released', 'releaseDate', 'name'))
    for _ in versions[-count:]:
        w.writerow([_.name, _.released, _.raw.get('releaseDate'), _.raw.get('description')])


if __name__ == '__main__':
    cli()

    # runner = CliRunner()
    # result = runner.invoke(cli, ['-P', 'xxx', 'issues'])
    # assert result.exit_code == 0
    # assert result.output == 'Hello beneyn xxx\n'

    # runner = CliRunner()
    # result = runner.invoke(cli, ['issues'], env=dict(JIRA_PASSWORD='yyy'))
    # assert result.exit_code == 0
    # assert result.output == 'Hello beneyn yyy\n'
