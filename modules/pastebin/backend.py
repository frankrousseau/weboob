# -*- coding: utf-8 -*-

# Copyright(C) 2011-2012 Laurent Bachelier
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




from weboob.tools.capabilities.paste import BasePasteBackend
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.capabilities.base import NotLoaded
from weboob.tools.value import Value, ValueBackendPassword

from .browser import PastebinBrowser
from .paste import PastebinPaste


__all__ = ['PastebinBackend']


class PastebinBackend(BaseBackend, BasePasteBackend):
    NAME = 'pastebin'
    MAINTAINER = u'Laurent Bachelier'
    EMAIL = 'laurent@bachelier.name'
    VERSION = '0.i'
    DESCRIPTION = 'Pastebin text sharing service'
    LICENSE = 'AGPLv3+'
    BROWSER = PastebinBrowser
    CONFIG = BackendConfig(
        Value('username', label='Optional username', default=''),
        ValueBackendPassword('password', label='Optional password', default=''),
        ValueBackendPassword('api_key',  label='Optional API key',  default='', noprompt=True),
    )

    EXPIRATIONS = {
        600: '10M',
        3600: '1H',
        3600 * 24: '1D',
        3600 * 24 * 30: '1M',
        False: 'N',
    }

    def create_default_browser(self):
        username = self.config['username'].get()
        if username:
            password = self.config['password'].get()
        else:
            password = None
        return self.create_browser(self.config['api_key'].get() if self.config['api_key'].get() else None,
                                   username, password, get_home=False)

    def new_paste(self, *args, **kwargs):
        return PastebinPaste(*args, **kwargs)

    def can_post(self, contents, title=None, public=None, max_age=None):
        if max_age is not None:
            if self.get_closest_expiration(max_age) is None:
                return 0
        if not title or len(title) <= 60:
            return 2
        return 1

    def get_paste(self, _id):
        with self.browser:
            return self.browser.get_paste(_id)

    def fill_paste(self, paste, fields):
        # if we only want the contents
        if fields == ['contents']:
            if paste.contents is NotLoaded:
                with self.browser:
                    contents = self.browser.get_contents(paste.id)
                paste.contents = contents
        # get all fields
        elif fields is None or len(fields):
            with self.browser:
                self.browser.fill_paste(paste)
        return paste

    def post_paste(self, paste, max_age=None, use_api=True):
        if max_age is not None:
            expiration = self.get_closest_expiration(max_age)
        else:
            expiration = None
        with self.browser:
            if use_api and self.config.get('api_key').get():
                self.browser.api_post_paste(paste, expiration=self.EXPIRATIONS.get(expiration))
            else:
                self.browser.post_paste(paste, expiration=self.EXPIRATIONS.get(expiration))

    OBJECTS = {PastebinPaste: fill_paste}
