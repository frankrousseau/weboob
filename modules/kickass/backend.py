# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Julien Veyssier
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

from weboob.capabilities.torrent import ICapTorrent, Torrent
from weboob.tools.backend import BaseBackend

from .browser import KickassBrowser

from urllib import quote_plus
from contextlib import closing
from gzip import GzipFile

__all__ = ['KickassBackend']


class KickassBackend(BaseBackend, ICapTorrent):
    NAME = 'kickass'
    MAINTAINER = u'Julien Veyssier'
    EMAIL = 'julien.veyssier@aiur.fr'
    VERSION = '0.i'
    DESCRIPTION = 'Kickass Torrents BitTorrent tracker'
    LICENSE = 'AGPLv3+'
    BROWSER = KickassBrowser

    def get_torrent(self, id):
        return self.browser.get_torrent(id)

    def get_torrent_file(self, id):
        torrent = self.browser.get_torrent(id)
        if not torrent:
            return None

        # decode gzip if needed
        response = self.browser.openurl(torrent.url.encode('utf-8'))
        headers = response.info()
        if headers.get('Content-Encoding', '') == 'gzip':
            with closing(GzipFile(fileobj=response, mode='rb')) as gz:
                data = gz.read()
        else:
            data = response.read()
        return data

    def iter_torrents(self, pattern):
        return self.browser.iter_torrents(quote_plus(pattern.encode('utf-8')))

    def fill_torrent(self, torrent, fields):
        if 'description' in fields or 'files' in fields:
            tor = self.get_torrent(torrent.id)
            torrent.description = tor.description
            torrent.magnet = tor.magnet
            torrent.files = tor.files
            torrent.url = tor.url
        return torrent

    OBJECTS = {
        Torrent: fill_torrent
    }
