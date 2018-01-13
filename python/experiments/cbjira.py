from __future__ import print_function

from jira import JIRA


class JiraFacade:
    def __init__(self, server, username, password):
        self.conn = dict(server=server, username=username, password=password)

    # @lru_cache
    def jira(self):
        return JIRA(options=dict(
            server=self.conn['server'],
            verify=False),
            basic_auth=(self.conn['username'], self.conn['password'])
        )

    #
    # Components
    #

    def add_component(self, project, name, description):
        project = self.jira().project(project.upper())
        resource = self.jira().create_component(name, project, description=description)
        return resource

    def delete_component(self, project, name):
        project = self.jira().project(project.upper())
        component = [_ for _ in self.jira().project_components(project) if _.name == name][0]
        component.delete()

    def edit_component(self, project, name, description):
        project = self.jira().project(project.upper())
        component = [_ for _ in self.jira().project_components(project) if _.name == name][0]
        component.update(description=description)
        return component

    def search_components(self, project):
        project = self.jira().project(project.upper())
        components = self.jira().project_components(project)
        return components

    #
    # Issues
    #

    def new_issue(self, project, type, summary):
        fields = dict(
            project=project.upper(),
            issuetype=type.capitalize(),
            summary=summary,
        )
        resource = self.jira().create_issue(fields)
        return resource

    def transition_issue(self, key, transition):
        self.jira().transition_issue(key, transition)

    def attach_issue(self, key, file, name):
        resource = self.jira().add_attachment(key, attachment=file, filename=name)
        return resource

    def assign_issue(self, key, user):
        resource = self.jira().assign_issue(key, user)

    def unassign_issue(self, key):
        resource = self.jira().assign_issue(key, None)

    def comment_issue(self, key, text):
        resource = self.jira().add_comment(key, text)

    def link_issue(self, type, key_from, key_to):
        self.jira().create_issue_link(type, key_from, key_to)

    def unlink_issue(self, key_from, key_to):
        links = self.jira().issue(key_from, fields=['issuelinks']).fields.issuelinks
        for _ in links:
            if _.outwardIssue.key == key_to:
                self.jira().delete_issue_link(_.id)

    def search_issues(self):
        issues = self.jira().search_issues(
            "status not in (Resolved, Closed) AND assignee not in (EMPTY) AND project in (KB) ORDER BY assignee ASC, project ASC, summary ASC",
            fields=['key', 'summary', 'assignee', 'project'])
        return issues

    #
    # Meta
    #

    def meta_fields(self):
        return self.jira().fields()

    def meta_issue_link_types(self):
        return self.jira().issue_link_types()

    def meta_issue_types(self):
        return self.jira().issue_types()

    def meta_priorities(self):
        return self.jira().priorities()

    def meta_resolutions(self):
        return self.jira().resolutions()

    def meta_statuses(self):
        return self.jira().statuses()

    def meta_transitions(self, key):
        return self.jira().transitions(key)

    #
    # Projects
    #

    def info_project(self, project):
        project = self.jira().project(project)
        return project

    def search_projects(self):
        projects = self.jira().projects()
        return projects

    #
    # Users
    #

    def add_user(self, username, email, password, fullname):
        resource = self.jira().add_user(username, email, password=password, fullname=fullname)
        return resource

    def delete_user(self, username):
        self.jira().delete_user(username)

    def edit_user(self, username, email):
        user = [_ for _ in self.jira().search_users(user=username) if _.name == username][0]
        user.update(emailAddress=email)
        return user

    def search_user(self, filter=None):
        filter = filter.lower() if filter else '@'
        users = self.jira().search_users(user=filter, maxResults=5000)
        return [_ for _ in users if
                filter in _.key.lower() or filter in _.name.lower() or filter in _.emailAddress.lower()]

    #
    # Versions
    #

    def add_version(self, project, name, description):
        project = self.jira().project(project.upper())
        resource = self.jira().create_version(name, project, description=description)

    def delete_version(self, project, name):
        project = self.jira().project(project.upper())
        version = [_ for _ in self.jira().project_versions(project) if _.name == name][0]
        version.delete()

    def edit_version(self, project, name, description):
        project = self.jira().project(project.upper())
        version = [_ for _ in self.jira().project_versions(project) if _.name == name][0]
        version.update(description=description)

    def search_versions(self, project):
        project = self.jira().project(project.upper())
        versions = self.jira().project_versions(project)
        return versions
