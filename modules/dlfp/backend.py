# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011  Romain Bignon
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




from datetime import datetime, timedelta
import time

from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.browser import BrowserForbidden
from weboob.tools.newsfeed import Newsfeed
from weboob.tools.value import Value, ValueBool, ValueBackendPassword
from weboob.capabilities.messages import ICapMessages, ICapMessagesPost, Message, Thread, CantSendMessage
from weboob.capabilities.content import ICapContent, Content

from .browser import DLFP
from .tools import rssid, id2url


__all__ = ['DLFPBackend']


class DLFPBackend(BaseBackend, ICapMessages, ICapMessagesPost, ICapContent):
    NAME = 'dlfp'
    MAINTAINER = u'Romain Bignon'
    EMAIL = 'romain@weboob.org'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = "Da Linux French Page news website"
    CONFIG = BackendConfig(Value('username',                label='Username', default=''),
                           ValueBackendPassword('password', label='Password', default=''),
                           ValueBool('get_news',            label='Get newspapers', default=True),
                           ValueBool('get_diaries',         label='Get diaries', default=False),
                           ValueBool('get_polls',           label='Get polls', default=False),
                           ValueBool('get_board',           label='Get board', default=False),
                           ValueBool('get_wiki',            label='Get wiki', default=False),
                           ValueBool('get_tracker',         label='Get tracker', default=False))
    STORAGE = {'seen': {}}
    BROWSER = DLFP

    FEEDS = {'get_news':     "https://linuxfr.org/news.atom",
             'get_diaries':  "https://linuxfr.org/journaux.atom",
             'get_polls':    "https://linuxfr.org/sondages.atom",
             'get_board':    "https://linuxfr.org/forums.atom",
             'get_wiki':     "https://linuxfr.org/wiki.atom",
             'get_tracker':  "https://linuxfr.org/suivi.atom",
            }

    def create_default_browser(self):
        username = self.config['username'].get()
        if username:
            password = self.config['password'].get()
        else:
            password = None
        return self.create_browser(username, password)

    def deinit(self):
        # don't need to logout if the browser hasn't been used.
        if not self._browser:
            return

        with self.browser:
            self.browser.close_session()

    #### ICapMessages ##############################################

    def iter_threads(self):
        whats = set()
        for param, url in self.FEEDS.iteritems():
            if self.config[param].get():
                whats.add(url)

        for what in whats:
            for article in Newsfeed(what, rssid).iter_entries():
                if article.datetime and (datetime.now() - article.datetime) > timedelta(days=60):
                    continue
                thread = Thread(article.id)
                thread.title = article.title
                thread._rsscomment = article.rsscomment
                if article.datetime:
                    thread.date = article.datetime
                yield thread

    def get_thread(self, id, getseen=True):
        if not isinstance(id, Thread):
            thread = None
        else:
            thread = id
            id = thread.id

            if thread.date:
                self.storage.set('date', id, thread.date)
                self.storage.save()

        with self.browser:
            content = self.browser.get_content(id)

        if not content:
            return None

        if not thread:
            thread = Thread(content.id)

        flags = Message.IS_HTML
        if not thread.id in self.storage.get('seen', default={}):
            flags |= Message.IS_UNREAD

        thread.title = content.title
        if not thread.date:
            thread.date = content.date

        thread.root = Message(thread=thread,
                              id='0',  # root message
                              title=content.title,
                              sender=content.author or u'',
                              receivers=None,
                              date=thread.date,
                              parent=None,
                              content=content.body,
                              signature='URL: %s' % self.browser.absurl(id2url(content.id)),
                              children=[],
                              flags=flags)

        for com in content.comments:
            self._insert_comment(com, thread.root, getseen)

        return thread

    def _insert_comment(self, com, parent, getseen=True):
        """"
        Insert 'com' comment and its children in the parent message.
        """
        flags = Message.IS_HTML
        if not com.id in self.storage.get('seen', parent.thread.id, 'comments', default=[]):
            flags |= Message.IS_UNREAD

        if getseen or flags & Message.IS_UNREAD:
            com.parse()
            message = Message(thread=parent.thread,
                              id=com.id,
                              title=com.title,
                              sender=com.author or u'',
                              receivers=None,
                              date=com.date,
                              parent=parent,
                              content=com.body,
                              signature=com.signature +
                                        '<br />'.join(['Score: %d' % com.score,
                                                       'URL: %s' % com.url]),
                              children=[],
                              flags=flags)
        else:
            message = Message(thread=parent.thread,
                              id=com.id,
                              children=[],
                              flags=flags)
        parent.children.append(message)
        for sub in com.comments:
            self._insert_comment(sub, message, getseen)

    def iter_unread_messages(self):
        for thread in self.iter_threads():
            # Check if we have seen all comments of this thread.
            with self.browser:
                oldhash = self.storage.get('hash', thread.id, default="")
                newhash = self.browser.get_hash(thread._rsscomment)
            if oldhash != newhash:
                self.storage.set('hash', thread.id, newhash)
                self.storage.save()

                self.fill_thread(thread, 'root', getseen=False)
                for m in thread.iter_all_messages():
                    if m.flags & m.IS_UNREAD:
                        yield m

    def set_message_read(self, message):
        self.storage.set('seen', message.thread.id, 'comments',
            self.storage.get('seen', message.thread.id, 'comments', default=[]) + [message.id])
        self.storage.save()

        lastpurge = self.storage.get('lastpurge', default=0)
        # 86400 = one day
        if time.time() - lastpurge > 86400:
            self.storage.set('lastpurge', time.time())
            self.storage.save()

            # we can't directly delete without a "RuntimeError: dictionary changed size during iteration"
            todelete = []

            for id in self.storage.get('seen', default={}):
                date = self.storage.get('date', id, default=0)
                # if no date available, create a new one (compatibility with "old" storage)
                if date == 0:
                    self.storage.set('date', id, datetime.now())
                elif datetime.now() - date > timedelta(days=60):
                    todelete.append(id)

            for id in todelete:
                self.storage.delete('hash', id)
                self.storage.delete('date', id)
                self.storage.delete('seen', id)
            self.storage.save()

    def fill_thread(self, thread, fields, getseen=True):
        return self.get_thread(thread, getseen)

    #### ICapMessagesReply #########################################
    def post_message(self, message):
        if not self.browser.username:
            raise BrowserForbidden()
        if not message.parent:
            raise CantSendMessage('Posting news and diaries on DLFP is not supported yet')

        assert message.thread

        with self.browser:
            return self.browser.post_comment(message.thread.id,
                                             message.parent.id,
                                             message.title,
                                             message.content)

    #### ICapContent ###############################################
    def get_content(self, _id, revision=None):
        if isinstance(_id, basestring):
            content = Content(_id)
        else:
            content = _id
            _id = content.id

        if revision:
            raise NotImplementedError('Website does not provide access to older revisions sources.')
        with self.browser:
            data = self.browser.get_wiki_content(_id)

        if data is None:
            return None

        content.content = data
        return content

    def push_content(self, content, message=None, minor=False):
        if not self.browser.username:
            raise BrowserForbidden()
        with self.browser:
            return self.browser.set_wiki_content(content.id, content.content, message)

    def get_content_preview(self, content):
        with self.browser:
            return self.browser.get_wiki_preview(content.id, content.content)

    OBJECTS = {Thread: fill_thread}
