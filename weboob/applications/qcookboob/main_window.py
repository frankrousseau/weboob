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

import os
import codecs

from PyQt4.QtCore import SIGNAL, Qt, QStringList
from PyQt4.QtGui import QApplication, QCompleter

from weboob.capabilities.recipe import CapRecipe
from weboob.tools.application.qt import QtMainWindow, QtDo
from weboob.tools.application.qt.backendcfg import BackendCfg

from weboob.applications.qcookboob.ui.main_window_ui import Ui_MainWindow

from .minirecipe import MiniRecipe
from .recipe import Recipe


class MainWindow(QtMainWindow):
    def __init__(self, config, weboob, app, parent=None):
        QtMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.config = config
        self.weboob = weboob
        self.app = app
        self.minis = []
        self.current_info_widget = None

        # search history is a list of patterns which have been searched
        self.search_history = self.loadSearchHistory()
        self.updateCompletion()

        # action history is composed by the last action and the action list
        # An action is a function, a list of arguments and a description string
        self.action_history = {'last_action': None, 'action_list': []}
        self.connect(self.ui.backButton, SIGNAL("clicked()"), self.doBack)
        self.ui.backButton.hide()
        self.connect(self.ui.stopButton, SIGNAL("clicked()"), self.stopProcess)
        self.ui.stopButton.hide()

        self.connect(self.ui.searchEdit, SIGNAL("returnPressed()"), self.search)
        self.connect(self.ui.idEdit, SIGNAL("returnPressed()"), self.searchId)

        count = self.config.get('settings', 'maxresultsnumber')
        self.ui.countSpin.setValue(int(count))

        self.connect(self.ui.actionBackends, SIGNAL("triggered()"), self.backendsConfig)
        self.connect(self.ui.actionQuit, SIGNAL("triggered()"), self.close)

        self.loadBackendsList()

        if self.ui.backendEdit.count() == 0:
            self.backendsConfig()

    def backendsConfig(self):
        bckndcfg = BackendCfg(self.weboob, (CapRecipe, ), self)
        if bckndcfg.run():
            self.loadBackendsList()

    def loadBackendsList(self):
        self.ui.backendEdit.clear()
        for i, backend in enumerate(self.weboob.iter_backends()):
            if i == 0:
                self.ui.backendEdit.addItem('All backends', '')
            self.ui.backendEdit.addItem(backend.name, backend.name)
            if backend.name == self.config.get('settings', 'backend'):
                self.ui.backendEdit.setCurrentIndex(i+1)

        if self.ui.backendEdit.count() == 0:
            self.ui.searchEdit.setEnabled(False)
        else:
            self.ui.searchEdit.setEnabled(True)

    def loadSearchHistory(self):
        ''' Return search string history list loaded from history file
        '''
        result = []
        history_path = os.path.join(self.weboob.workdir, 'qcookboob_history')
        if os.path.exists(history_path):
            f = codecs.open(history_path, 'r', 'utf-8')
            conf_hist = f.read()
            f.close()
            if conf_hist is not None and conf_hist.strip() != '':
                result = conf_hist.strip().split('\n')
        return result

    def saveSearchHistory(self):
        ''' Save search history in history file
        '''
        if len(self.search_history) > 0:
            history_path = os.path.join(self.weboob.workdir, 'qcookboob_history')
            f = codecs.open(history_path, 'w', 'utf-8')
            f.write('\n'.join(self.search_history))
            f.close()

    def updateCompletion(self):
        qc = QCompleter(QStringList(self.search_history), self)
        qc.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.searchEdit.setCompleter(qc)

    def getCount(self):
        num = self.ui.countSpin.value()
        if num == 0:
            return None
        else:
            return num

    def stopProcess(self):
        self.process.process.finish_event.set()

    def doAction(self, description, fun, args):
        ''' Call fun with args as arguments
        and save it in the action history
        '''
        self.ui.currentActionLabel.setText(description)
        if self.action_history['last_action'] is not None:
            self.action_history['action_list'].append(self.action_history['last_action'])
            self.ui.backButton.setToolTip(self.action_history['last_action']['description'])
            self.ui.backButton.show()
        self.action_history['last_action'] = {'function': fun, 'args': args, 'description': description}
        return fun(*args)

    def doBack(self):
        ''' Go back in action history
        Basically call previous function and update history
        '''
        if len(self.action_history['action_list']) > 0:
            todo = self.action_history['action_list'].pop()
            self.ui.currentActionLabel.setText(todo['description'])
            self.action_history['last_action'] = todo
            if len(self.action_history['action_list']) == 0:
                self.ui.backButton.hide()
            else:
                self.ui.backButton.setToolTip(self.action_history['action_list'][-1]['description'])
            return todo['function'](*todo['args'])

    def search(self):
        pattern = unicode(self.ui.searchEdit.text())
        # arbitrary max number of completion word
        if len(self.search_history) > 50:
            self.search_history.pop(0)
        if pattern not in self.search_history:
            self.search_history.append(pattern)
            self.updateCompletion()

        self.searchRecipe()

    def searchRecipe(self):
        pattern = unicode(self.ui.searchEdit.text())
        if not pattern:
            return
        self.doAction(u'Search recipe "%s"' % pattern, self.searchRecipeAction, [pattern])

    def searchRecipeAction(self, pattern):
        self.ui.stackedWidget.setCurrentWidget(self.ui.list_page)
        for mini in self.minis:
            self.ui.list_content.layout().removeWidget(mini)
            mini.hide()
            mini.deleteLater()

        self.minis = []
        self.ui.searchEdit.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        backend_name = str(self.ui.backendEdit.itemData(self.ui.backendEdit.currentIndex()).toString())

        self.process = QtDo(self.weboob, self.addRecipe)
        self.process.do(self.app._do_complete, self.getCount(), ('title'), 'iter_recipes', pattern, backends=backend_name, caps=CapRecipe)
        self.ui.stopButton.show()

    def addRecipe(self, backend, recipe):
        if not backend:
            self.ui.searchEdit.setEnabled(True)
            QApplication.restoreOverrideCursor()
            self.process = None
            self.ui.stopButton.hide()
            return
        minirecipe = MiniRecipe(self.weboob, backend, recipe, self)
        self.ui.list_content.layout().addWidget(minirecipe)
        self.minis.append(minirecipe)

    def displayRecipe(self, recipe, backend):
        self.ui.stackedWidget.setCurrentWidget(self.ui.info_page)
        if self.current_info_widget is not None:
            self.ui.info_content.layout().removeWidget(self.current_info_widget)
            self.current_info_widget.hide()
            self.current_info_widget.deleteLater()
        wrecipe = Recipe(recipe, backend, self)
        self.ui.info_content.layout().addWidget(wrecipe)
        self.current_info_widget = wrecipe
        QApplication.restoreOverrideCursor()

    def searchId(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        id = unicode(self.ui.idEdit.text())
        if '@' in id:
            backend_name = id.split('@')[1]
            id = id.split('@')[0]
        else:
            backend_name = None
        for backend in self.weboob.iter_backends():
            if (backend_name and backend.name == backend_name) or not backend_name:
                recipe = backend.get_recipe(id)
                if recipe:
                    self.doAction('Details of recipe "%s"' % recipe.title, self.displayRecipe, [recipe, backend])
        QApplication.restoreOverrideCursor()

    def closeEvent(self, ev):
        self.config.set('settings', 'backend', str(self.ui.backendEdit.itemData(
            self.ui.backendEdit.currentIndex()).toString()))
        self.saveSearchHistory()
        self.config.set('settings', 'maxresultsnumber', self.ui.countSpin.value())

        self.config.save()
        ev.accept()
