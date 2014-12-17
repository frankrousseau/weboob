# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
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


from mechanize import FormNotFoundError
from weboob.deprecated.mech import ClientForm
ControlNotFoundError = ClientForm.ControlNotFoundError

from decimal import Decimal, InvalidOperation
import re

from weboob.deprecated.browser import Page
from weboob.tools.misc import to_unicode
from weboob.tools.ordereddict import OrderedDict
from weboob.capabilities.bank import Account
from weboob.tools.capabilities.bank.transactions import FrenchTransaction


class LoginPage(Page):
    def login(self, login, passwd):
        try:
            length = int(self.document.xpath('//input[@id="pass"]')[0].attrib['maxlength'])
        except (IndexError,KeyError):
            pass
        else:
            passwd = passwd[:length]

        self.browser.select_form(name='authen')
        try:
            self.browser['id'] = login.encode(self.browser.ENCODING)
            self.browser['pass'] = passwd.encode(self.browser.ENCODING)
        except ControlNotFoundError:
            self.browser.controls.append(ClientForm.TextControl('text', 'id', {'value': login.encode(self.browser.ENCODING)}))
            self.browser.controls.append(ClientForm.TextControl('text', 'pass', {'value': passwd.encode(self.browser.ENCODING)}))

        self.browser.submit(nologin=True)


class LoginResultPage(Page):
    def on_loaded(self):
        for script in self.document.xpath('//script'):
            text = script.text
            if text is None:
                continue
            m = re.search("window.location.replace\('([^']+)'\);", text)
            if m:
                self.browser.location(m.group(1))

        try:
            self.browser.select_form(name='banque')
        except FormNotFoundError:
            pass
        else:
            self.browser.set_all_readonly(False)
            accounts = OrderedDict()
            for tr in self.document.getroot().cssselect('table.compteTable > tbody > tr'):
                if len(tr.findall('td')) == 0:
                    continue
                attr = tr.xpath('.//a')[0].attrib.get('onclick', '')
                m = re.search("value = '(\w+)';(checkAndSubmit\('\w+','(\w+)','(\w+)'\))?", attr)
                if m:
                    typeCompte = m.group(1)
                    tagName = m.group(3)
                    if tagName is not None:
                        value = self.document.xpath('//input[@name="%s"]' % m.group(3))[int(m.group(4))].attrib['value']
                    else:
                        value = typeCompte
                    accounts[value] = (typeCompte, tagName)

            try:
                typeCompte, tagName = accounts[self.browser.accnum]
                value = self.browser.accnum
            except KeyError:
                accnums = ', '.join(accounts.keys())
                if self.browser.accnum != '00000000000':
                    self.logger.warning(u'Unable to find account "%s". Available ones: %s' % (self.browser.accnum, accnums))
                elif len(accounts) > 1:
                    self.logger.warning('There are several accounts, please use "accnum" backend parameter to force the one to use (%s)' % accnums)
                value, (typeCompte, tagName) = accounts.popitem(last=False)
            self.browser['typeCompte'] = typeCompte
            if tagName is not None:
                self.browser[tagName] = [value]
            self.browser.submit()

    def confirm(self):
        self.browser.location('MainAuth?typeDemande=AC', no_login=True)

    def get_error(self):
        error = self.document.xpath('//td[@class="txt_norm2"]')
        if len(error) == 0:
            return None

        error = error[0]
        if error.find('b') is not None:
            error = error.find('b')

        return error.text.strip()


class EmptyPage(Page):
    pass


class BredBasePage(Page):
    def js2args(self, s):
        cur_arg = None
        args = {}
        # For example:
        # javascript:reloadApplication('nom_application', 'compte_telechargement', 'numero_poste', '000', 'numero_compte', '12345678901','monnaie','EUR');
        for sub in re.findall("'([^']+)'", s):
            if cur_arg is None:
                cur_arg = sub
            else:
                args[cur_arg] = sub
                cur_arg = None

        return args


class AccountsPage(BredBasePage):
    def get_list(self):
        for tr in self.document.xpath('//table[@class="compteTable"]/tr'):
            if not tr.attrib.get('class', '').startswith('ligne_'):
                continue

            cols = tr.findall('td')

            if len(cols) < 2:
                continue

            try:
                amount = sum([Decimal(FrenchTransaction.clean_amount(txt)) for txt in cols[-1].itertext() if len(txt.strip()) > 0])
            except InvalidOperation:
                continue

            a = cols[0].find('a')
            if a is None:
                for a in cols[0].xpath('.//li/a'):
                    args = self.js2args(a.attrib['href'])
                    if 'numero_compte' not in args or 'numero_poste' not in args:
                        self.logger.warning('Card link with strange args: %s' % args)
                        continue

                    account = Account()
                    account.id = '%s.%s' % (args['numero_compte'], args['numero_poste'])
                    account.label = u'Carte %s' % self.parser.tocleanstring(a)
                    account.balance = amount
                    account.type = account.TYPE_CARD
                    account.currency = [account.get_currency(txt) for txt in cols[-1].itertext() if len(txt.strip()) > 0][0]
                    yield account
                continue

            args = self.js2args(a.attrib['href'])

            if 'numero_compte' not in args or 'numero_poste' not in args:
                self.logger.warning('Account link for %r with strange args: %s' % (a.attrib.get('alt', a.text), args))
                continue

            account = Account()
            account.id = u'%s.%s' % (args['numero_compte'], args['numero_poste'])
            account.label = to_unicode(a.attrib.get('alt', a.text.strip()))
            account.balance = amount
            account.currency = [account.get_currency(txt) for txt in cols[-1].itertext() if len(txt.strip()) > 0][0]
            yield account


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^RETRAIT G.A.B. \d+ (?P<text>.*?)( CARTE .*)? LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2}).*'),
                                                            FrenchTransaction.TYPE_WITHDRAWAL),
                (re.compile('^VIR(EMENT)? (?P<text>.*)'),   FrenchTransaction.TYPE_TRANSFER),
                (re.compile('^PRLV (?P<text>.*)'),          FrenchTransaction.TYPE_ORDER),
                (re.compile('^(?P<text>.*) TRANSACTION( CARTE .*)? LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2}) ?(.*)$'),
                                                            FrenchTransaction.TYPE_CARD),
                (re.compile('^CHEQUE.*'),                   FrenchTransaction.TYPE_CHECK),
                (re.compile('^(CONVENTION \d+ )?COTISATION (?P<text>.*)'),
                                                            FrenchTransaction.TYPE_BANK),
                (re.compile('^REMISE (?P<text>.*)'),        FrenchTransaction.TYPE_DEPOSIT),
                (re.compile('^(?P<text>.*)( \d+)? QUITTANCE .*'),
                                                            FrenchTransaction.TYPE_ORDER),
                (re.compile('^CB PAIEM. EN \d+ FOIS \d+ (?P<text>.*?) LE .* LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2})$'),
                                                            FrenchTransaction.TYPE_CARD),
                (re.compile('^.* LE (?P<dd>\d{2})/(?P<mm>\d{2})/(?P<yy>\d{2})$'),
                                                            FrenchTransaction.TYPE_UNKNOWN),
               ]


class TransactionsPage(Page):
    def get_history(self):
        for tr in self.document.xpath('//div[@class="scrollTbody"]/table//tr'):
            cols = tr.findall('td')

            if len(cols) < 4:
                continue

            col_label = cols[1]
            if col_label.find('a') is not None:
                col_label = col_label.find('a')

            date = self.parser.tocleanstring(cols[0])
            label = self.parser.tocleanstring(col_label)

            t = Transaction(col_label.attrib.get('id', ''))

            # an optional tooltip on page contain the second part of the transaction label.
            tooltip = self.document.xpath('//div[@id="tooltip%s"]' % t.id)
            raw = label
            if len(tooltip) > 0:
                raw += u' ' + u' '.join([txt.strip() for txt in tooltip[0].itertext()])

            raw = re.sub(r'[ ]+', ' ', raw)

            t.parse(date, raw)

            # as only the first part of label is important to user, if there are no subpart
            # taken by FrenchTransaction regexps, reset the label as first part.
            if t.label == t.raw:
                t.label = label

            debit = self.parser.tocleanstring(cols[-2])
            credit = self.parser.tocleanstring(cols[-1])
            t.set_amount(credit, debit)

            yield t
