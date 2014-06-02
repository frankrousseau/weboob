# -*- coding: utf-8 -*-

# Copyright(C) 2013-2014      Romain Bignon
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


from weboob.tools.browser2 import LoginBrowser, need_login, URL
from weboob.tools.exceptions import BrowserIncorrectPassword

from .pages import LoginPage, IndexPage, AccountsPage, OperationsPage


__all__ = ['BanqueAccordBrowser']


class BanqueAccordBrowser(LoginBrowser):
    BASEURL = 'https://www.banque-accord.fr/site/s/'
    TIMEOUT = 20.0

    login = URL('login/login.html', LoginPage)
    index = URL('detailcompte/detailcompte.html', IndexPage)
    accounts = URL('detailcompte/ongletdetailcompte.html', AccountsPage)
    operations = URL('detailcompte/ongletdernieresoperations.html', OperationsPage)

    def do_login(self):
        """
        Attempt to log in.
        Note: this method does nothing if we are already logged in.
        """
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)
        self.login.go()

        self.page.login(self.username, self.password)

        if not self.index.is_here():
            raise BrowserIncorrectPassword()

    @need_login
    def get_accounts_list(self):
        self.index.stay_or_go()

        for a in self.page.get_list():
            post = {'numeroCompte': a.id,}
            self.index.go(data=post)

            a.balance = self.page.get_loan_balance()
            if a.balance is not None:
                a.type = a.TYPE_LOAN
            else:
                self.accounts.go()
                a.balance = self.page.get_balance()
                a.type = a.TYPE_CARD
            if a.balance is None:
                continue
            yield a

    @need_login
    def iter_history(self, account):
        post = {'numeroCompte': account.id}

        self.index.go(data=post)

        if account.type == account.TYPE_LOAN:
            return self.page.iter_loan_transactions()

        self.operations.go()

        return sorted(self.page.iter_transactions(), key=lambda tr: tr.rdate, reverse=True)
