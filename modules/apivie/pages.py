# -*- coding: utf-8 -*-

# Copyright(C) 2013      Romain Bignon
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


from decimal import Decimal

from weboob.capabilities.bank import Account
from weboob.deprecated.browser import Page
from weboob.tools.capabilities.bank.transactions import FrenchTransaction


class LoginPage(Page):
    def login(self, username, password):
        self.browser.select_form(nr=0)
        self.browser['_58_login'] = username.encode('utf-8')
        self.browser['_58_password'] = password.encode('utf-8')
        self.browser.submit(nologin=True)


class AccountsPage(Page):
    COL_LABEL = 0
    COL_OWNER = 1
    COL_ID = 2
    COL_AMOUNT = 3

    def iter_accounts(self):
        for line in self.document.xpath('//table[@summary="informations contrat"]/tbody/tr'):
            yield self._get_account(line)

    def _get_account(self, line):
        tds = line.findall('td')
        account = Account()
        account.id = self.parser.tocleanstring(tds[self.COL_ID])
        account.label = self.parser.tocleanstring(tds[self.COL_LABEL])

        balance_str = self.parser.tocleanstring(tds[self.COL_AMOUNT])
        account.balance = Decimal(FrenchTransaction.clean_amount(balance_str))
        account.currency = account.get_currency(balance_str)
        return account


class Transaction(FrenchTransaction):
    pass


class OperationsPage(Page):
    COL_DATE = 0
    COL_LABEL = 1
    COL_AMOUNT = 2

    def iter_history(self):
        for line in self.document.xpath('//table[@role="treegrid"]/tbody/tr'):
            tds = line.findall('td')

            operation = Transaction(int(line.attrib['data-rk']))

            date = self.parser.tocleanstring(tds[self.COL_DATE])
            label = self.parser.tocleanstring(tds[self.COL_LABEL])
            amount = self.parser.tocleanstring(tds[self.COL_AMOUNT])

            if len(amount) == 0:
                continue

            color = tds[self.COL_AMOUNT].find('span').attrib['class']
            if color == 'black':
                continue

            operation.parse(date, label)
            operation.set_amount(amount)

            if color == 'red' and operation.amount > 0:
                operation.amount = - operation.amount

            yield operation
