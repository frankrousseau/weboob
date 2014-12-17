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

import urllib

from PyQt4.QtCore import SIGNAL, Qt
from PyQt4.QtGui import QFrame, QImage, QPixmap, QApplication, QMessageBox

from weboob.applications.qcineoob.ui.person_ui import Ui_Person
from weboob.capabilities.base import empty


class Person(QFrame):
    def __init__(self, person, backend, parent=None):
        QFrame.__init__(self, parent)
        self.parent = parent
        self.ui = Ui_Person()
        self.ui.setupUi(self)

        self.connect(self.ui.filmographyButton, SIGNAL("clicked()"), self.filmography)
        self.connect(self.ui.biographyButton, SIGNAL("clicked()"), self.biography)
        self.connect(self.ui.moviesInCommonButton, SIGNAL("clicked()"), self.moviesInCommon)

        self.person = person
        self.backend = backend
        self.gotThumbnail()
        self.ui.nameLabel.setText(person.name)

        self.ui.idEdit.setText(u'%s@%s' % (person.id, backend.name))
        if not empty(person.real_name):
            self.ui.realNameLabel.setText('%s' % person.real_name)
        else:
            self.ui.realNameLabel.parent().hide()
        if not empty(person.birth_place):
            self.ui.birthPlaceLabel.setText('%s' % person.birth_place)
        else:
            self.ui.birthPlaceLabel.parent().hide()
        if not empty(person.birth_date):
            self.ui.birthDateLabel.setText(person.birth_date.strftime('%Y-%m-%d'))
        else:
            self.ui.birthDateLabel.parent().hide()
        if not empty(person.death_date):
            self.ui.deathDateLabel.setText(person.death_date.strftime('%Y-%m-%d'))
        else:
            self.ui.deathDateLabel.parent().hide()
        self.ui.shortBioPlain.setPlainText('%s' % person.short_biography)
        for role in person.roles.keys():
            self.ui.filmographyCombo.addItem(role)
        self.ui.verticalLayout_2.setAlignment(Qt.AlignTop)

    def gotThumbnail(self):
        if not empty(self.person.thumbnail_url):
            data = urllib.urlopen(self.person.thumbnail_url).read()
            img = QImage.fromData(data)
            self.ui.imageLabel.setPixmap(QPixmap.fromImage(img).scaledToWidth(220,Qt.SmoothTransformation))

    def filmography(self):
        role = None
        tosearch = unicode(self.ui.filmographyCombo.currentText())
        role_desc = ''
        if tosearch != 'all':
            role = tosearch
            role_desc = ' as %s' % role
        self.parent.doAction('Filmography of "%s"%s' % (self.person.name, role_desc),
                             self.parent.filmographyAction, [self.backend.name, self.person.id, role])

    def biography(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.backend.fill_person(self.person, 'biography')
        bio = self.person.biography
        self.ui.shortBioPlain.setPlainText(u'%s' % bio)
        self.ui.biographyLabel.setText('Full biography:')
        self.ui.biographyButton.hide()
        QApplication.restoreOverrideCursor()

    def moviesInCommon(self):
        my_id = self.person.id
        my_name = self.person.name
        other_id = unicode(self.ui.moviesInCommonEdit.text()).split('@')[0]
        other_person = self.backend.get_person(other_id)
        if other_id == self.person.id:
            QMessageBox.critical(None, self.tr('"Moviess in common" error'),
                                 unicode(self.tr('Nice try\nThe persons must be different')),
                                 QMessageBox.Ok)
        elif not other_person:
            QMessageBox.critical(None, self.tr('"Movies in common" error'),
                                 unicode(self.tr('Person not found: %s' % other_id)),
                                 QMessageBox.Ok)
        else:
            other_name = other_person.name
            desc = 'Movies in common %s, %s'%(my_name, other_name)
            self.parent.doAction(desc, self.parent.moviesInCommonAction, [self.backend.name, my_id, other_id])
