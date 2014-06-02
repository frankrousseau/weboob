# -*- coding: utf-8 -*-

# Copyright(C) 2014      Roger Philibert
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


import datetime
from dateutil.parser import parse as parse_date

from weboob.capabilities.messages import ICapMessages, ICapMessagesPost, Thread, Message
from weboob.capabilities.dating import ICapDating, Optimization
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import Value, ValueBackendPassword
from weboob.tools.log import getLogger

from .browser import TinderBrowser, FacebookBrowser


__all__ = ['TinderBackend']


class ProfilesWalker(Optimization):
    def __init__(self, sched, storage, browser):
        self.sched = sched
        self.storage = storage
        self.browser = browser
        self.logger = getLogger('walker', browser.logger)

        self.view_cron = None

    def start(self):
        self.view_cron = self.sched.schedule(1, self.view_profile)
        return True

    def stop(self):
        self.sched.cancel(self.view_cron)
        self.view_cron = None
        return True

    def set_config(self, params):
        pass

    def is_running(self):
        return self.view_cron is not None

    def view_profile(self):
        try:
            self.browser.like_profile()
        finally:
            if self.view_cron is not None:
                self.view_cron = self.sched.schedule(1, self.view_profile)


class TinderBackend(BaseBackend, ICapMessages, ICapMessagesPost, ICapDating):
    NAME = 'tinder'
    DESCRIPTION = u'Tinder dating mobile application'
    MAINTAINER = u'Roger Philibert'
    EMAIL = 'roger.philibert@gmail.com'
    LICENSE = 'AGPLv3+'
    VERSION = '0.j'
    CONFIG = BackendConfig(Value('username',                label='Facebook email'),
                           ValueBackendPassword('password', label='Facebook password'))

    BROWSER = TinderBrowser
    STORAGE = {'contacts': {},
              }

    def create_default_browser(self):
        facebook = FacebookBrowser()
        facebook.login(self.config['username'].get(),
                       self.config['password'].get())
        return TinderBrowser(facebook)

    # ---- ICapDating methods -----------------------

    def init_optimizations(self):
        self.add_optimization('PROFILE_WALKER', ProfilesWalker(self.weboob.scheduler, self.storage, self.browser))

    # ---- ICapMessages methods ---------------------

    def fill_thread(self, thread, fields):
        return self.get_thread(thread)

    def iter_threads(self):
        for thread in self.browser.get_threads():
            t = Thread(thread['_id'])
            t.flags = Thread.IS_DISCUSSION
            t.title = u'Discussion with %s' % thread['person']['name']
            contact = self.storage.get('contacts', t.id, default={'lastmsg': 0})

            birthday = parse_date(thread['person']['birth_date']).date()
            signature = u'Age: %d (%s)' % ((datetime.date.today() - birthday).days / 365.25, birthday)
            signature += u'\nLast ping: %s' % parse_date(thread['person']['ping_time']).strftime('%Y-%m-%d %H:%M:%S')
            signature += u'\nPhotos:\n\t%s' % '\n\t'.join([photo['url'] for photo in thread['person']['photos']])
            signature += u'\n\n%s' % thread['person']['bio']

            t.root = Message(thread=t, id=1, title=t.title,
                             sender=unicode(thread['person']['name']),
                             receivers=[self.browser.my_name],
                             date=parse_date(thread['created_date']),
                             content=u'Match!',
                             children=[],
                             signature=signature,
                             flags=Message.IS_UNREAD if int(contact['lastmsg']) < 1 else 0)
            parent = t.root

            for msg in thread['messages']:
                flags = 0
                if int(contact['lastmsg']) < msg['timestamp']:
                    flags = Message.IS_UNREAD

                msg = Message(thread=t,
                              id=msg['timestamp'],
                              title=t.title,
                              sender=unicode(self.browser.my_name if msg['from'] == self.browser.my_id else thread['person']['name']),
                              receivers=[unicode(self.browser.my_name if msg['to'] == self.browser.my_id else thread['person']['name'])],
                              date=parse_date(msg['sent_date']),
                              content=unicode(msg['message']),
                              children=[],
                              parent=parent,
                              signature=signature if msg['to'] == self.browser.my_id else u'',
                              flags=flags)
                parent.children.append(msg)
                parent = msg

            yield t

    def get_thread(self, _id):
        for t in self.iter_threads():
            if t.id == _id:
                return t

    def iter_unread_messages(self):
        for thread in self.iter_threads():
            for message in thread.iter_all_messages():
                if message.flags & message.IS_UNREAD:
                    yield message

    def set_message_read(self, message):
        contact = self.storage.get('contacts', message.thread.id, default={'lastmsg': 0})
        if int(contact['lastmsg']) < int(message.id):
            contact['lastmsg'] = int(message.id)
            self.storage.set('contacts', message.thread.id, contact)
            self.storage.save()

    # ---- ICapMessagesPost methods ---------------------

    def post_message(self, message):
        self.browser.post_message(message.thread.id, message.content)

    OBJECTS = {Thread: fill_thread,
              }
