# -*- coding: utf-8 -*-

# Copyright(C) 2011  Clément Schreiner
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

from weboob.tools.application.qt import QtApplication
from weboob.capabilities.content import ICapContent

from .main_window import MainWindow


class QWebContentEdit(QtApplication):
    APPNAME = 'qwebcontentedit'
    VERSION = '0.j'
    COPYRIGHT = u'Copyright(C) 2011 Clément Schreiner'
    DESCRIPTION = "Qt application allowing to manage content of various websites."
    SHORT_DESCRIPTION = "manage websites content"
    CAPS = ICapContent

    def main(self, argv):
        self.load_backends(ICapContent, storage=self.create_storage())
        self.main_window = MainWindow(self.config, self.weboob, self)
        self.main_window.show()
        return self.weboob.loop()
