# -*- coding: utf-8 -*-
# vim: ft=python et softtabstop=4 cinoptions=4 shiftwidth=4 ts=4 ai

# Copyright(C) 2010-2011 Romain Bignon
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


from weboob.tools.application.qt import BackendCfg, QtApplication


class QWeboobCfg(QtApplication):
    APPNAME = 'qweboobcfg'
    VERSION = '0.i'
    COPYRIGHT = 'Copyright(C) 2010-2011 Romain Bignon'
    DESCRIPTION = "weboob-config-qt is a graphical application to add/edit/remove backends, " \
                  "and to register new website accounts."
    SHORT_DESCRIPTION = "manage backends or register new accounts"

    def main(self, argv):
        self.load_backends()

        self.dlg = BackendCfg(self.weboob)
        self.dlg.show()

        return self.weboob.loop()
