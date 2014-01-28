# -*- coding: utf-8 -*-

# Copyright(C) 2011 Laurent Bachelier
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




import re

from weboob.tools.capabilities.paste import BasePasteBackend
from weboob.tools.backend import BaseBackend
from weboob.capabilities.base import NotLoaded

from .browser import PastealaconBrowser
from .paste import PastealaconPaste


__all__ = ['PastealaconBackend']


class PastealaconBackend(BaseBackend, BasePasteBackend):
    NAME = 'pastealacon'
    MAINTAINER = u'Laurent Bachelier'
    EMAIL = 'laurent@bachelier.name'
    VERSION = '0.i'
    DESCRIPTION = u'Paste à la con text sharing tool'
    LICENSE = 'AGPLv3+'
    BROWSER = PastealaconBrowser

    EXPIRATIONS = {
        24 * 3600: 'd',
        24 * 3600 * 30: 'm',
        False: 'f',
    }

    def new_paste(self, *args, **kwargs):
        return PastealaconPaste(*args, **kwargs)

    def can_post(self, contents, title=None, public=None, max_age=None):
        try:
            contents.encode(self.browser.ENCODING)
        except UnicodeEncodeError:
            return 0
        if public is False:
            return 0
        if max_age is not None:
            if self.get_closest_expiration(max_age) is None:
                return 0
        # the "title" is filtered (does not even accepts dots)
        if not title or re.match('^\w+$', title) and len(title) <= 24:
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

    def post_paste(self, paste, max_age=None):
        if max_age is not None:
            expiration = self.get_closest_expiration(max_age)
        else:
            expiration = None
        with self.browser:
            self.browser.post_paste(paste, expiration=self.EXPIRATIONS.get(expiration))

    OBJECTS = {PastealaconPaste: fill_paste}
