# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Romain Bignon
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


from weboob.capabilities.housing import ICapHousing
from weboob.tools.application.qt import QtApplication
from weboob.tools.config.yamlconfig import YamlConfig

from .main_window import MainWindow


class QFlatBoob(QtApplication):
    APPNAME = 'qflatboob'
    VERSION = '0.i'
    COPYRIGHT = 'Copyright(C) 2010-2012 Romain Bignon'
    DESCRIPTION = "Qt application to search for housing."
    SHORT_DESCRIPTION = "search for housing"
    CAPS = ICapHousing
    CONFIG = {'queries': {}}
    STORAGE = {'bookmarks': [], 'read': [], 'notes': {}}

    def main(self, argv):
        self.load_backends(ICapHousing)
        self.create_storage()
        self.load_config(klass=YamlConfig)

        self.main_window = MainWindow(self.config, self.storage, self.weboob)
        self.main_window.show()
        return self.weboob.loop()
