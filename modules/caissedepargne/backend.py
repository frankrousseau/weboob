# -*- coding: utf-8 -*-

# Copyright(C) 2012-2013 Romain Bignon
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
from weboob.tools.value import Value, ValueBackendPassword

from .browser import CaisseEpargne


__all__ = ['CaisseEpargneBackend']


class CaisseEpargneBackend(BaseBackend, ICapBank):
    NAME = 'caissedepargne'
    MAINTAINER = u'Romain Bignon'
    EMAIL = 'romain@weboob.org'
    VERSION = '0.j'
    DESCRIPTION = u'Caisse d\'Épargne'
    LICENSE = 'AGPLv3+'
    CONFIG = BackendConfig(ValueBackendPassword('login',    label='Identifiant client', masked=False),
                           ValueBackendPassword('password', label='Code personnel', regexp='\d+'),
                           Value('nuser', label='User ID (optional)', default=''))
    BROWSER = CaisseEpargne

    def create_default_browser(self):
        return self.create_browser(self.config['nuser'].get(),
                                   self.config['login'].get(),
                                   self.config['password'].get())

    def iter_accounts(self):
        with self.browser:
            return self.browser.get_accounts_list()

    def get_account(self, _id):
        with self.browser:
            account = self.browser.get_account(_id)

        if account:
            return account
        else:
            raise AccountNotFound()

    def iter_history(self, account):
        with self.browser:
            return self.browser.get_history(account)

    def iter_coming(self, account):
        with self.browser:
            return self.browser.get_coming(account)
