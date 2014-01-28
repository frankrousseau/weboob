# -*- coding: utf-8 -*-

# Copyright(C) 2013 Julien Veyssier
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

from weboob.capabilities.subtitle import ICapSubtitle, LanguageNotSupported, Subtitle
from weboob.applications.suboob.suboob import LANGUAGE_CONV
from weboob.tools.backend import BaseBackend

from .browser import OpensubtitlesBrowser

from urllib import quote_plus

__all__ = ['OpensubtitlesBackend']


class OpensubtitlesBackend(BaseBackend, ICapSubtitle):
    NAME = 'opensubtitles'
    MAINTAINER = u'Julien Veyssier'
    EMAIL = 'julien.veyssier@aiur.fr'
    VERSION = '0.i'
    DESCRIPTION = 'Opensubtitles subtitle website'
    LICENSE = 'AGPLv3+'
    BROWSER = OpensubtitlesBrowser

    def get_subtitle(self, id):
        return self.browser.get_subtitle(id)

    def get_subtitle_file(self, id):
        subtitle = self.browser.get_subtitle(id)
        if not subtitle:
            return None

        return self.browser.openurl(subtitle.url.encode('utf-8')).read()

    def iter_subtitles(self, language, pattern):
        if language not in LANGUAGE_CONV.keys():
            raise LanguageNotSupported()
        return self.browser.iter_subtitles(language, quote_plus(pattern.encode('utf-8')))

    def fill_subtitle(self, subtitle, fields):
        if 'description' in fields:
            sub = self.get_subtitle(subtitle.id)
            subtitle.description = sub.description

        return subtitle

    OBJECTS = {
        Subtitle: fill_subtitle,
    }
