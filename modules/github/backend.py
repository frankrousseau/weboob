# -*- coding: utf-8 -*-

# Copyright(C) 2013      Vincent A
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import Value, ValueBackendPassword
from weboob.capabilities.bugtracker import ICapBugTracker, Issue, Project, User, Version, Status, Update, Attachment

from .browser import GithubBrowser


__all__ = ['GithubBackend']


STATUSES = {'open': Status('open', u'Open', Status.VALUE_NEW),
            'closed': Status('closed', u'closed', Status.VALUE_RESOLVED)}
# TODO tentatively parse github "labels"?

class GithubBackend(BaseBackend, ICapBugTracker):
    NAME = 'github'
    DESCRIPTION = u'GitHub issues tracking'
    MAINTAINER = u'Vincent A'
    EMAIL = 'dev@indigo.re'
    LICENSE = 'AGPLv3+'
    VERSION = '0.j'
    CONFIG = BackendConfig(Value('username', label='Username', default=''),
                           ValueBackendPassword('password', label='Password', default=''))

    BROWSER = GithubBrowser

    def create_default_browser(self):
        username = self.config['username'].get()
        if username:
            password = self.config['password'].get()
        else:
            password = None
        return self.create_browser(username, password)

    def get_project(self, _id):
        d = self.browser.get_project(_id)

        project = Project(_id, d['name'])
        project.members = list(self._iter_members(project.id))
        project.statuses = list(STATUSES.values())
        project.categories = []
        project.versions = list(self._iter_versions(project.id))

        return project

    def get_issue(self, _id):
        project_id, issue_number = self._extract_issue_id(_id)
        project = self.get_project(project_id)

        d = self.browser.get_issue(project_id, issue_number)

        issue = self._make_issue(d, project)
        if d['has_comments']:
            self._fetch_comments(issue)

        return issue

    def iter_issues(self, query):
        if ((query.assignee, query.author, query.status, query.title) ==
                                             (None, None, None, None)):
            it = self.browser.iter_project_issues(query.project)
        else:
            it = self.browser.iter_issues(query)

        project = self.get_project(query.project)
        for d in it:
            issue = self._make_issue(d, project)
            yield issue

    def create_issue(self, project_id):
        issue = Issue(0)
        issue.project = self.get_project(project_id)
        return issue

    def post_issue(self, issue):
        assert not issue.attachments
        if issue.id and issue.id != '0':
            _, issue_number = self._extract_issue_id(issue.id)
            self.browser.edit_issue(issue, issue_number)
        else:
            self.browser.post_issue(issue)

    def update_issue(self, issue_id, update):
        assert not update.attachments
        self.browser.post_comment(issue_id, update.message)

    # iter_projects, remove_issue are impossible

    def _iter_members(self, project_id):
        for d in self.browser.iter_members(project_id):
            yield User(d['id'], d['name'])

    def _iter_versions(self, project_id):
        for d in self.browser.iter_milestones(project_id):
            yield Version(d['id'], d['name'])

    def _make_issue(self, d, project):
        _id = self._build_issue_id(project.id, d['number'])
        issue = Issue(_id)
        issue.project = project
        issue.title = d['title']
        issue.body = d['body']
        issue.creation = d['creation']
        issue.updated = d['updated']
        issue.author = project.find_user(d['author'], None)
        if not issue.author:
            # may duplicate users
            issue.author = User(d['author'], d['author'])
        issue.status = STATUSES[d['status']]

        if d['assignee']:
            issue.assignee = project.find_user(d['assignee'], None)
        else:
            issue.assignee = None

        if d['version']:
            issue.version = project.find_version(d['version'], None)
        else:
            issue.version = None

        issue.category = None

        issue.attachments = [self._make_attachment(dattach) for dattach in d['attachments']]

        return issue

    def _fetch_comments(self, issue):
        project_id, issue_number = self._extract_issue_id(issue.id)
        if not issue.history:
            issue.history = []
        issue.history += [self._make_comment(dcomment, issue.project) for dcomment in self.browser.iter_comments(project_id, issue_number)]

    def _make_attachment(self, d):
        a = Attachment(d['url'])
        a.url = d['url']
        a.filename = d['filename']
        return a

    def _make_comment(self, d, project):
        u = Update(d['id'])
        u.message = d['message']
        u.author = project.find_user(d['author'], None)
        if not u.author:
            # may duplicate users
            u.author = User(d['author'], d['author'])
        u.date = d['date']
        u.changes = []
        u.attachments = [self._make_attachment(dattach) for dattach in d['attachments']]
        return u

    @staticmethod
    def _extract_issue_id(_id):
        return _id.rsplit('/', 1)

    @staticmethod
    def _build_issue_id(project_id, issue_number):
        return '%s/%s' % (project_id, issue_number)
