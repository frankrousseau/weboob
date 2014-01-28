# -*- coding: utf-8 -*-

# Copyright(C) 2012      Gabriel Serme
# Copyright(C) 2011      Gabriel Kerneis
# Copyright(C) 2010-2011 Jocelyn Jaubert
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


from weboob.capabilities.bank import ICapBank, AccountNotFound
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import ValueBackendPassword, ValueBool, Value

from .browser import Boursorama


__all__ = ['BoursoramaBackend']


class BoursoramaBackend(BaseBackend, ICapBank):
    NAME = 'boursorama'
    MAINTAINER = u'Gabriel Kerneis'
    EMAIL = 'gabriel@kerneis.info'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = u'Boursorama'
    CONFIG = BackendConfig(ValueBackendPassword('login',      label='Identifiant', masked=False),
                           ValueBackendPassword('password',   label='Mot de passe'),
                           ValueBool('enable_twofactors',     label='Send validation sms', default=False),
                           Value('device',                    label='Device name', regexp='\w*', default=''),
                          )
    BROWSER = Boursorama

    def create_default_browser(self):
        return self.create_browser(
            self.config["device"].get()
            , self.config["enable_twofactors"].get()
            , self.config['login'].get()
            , self.config['password'].get())

    def iter_accounts(self):
        for account in self.browser.get_accounts_list():
            yield account

    def get_account(self, _id):
        if not _id.isdigit():
            raise AccountNotFound()
        with self.browser:
            account = self.browser.get_account(_id)
        if account:
            return account
        else:
            raise AccountNotFound()

    def iter_history(self, account):
        with self.browser:
            for history in self.browser.get_history(account):
                yield history

    # TODO
    #def iter_coming(self, account):
    #    with self.browser:
    #        for coming in self.browser.get_coming_operations(account):
    #            yield coming
