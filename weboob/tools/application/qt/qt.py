# -*- coding: utf-8 -*-

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

from __future__ import print_function

import sys
import logging
import re
from threading import Event
from copy import copy
from PyQt4.QtCore import QTimer, SIGNAL, QObject, QString, QSize, QVariant, QMutex, Qt
from PyQt4.QtGui import QMainWindow, QApplication, QStyledItemDelegate, \
                        QStyleOptionViewItemV4, QTextDocument, QStyle, \
                        QAbstractTextDocumentLayout, QPalette, QMessageBox, \
                        QSpinBox, QLineEdit, QComboBox, QCheckBox, QInputDialog

from weboob.core.ouiboube import Weboob, VersionsMismatchError
from weboob.core.scheduler import IScheduler
from weboob.core.repositories import ModuleInstallError
from weboob.tools.config.iconfig import ConfigError
from weboob.exceptions import BrowserUnavailable, BrowserIncorrectPassword, BrowserForbidden
from weboob.tools.value import ValueInt, ValueBool, ValueBackendPassword
from weboob.tools.misc import to_unicode
from weboob.capabilities import UserError

from ..base import Application, MoreResultsAvailable


__all__ = ['QtApplication', 'QtMainWindow', 'QtDo', 'HTMLDelegate']


class QtScheduler(IScheduler):
    def __init__(self, app):
        self.app = app
        self.count = 0
        self.timers = {}

    def schedule(self, interval, function, *args):
        timer = QTimer()
        timer.setInterval(interval * 1000)
        timer.setSingleShot(True)

        count = self.count
        self.count += 1

        timer.start()
        self.app.connect(timer, SIGNAL("timeout()"), lambda: self.timeout(count, None, function, *args))
        self.timers[count] = timer

    def repeat(self, interval, function, *args):
        timer = QTimer()
        timer.setSingleShot(False)

        count = self.count
        self.count += 1

        timer.start(0)
        self.app.connect(timer, SIGNAL("timeout()"), lambda: self.timeout(count, interval, function, *args))
        self.timers[count] = timer

    def timeout(self, _id, interval, function, *args):
        function(*args)
        if interval is None:
            self.timers.pop(_id)
        else:
            self.timers[_id].setInterval(interval * 1000)

    def want_stop(self):
        self.app.quit()

    def run(self):
        self.app.exec_()


class QCallbacksManager(QObject):
    class Request(object):
        def __init__(self):
            self.event = Event()
            self.answer = None

        def __call__(self):
            raise NotImplementedError()

    class LoginRequest(Request):
        def __init__(self, backend_name, value):
            QCallbacksManager.Request.__init__(self)
            self.backend_name = backend_name
            self.value = value

        def __call__(self):
            password, ok = QInputDialog.getText(None,
                '%s request' % self.value.label,
                'Please enter %s for %s' % (self.value.label,
                                            self.backend_name),
                                                QLineEdit.Password)
            return password

    def __init__(self, weboob, parent=None):
        QObject.__init__(self, parent)
        self.weboob = weboob
        self.weboob.callbacks['login'] = self.callback(self.LoginRequest)
        self.mutex = QMutex()
        self.requests = []
        self.connect(self, SIGNAL('new_request'), self.do_request)

    def callback(self, klass):
        def cb(*args, **kwargs):
            return self.add_request(klass(*args, **kwargs))
        return cb

    def do_request(self):
        self.mutex.lock()
        request = self.requests.pop()
        request.answer = request()
        request.event.set()
        self.mutex.unlock()

    def add_request(self, request):
        self.mutex.lock()
        self.requests.append(request)
        self.mutex.unlock()
        self.emit(SIGNAL('new_request'))
        request.event.wait()
        return request.answer


class QtApplication(QApplication, Application):
    def __init__(self):
        QApplication.__init__(self, sys.argv)
        self.setApplicationName(self.APPNAME)

        Application.__init__(self)
        self.cbmanager = QCallbacksManager(self.weboob, self)

    def create_weboob(self):
        return Weboob(scheduler=QtScheduler(self))

    def load_backends(self, *args, **kwargs):
        while True:
            try:
                return Application.load_backends(self, *args, **kwargs)
            except VersionsMismatchError as e:
                msg = 'Versions of modules mismatch with version of weboob.'
            except ConfigError as e:
                msg = unicode(e)

            res = QMessageBox.question(None, 'Configuration error', u'%s\n\nDo you want to update repositories?' % msg, QMessageBox.Yes|QMessageBox.No)
            if res == QMessageBox.No:
                raise e

            # Do not import it globally, it causes circular imports
            from .backendcfg import ProgressDialog
            pd = ProgressDialog('Update of repositories', "Cancel", 0, 100)
            pd.setWindowModality(Qt.WindowModal)
            try:
                self.weboob.update(pd)
            except ModuleInstallError as err:
                QMessageBox.critical(None, self.tr('Update error'),
                                     unicode(self.tr('Unable to update repositories: %s' % err)),
                                     QMessageBox.Ok)
            pd.setValue(100)
            QMessageBox.information(None, self.tr('Update of repositories'),
                                    self.tr('Repositories updated!'), QMessageBox.Ok)


class QtMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)


class QtDo(QObject):
    def __init__(self, weboob, cb, eb=None, fb=None):
        QObject.__init__(self)

        if not eb:
            eb = self.default_eb

        self.weboob = weboob
        self.process = None
        self.cb = cb
        self.eb = eb
        self.fb = fb

        self.connect(self, SIGNAL('cb'), self.local_cb)
        self.connect(self, SIGNAL('eb'), self.local_eb)
        self.connect(self, SIGNAL('fb'), self.local_fb)

    def do(self, *args, **kwargs):
        self.process = self.weboob.do(*args, **kwargs)
        self.process.callback_thread(self.thread_cb, self.thread_eb, self.thread_fb)

    def default_eb(self, backend, error, backtrace):
        if isinstance(error, MoreResultsAvailable):
            # This is not an error, ignore.
            return

        msg = unicode(error)
        if isinstance(error, BrowserIncorrectPassword):
            if not msg:
                msg = 'Invalid login/password.'
        elif isinstance(error, BrowserUnavailable):
            if not msg:
                msg = 'Website is unavailable.'
        elif isinstance(error, BrowserForbidden):
            if not msg:
                msg = 'This action is forbidden.'
        elif isinstance(error, NotImplementedError):
            msg = u'This feature is not supported by this backend.\n\n' \
                  u'To help the maintainer of this backend implement this feature, please contact: %s <%s>' % (backend.MAINTAINER, backend.EMAIL)
        elif isinstance(error, UserError):
            if not msg:
                msg = type(error).__name__
        elif logging.root.level <= logging.DEBUG:
            msg += u'<br />'
            ul_opened = False
            for line in backtrace.split('\n'):
                m = re.match('  File (.*)', line)
                if m:
                    if not ul_opened:
                        msg += u'<ul>'
                        ul_opened = True
                    else:
                        msg += u'</li>'
                    msg += u'<li><b>%s</b>' % m.group(1)
                else:
                    msg += u'<br />%s' % to_unicode(line)
            if ul_opened:
                msg += u'</li></ul>'
            print(error, file=sys.stderr)
            print(backtrace, file=sys.stderr)
        QMessageBox.critical(None, unicode(self.tr('Error with backend %s')) % backend.name,
                             msg, QMessageBox.Ok)

    def local_cb(self, data):
        if self.cb:
            self.cb(data)

    def local_eb(self, backend, error, backtrace):
        if self.eb:
            self.eb(backend, error, backtrace)

    def local_fb(self):
        if self.fb:
            self.fb()

        self.disconnect(self, SIGNAL('cb'), self.local_cb)
        self.disconnect(self, SIGNAL('eb'), self.local_eb)
        self.disconnect(self, SIGNAL('fb'), self.local_fb)
        self.process = None

    def thread_cb(self, data):
        self.emit(SIGNAL('cb'), data)

    def thread_eb(self, backend, error, backtrace):
        self.emit(SIGNAL('eb'), backend, error, backtrace)

    def thread_fb(self):
        self.emit(SIGNAL('fb'))


class HTMLDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        optionV4 = QStyleOptionViewItemV4(option)
        self.initStyleOption(optionV4, index)

        style = optionV4.widget.style() if optionV4.widget else QApplication.style()

        doc = QTextDocument()
        doc.setHtml(optionV4.text)

        # painting item without text
        optionV4.text = QString()
        style.drawControl(QStyle.CE_ItemViewItem, optionV4, painter)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        # Hilight text if item is selected
        if optionV4.state & QStyle.State_Selected:
            ctx.palette.setColor(QPalette.Text, optionV4.palette.color(QPalette.Active, QPalette.HighlightedText))

        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, optionV4)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        optionV4 = QStyleOptionViewItemV4(option)
        self.initStyleOption(optionV4, index)

        doc = QTextDocument()
        doc.setHtml(optionV4.text)
        doc.setTextWidth(optionV4.rect.width())

        return QSize(doc.idealWidth(), max(doc.size().height(), optionV4.decorationSize.height()))


class _QtValueStr(QLineEdit):
    def __init__(self, value):
        QLineEdit.__init__(self)
        self._value = value
        if value.default:
            self.setText(unicode(value.default))
        if value.masked:
            self.setEchoMode(self.Password)

    def set_value(self, value):
        self._value = value
        self.setText(self._value.get())

    def get_value(self):
        self._value.set(unicode(self.text()))
        return self._value


class _QtValueBackendPassword(_QtValueStr):
    def get_value(self):
        self._value._domain = None
        return _QtValueStr.get_value(self)


class _QtValueBool(QCheckBox):
    def __init__(self, value):
        QCheckBox.__init__(self)
        self._value = value
        if value.default:
            self.setChecked(True)

    def set_value(self, value):
        self._value = value
        self.setChecked(self._value.get())

    def get_value(self):
        self._value.set(self.isChecked())
        return self._value


class _QtValueInt(QSpinBox):
    def __init__(self, value):
        QSpinBox.__init__(self)
        self._value = value
        if value.default:
            self.setValue(int(value.default))

    def set_value(self, value):
        self._value = value
        self.setValue(self._value.get())

    def get_value(self):
        self._value.set(self.getValue())
        return self._value


class _QtValueChoices(QComboBox):
    def __init__(self, value):
        QComboBox.__init__(self)
        self._value = value
        for k, l in value.choices.iteritems():
            self.addItem(l, QVariant(k))
            if value.default == k:
                self.setCurrentIndex(self.count()-1)

    def set_value(self, value):
        self._value = value
        for i in xrange(self.count()):
            if unicode(self.itemData(i).toString()) == self._value.get():
                self.setCurrentIndex(i)
                return

    def get_value(self):
        self._value.set(unicode(self.itemData(self.currentIndex()).toString()))
        return self._value


def QtValue(value):
    if isinstance(value, ValueBool):
        klass = _QtValueBool
    elif isinstance(value, ValueInt):
        klass = _QtValueInt
    elif isinstance(value, ValueBackendPassword):
        klass = _QtValueBackendPassword
    elif value.choices is not None:
        klass = _QtValueChoices
    else:
        klass = _QtValueStr

    return klass(copy(value))
