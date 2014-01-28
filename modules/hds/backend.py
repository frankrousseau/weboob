# -*- coding: utf-8 -*-

# Copyright(C) 2011  Romain Bignon
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




from weboob.tools.backend import BaseBackend
from weboob.capabilities.messages import ICapMessages, Message, Thread

from .browser import HDSBrowser


__all__ = ['HDSBackend']


class HDSBackend(BaseBackend, ICapMessages):
    NAME = 'hds'
    MAINTAINER = u'Romain Bignon'
    EMAIL = 'romain@weboob.org'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = u"Histoires de Sexe French erotic novels"
    STORAGE = {'seen': []}
    BROWSER = HDSBrowser

    #### ICapMessages ##############################################

    def iter_threads(self):
        with self.browser:
            for story in self.browser.iter_stories():
                thread = Thread(story.id)
                thread.title = story.title
                thread.date = story.date
                yield thread

    GENDERS = ['<unknown>', 'boy', 'girl', 'transexual']

    def get_thread(self, id):
        if isinstance(id, Thread):
            thread = id
            id = thread.id
        else:
            thread = None

        with self.browser:
            story = self.browser.get_story(id)

        if not story:
            return None

        if not thread:
            thread = Thread(story.id)

        flags = 0
        if not thread.id in self.storage.get('seen', default=[]):
            flags |= Message.IS_UNREAD

        thread.title = story.title
        thread.date = story.date
        thread.root = Message(thread=thread,
                              id=0,
                              title=story.title,
                              sender=story.author.name,
                              receivers=None,
                              date=thread.date,
                              parent=None,
                              content=story.body,
                              children=[],
                              signature='Written by a %s (%s)' % (self.GENDERS[story.author.sex], story.author.email),
                              flags=flags)

        return thread

    def iter_unread_messages(self):
        for thread in self.iter_threads():
            if thread.id in self.storage.get('seen', default=[]):
                continue
            self.fill_thread(thread, 'root')
            yield thread.root

    def set_message_read(self, message):
        self.storage.set('seen', self.storage.get('seen', default=[]) + [message.thread.id])
        self.storage.save()

    def fill_thread(self, thread, fields):
        return self.get_thread(thread)

    OBJECTS = {Thread: fill_thread}
