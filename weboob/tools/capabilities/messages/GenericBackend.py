# -*- coding: utf-8 -*-

# Copyright(C) 2011  Julien Hebert
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


import time
from weboob.capabilities.messages import ICapMessages, Message, Thread
from weboob.tools.backend import BaseBackend
from weboob.tools.newsfeed import Newsfeed


class GenericNewspaperBackend(BaseBackend, ICapMessages):
    """
    GenericNewspaperBackend class
    """
    MAINTAINER = u'Julien Hebert'
    EMAIL = 'juke@free.fr'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    STORAGE = {'seen': {}}
    RSS_FEED = None
    RSSID = None
    URL2ID = None
    RSSSIZE = 0

    def _get_thread(self, id):
        for thread in self.iter_threads():
            if thread.id == id:
                return thread

    def get_thread(self, _id):
        if isinstance(_id, Thread):
            thread = _id
            id = thread.id
        else:
            thread = self._get_thread(_id)
            id = _id

        with self.browser:
            content = self.browser.get_content(id)

        if content is None:
            return None

        if not thread:
            thread = Thread(id)

        flags = Message.IS_HTML
        if not thread.id in self.storage.get('seen', default={}):
            flags |= Message.IS_UNREAD
        thread.title = content.title
        if not thread.date:
            thread.date = content.date

        thread.root = Message(
            thread=thread,
            id=0,
            title=content.title,
            sender=content.author,
            receivers=None,
            date=thread.date,
            parent=None,
            content=content.body,
            signature='<a href="%s">URL</a> \n' % content.url,
            flags=flags,
            children=[])
        return thread

    def iter_threads(self):
        for article in Newsfeed(self.RSS_FEED, GenericNewspaperBackend.RSSID).iter_entries():
            thread = Thread(article.id)
            thread.title = article.title
            thread.date = article.datetime
            yield(thread)

    def fill_thread(self, thread, fields):
        "fill the thread"
        t = self.get_thread(thread)
        return t or thread

    def iter_unread_messages(self):
        for thread in self.iter_threads():
            if thread.id in self.storage.get('seen', default={}):
                continue
            self.fill_thread(thread, 'root')
            for msg in thread.iter_all_messages():
                yield msg

    def set_message_read(self, message):
        self.storage.set(
            'seen',
            message.thread.id,
            'comments',
            self.storage.get(
                'seen',
                message.thread.id,
                'comments',
                default=[]) + [message.id])

        if self.URL2ID and self.RSSSIZE != 0:
            url2id = self.URL2ID
            lastpurge = self.storage.get('lastpurge', default=0)
            l = []
            if time.time() - lastpurge > 7200:
                self.storage.set('lastpurge', time.time())
                for id in self.storage.get('seen', default={}):
                    l.append((int(url2id(id)), id))
                l.sort()
                l.reverse()
                tosave = [v[1] for v in l[0:self.RSSSIZE + 10]]
                toremove = set([v for v in self.storage.get('seen', default={})]).difference(tosave)
                for id in toremove:
                    self.storage.delete('seen', id)

        self.storage.save()

    OBJECTS = {Thread: fill_thread}
