# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Julien Veyssier
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


try:
    from urlparse import urlsplit, parse_qsl, urlparse
except ImportError:
    from urllib.parse import urlsplit, parse_qsl, urlparse

from datetime import datetime, timedelta

from weboob.tools.compat import basestring
from weboob.browser.browsers import LoginBrowser, need_login
from weboob.browser.profiles import Wget
from weboob.browser.url import URL
from weboob.exceptions import BrowserIncorrectPassword
from weboob.capabilities.bank import Transfer, TransferError

from .pages import LoginPage, LoginErrorPage, AccountsPage, UserSpacePage, \
                   OperationsPage, CardPage, ComingPage, NoOperationsPage, \
                   TransfertPage, ChangePasswordPage, VerifCodePage, EmptyPage


__all__ = ['CreditMutuelBrowser']


class CreditMutuelBrowser(LoginBrowser):
    PROFILE = Wget()
    BASEURL = 'https://www.creditmutuel.fr'

    login =       URL('/groupe/fr/index.html',                               LoginPage)
    login_error = URL('/(?P<subbank>.*)/fr/identification/default.cgi',      LoginErrorPage)
    accounts =    URL('/(?P<subbank>.*)/fr/banque/situation_financiere.cgi', AccountsPage)
    user_space =  URL('/(?P<subbank>.*)/fr/banque/espace_personnel.aspx',    UserSpacePage)
    operations =  URL('/(?P<subbank>.*)/fr/banque/mouvements.cgi.*',
                      '/(?P<subbank>.*)/fr/banque/nr/nr_devbooster.aspx.*',
                      OperationsPage)
    coming =      URL('/(?P<subbank>.*)/fr/banque/mvts_instance.cgi.*',      ComingPage)
    card =        URL('/(?P<subbank>.*)/fr/banque/operations_carte.cgi.*',   CardPage)
    noop =        URL('/(?P<subbank>.*)/fr/banque/CR/arrivee.asp.*',         NoOperationsPage)
    info =        URL('/(?P<subbank>.*)/fr/banque/BAD.*',                    EmptyPage)
    transfert =   URL('/(?P<subbank>.*)/fr/banque/WI_VPLV_VirUniSaiCpt.asp\?(?P<parameters>.*)', TransfertPage)
    change_pass = URL('/(?P<subbank>.*)/fr/validation/change_password.cgi',  ChangePasswordPage)
    verify_pass = URL('/(?P<subbank>.*)/fr/validation/verif_code.cgi.*',     VerifCodePage)
    empty =       URL('/(?P<subbank>.*)/fr/$',
                      '/(?P<subbank>.*)/fr/banques/index.html',
                      '/(?P<subbank>.*)/fr/banque/paci_beware_of_phishing.*',
                      '/(?P<subbank>.*)/fr/validation/(?!change_password|verif_code).*',
                      EmptyPage)

    currentSubBank = None

    def do_login(self):
        self.login.stay_or_go()

        self.page.login(self.username, self.password)

        if not self.page.logged or self.login_error.is_here():
            raise BrowserIncorrectPassword()

        self.getCurrentSubBank()

    @need_login
    def get_accounts_list(self):
        return self.accounts.stay_or_go(subbank=self.currentSubBank).iter_accounts()

    def get_account(self, id):
        assert isinstance(id, basestring)

        for a in self.get_accounts_list():
            if a.id == id:
                return a

    def getCurrentSubBank(self):
        # the account list and history urls depend on the sub bank of the user
        url = urlparse(self.url)
        self.currentSubBank = url.path.lstrip('/').split('/')[0]

    def list_operations(self, page_url):
        if page_url.startswith('/'):
            self.location(page_url)
        else:
            self.location('%s/%s/fr/banque/%s' % (self.BASEURL, self.currentSubBank, page_url))

        if not self.operations.is_here():
            return iter([])

        return self.pagination(lambda: self.page.get_history())

    def get_history(self, account):
        transactions = []
        last_debit = None
        for tr in self.list_operations(account._link_id):
            # to prevent redundancy with card transactions, we do not
            # store 'RELEVE CARTE' transaction.
            if tr.raw != 'RELEVE CARTE':
                transactions.append(tr)
            elif last_debit is None:
                last_debit = (tr.date - timedelta(days=10)).month

        coming_link = self.page.get_coming_link() if self.operations.is_here() else None
        if coming_link is not None:
            for tr in self.list_operations(coming_link):
                transactions.append(tr)

        month = 0
        for card_link in account._card_links:
            v = urlsplit(card_link)
            args = dict(parse_qsl(v.query))
            # useful with 12 -> 1
            if int(args['mois']) < month:
                month = month + 1
            else:
                month = int(args['mois'])

            for tr in self.list_operations(card_link):
                if month > last_debit:
                    tr._is_coming = True
                transactions.append(tr)

        transactions.sort(key=lambda tr: tr.rdate, reverse=True)
        return transactions

    def transfer(self, account, to, amount, reason=None):
        # access the transfer page
        parameters = 'RAZ=ALL&Cat=6&PERM=N&CHX=A'
        page = self.transfert.go(subbank=self.currentSubBank, parameters=parameters)

        # fill the form
        form = self.page.get_form(name='FormVirUniSaiCpt')
        form['IDB'] = account[-1]
        form['ICR'] = to[-1]
        form['MTTVIR'] = '%s' % str(amount).replace('.', ',')
        if reason is not None:
            form['LIBDBT'] = reason
            form['LIBCRT'] = reason
        page = form.submit()

        # look for known errors
        content = page.response.text
        insufficient_amount_message     = u'Montant insuffisant.'
        maximum_allowed_balance_message = u'Solde maximum autorisé dépassé.'

        if insufficient_amount_message in content:
            raise TransferError('The amount you tried to transfer is too low.')

        if maximum_allowed_balance_message in content:
            raise TransferError('The maximum allowed balance for the target account has been / would be reached.')

        # look for the known "all right" message
        ready_for_transfer_message = u'Confirmez un virement entre vos comptes'
        if ready_for_transfer_message in content:
            raise TransferError('The expected message "%s" was not found.' % ready_for_transfer_message)

        # submit the confirmation form
        form = page.get_form(name='FormVirUniCnf')
        submit_date = datetime.now()
        page = form.submit()

        # look for the known "everything went well" message
        content = page.response.text
        transfer_ok_message = u'Votre virement a été exécuté ce jour'
        if transfer_ok_message not in content:
            raise TransferError('The expected message "%s" was not found.' % transfer_ok_message)

        # We now have to return a Transfer object
        transfer = Transfer(submit_date.strftime('%Y%m%d%H%M%S'))
        transfer.amount = amount
        transfer.origin = account
        transfer.recipient = to
        transfer.date = submit_date
        return transfer
