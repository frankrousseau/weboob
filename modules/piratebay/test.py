# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Julien Veyssier, Laurent Bachelier
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

from weboob.tools.test import BackendTest
from weboob.capabilities.torrent import MagnetOnly

from random import choice


class PiratebayTest(BackendTest):
    MODULE = 'piratebay'

    def test_torrent(self):
        # try something popular so we sometimes get a magnet-only torrent
        l = list(self.backend.iter_torrents('ubuntu linux'))
        if len(l):
            torrent = choice(l)
            full_torrent = self.backend.get_torrent(torrent.id)
            assert torrent.name
            assert full_torrent.name == torrent.name
            # I assume descriptions can be empty
            assert isinstance(full_torrent.description, basestring)
            try:
                assert self.backend.get_torrent_file(torrent.id)
            except MagnetOnly as e:
                assert e.magnet.startswith('magnet:')
                assert e.magnet == full_torrent.magnet
