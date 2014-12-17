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

from PyQt4.QtGui import QFrame
from PyQt4.QtCore import SIGNAL

from weboob.applications.qcineoob.ui.minitorrent_ui import Ui_MiniTorrent
from weboob.applications.weboorrents.weboorrents import sizeof_fmt
from weboob.capabilities.base import empty


class MiniTorrent(QFrame):
    def __init__(self, weboob, backend, torrent, parent=None):
        QFrame.__init__(self, parent)
        self.parent = parent
        self.ui = Ui_MiniTorrent()
        self.ui.setupUi(self)

        self.weboob = weboob
        self.backend = backend
        self.torrent = torrent
        self.ui.nameLabel.setText(torrent.name)
        if not empty(torrent.seeders) and not empty(torrent.leechers):
            self.ui.seedLeechLabel.setText('%s/%s' % (torrent.seeders, torrent.leechers))
        if not empty(torrent.size):
            self.ui.sizeLabel.setText(u'%s' % sizeof_fmt(torrent.size))
        self.ui.backendLabel.setText(backend.name)

        self.connect(self.ui.newTabButton, SIGNAL("clicked()"), self.newTabPressed)
        self.connect(self.ui.viewButton, SIGNAL("clicked()"), self.viewPressed)

    def viewPressed(self):
        torrent = self.backend.get_torrent(self.torrent.id)
        if torrent:
            self.parent.doAction('Details of torrent "%s"' %
                                 torrent.name, self.parent.displayTorrent, [torrent, self.backend])

    def newTabPressed(self):
        torrent = self.backend.get_torrent(self.torrent.id)
        self.parent.parent.newTab(u'Details of torrent "%s"' %
             torrent.name, self.backend, torrent=torrent)

    def enterEvent(self, event):
        self.setFrameShadow(self.Sunken)
        QFrame.enterEvent(self, event)

    def leaveEvent(self, event):
        self.setFrameShadow(self.Raised)
        QFrame.leaveEvent(self, event)

    def mousePressEvent(self, event):
        QFrame.mousePressEvent(self, event)

        if event.button() == 4:
            self.newTabPressed()
        else:
            self.viewPressed()
