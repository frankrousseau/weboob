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


from weboob.capabilities.cinema import CapCinema
from weboob.capabilities.torrent import CapTorrent
from weboob.capabilities.subtitle import CapSubtitle
from weboob.tools.application.qt import QtApplication

from .main_window import MainWindow


class QCineoob(QtApplication):
    APPNAME = 'qcineoob'
    VERSION = '1.1'
    COPYRIGHT = 'Copyright(C) 2013-YEAR Julien Veyssier'
    DESCRIPTION = "Qt application allowing to search movies, people, torrent and subtitles."
    SHORT_DESCRIPTION = "search movies, people, torrent and subtitles"
    CAPS = CapCinema, CapTorrent, CapSubtitle
    CONFIG = {'settings': {'backend': '',
                           'maxresultsnumber': '10',
                           'showthumbnails': '0'
                           }
              }

    def main(self, argv):
        self.load_backends([CapCinema, CapTorrent, CapSubtitle])
        self.load_config()

        self.main_window = MainWindow(self.config, self.weboob, self)
        self.main_window.show()
        return self.weboob.loop()
