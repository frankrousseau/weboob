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
from weboob.tools.value import ValueBackendPassword, Value

from .browser import HSBC


__all__ = ['HSBCBackend']


class HSBCBackend(BaseBackend, ICapBank):
    NAME = 'hsbc'
    MAINTAINER = u'Romain Bignon'
    EMAIL = 'romain@weboob.org'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = 'HSBC France'
    CONFIG = BackendConfig(ValueBackendPassword('login',      label='Identifiant', masked=False),
                           ValueBackendPassword('password',   label='Mot de passe'),
                           Value(               'secret',     label=u'Réponse secrète (optionnel)', default=''))
    BROWSER = HSBC

    def create_default_browser(self):
        return self.create_browser(self.config['login'].get(),
                                   self.config['password'].get(),
                                   self.config['secret'].get())

    def iter_accounts(self):
        for account in self.browser.get_accounts_list():
            yield account

    def get_account(self, _id):
        with self.browser:
            account = self.browser.get_account(_id)
        if account:
            return account
        else:
            raise AccountNotFound()

    def iter_history(self, account):
        with self.browser:
            for tr in self.browser.get_history(account):
                # If there are deferred cards, strip CB invoices.
                if not tr._coming and (not tr.raw.startswith('FACTURES CB') or len(account._card_links) == 0):
                    yield tr

    def iter_coming(self, account):
        with self.browser:
            for tr in self.browser.get_history(account):
                if tr._coming:
                    yield tr
