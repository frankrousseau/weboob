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


import re
from collections import defaultdict

from weboob.deprecated.browser import Browser, BrowserIncorrectPassword
from weboob.capabilities.bank import Account

from .pages import (LoginPage, AccountsList, AccountHistory, CardHistory, UpdateInfoPage,
                    AuthenticationPage, AccountInvestment, InvestmentDetail)


__all__ = ['Boursorama']


class BrowserIncorrectAuthenticationCode(BrowserIncorrectPassword):
    pass


class Boursorama(Browser):
    DOMAIN = 'www.boursorama.com'
    PROTOCOL = 'https'
    CERTHASH = ['6bdf8b6dd177bd417ddcb1cfb818ede153288e44115eb269f2ddd458c8461039',
                'b290ef629c88f0508e9cc6305421c173bd4291175e3ddedbee05ee666b34c20e']
    ENCODING = None  # refer to the HTML encoding
    PAGES = {
             '.*/connexion/securisation/index.phtml': AuthenticationPage,
             '.*connexion.phtml.*': LoginPage,
             '.*/comptes/synthese.phtml': AccountsList,
             '.*/comptes/banque/detail/mouvements.phtml.*': AccountHistory,
             '.*/comptes/banque/cartes/mouvements.phtml.*': CardHistory,
             '.*/comptes/epargne/mouvements.phtml.*': AccountHistory,
             '.*/date_anniversaire.phtml.*':    UpdateInfoPage,
             '.*/detail.phtml.*': AccountInvestment,
             '.*/opcvm.phtml.*': InvestmentDetail
            }

    def __init__(self, device="weboob", enable_twofactors=False,
                 *args, **kwargs):
        self.device = device
        self.enable_twofactors = enable_twofactors
        Browser.__init__(self, *args, **kwargs)

    def home(self):
        if not self.is_logged():
            self.login()
        else:
            self.location('https://' + self.DOMAIN + '/comptes/synthese.phtml')

    def is_logged(self):
        return self.page is not None and not self.is_on_page(LoginPage)

    def handle_authentication(self):
        if self.is_on_page(AuthenticationPage):
            if self.enable_twofactors:
                self.page.authenticate(self.device)
            else:
                raise BrowserIncorrectAuthenticationCode(
                    """Boursorama - activate the two factor authentication in boursorama config."""
                    """ You will receive SMS code but are limited in request per day (around 15)"""
                )


    def login(self):
        assert isinstance(self.device, basestring)
        assert isinstance(self.enable_twofactors, bool)
        assert self.password.isdigit()

        if not self.is_on_page(LoginPage):
            self.location('https://' + self.DOMAIN + '/connexion.phtml', no_login=True)

        self.page.login(self.username, self.password)

        if self.is_on_page(LoginPage):
            raise BrowserIncorrectPassword()

        #after login, we might be redirected to the two factor
        #authentication page
        #print "handle authentication"
        self.handle_authentication()

        self.location('/comptes/synthese.phtml', no_login=True)

        #if the login was correct but authentication code failed,
        #we need to verify if bourso redirect us to login page or authentication page
        if self.is_on_page(LoginPage):
            raise BrowserIncorrectAuthenticationCode()

    def get_accounts_list(self):
        if not self.is_on_page(AccountsList):
            self.location('/comptes/synthese.phtml')

        return self.page.get_list()

    def get_account(self, id):
        assert isinstance(id, basestring)

        if not self.is_on_page(AccountsList):
            self.location('/comptes/synthese.phtml')

        l = self.page.get_list()
        for a in l:
            if a.id == id:
                return a

        return None

    def get_history(self, account):
        link = account._link_id
        #We need to skip the first link on card page because there is a summary,
        #and so the recent transaction are displayed twice
        if account.type == Account.TYPE_CARD:
            self.location(link)
            link = self.page.get_next_url()

        while link is not None:
            self.location(link)
            if not self.is_on_page(AccountHistory) and not self.is_on_page(CardHistory):
                raise NotImplementedError()

            for tr in self.page.get_operations():
                yield tr

            link = self.page.get_next_url()

    def get_investment(self, account):
        if account.type != Account.TYPE_MARKET or not account._detail_url:
            raise NotImplementedError()
        self.location(account._detail_url)

        seen = defaultdict(int)
        def slugify(label):
            label = label.upper().replace('FONDS EN EUROS (', '')[:12]
            slug = re.sub(r'[^A-Za-z0-9]', ' ', label).strip()
            slug = re.sub(r'\s+', '-', slug)
            if label in seen:
                counter = str(seen[slug])
                slug = slug[:-len(counter)] + counter
            seen[label] += 1
            return slug

        for inv in self.page.get_investment():
            if inv._detail_url:
                self.location(inv._detail_url)
                self.page.get_investment_detail(inv)
            if not inv.id:
                inv.id = inv.code = 'XX' + slugify(inv.label)
            yield inv

    def transfer(self, from_id, to_id, amount, reason=None):
        raise NotImplementedError()
