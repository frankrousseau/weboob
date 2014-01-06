# -*- coding: utf-8 -*-

# Copyright(C) 2009-2012  Romain Bignon
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
import datetime
import re

from weboob.capabilities.bank import Transaction
from weboob.capabilities import NotAvailable
from weboob.tools.misc import to_unicode
from weboob.tools.log import getLogger


__all__ = ['FrenchTransaction']


class FrenchTransaction(Transaction):
    """
    Transaction with some helpers for french bank websites.
    """
    PATTERNS = []

    def __init__(self, *args, **kwargs):
        Transaction.__init__(self, *args, **kwargs)
        self._logger = getLogger('FrenchTransaction')

    @classmethod
    def clean_amount(klass, text):
        """
        Clean a string containing an amount.
        """
        text = text.replace('.','').replace(',','.')
        return re.sub(u'[^\d\-\.]', '', text)

    def set_amount(self, credit='', debit=''):
        """
        Set an amount value from a string.

        Can take two strings if there are both credit and debit
        columns.
        """
        credit = self.clean_amount(credit)
        debit = self.clean_amount(debit)

        if len(debit) > 0:
            self.amount = - abs(Decimal(debit))
        elif len(credit) > 0:
            self.amount = Decimal(credit)
        else:
            self.amount = Decimal('0')

    def parse_date(self, date):
        if date is None:
            return NotAvailable

        if not isinstance(date, (datetime.date, datetime.datetime)):
            if date.isdigit() and len(date) == 8:
                date = datetime.date(int(date[4:8]), int(date[2:4]), int(date[0:2]))
            elif '/' in date:
                date = datetime.date(*reversed(map(int, date.split('/'))))
        if not isinstance(date, (datetime.date, datetime.datetime)):
            self._logger.warning('Unable to parse date %r' % date)
            date = NotAvailable
        elif date.year < 100:
            date = date.replace(year=2000 + date.year)

        return date

    def parse(self, date, raw, vdate=None):
        """
        Parse date and raw strings to create datetime.date objects,
        determine the type of transaction, and create a simplified label

        When calling this method, you should have defined patterns (in the
        PATTERN class attribute) with a list containing tuples of regexp
        and the associated type, for example::

            PATTERNS = [(re.compile('^VIR(EMENT)? (?P<text>.*)'), FrenchTransaction.TYPE_TRANSFER),
                        (re.compile('^PRLV (?P<text>.*)'),        FrenchTransaction.TYPE_ORDER),
                        (re.compile('^(?P<text>.*) CARTE \d+ PAIEMENT CB (?P<dd>\d{2})(?P<mm>\d{2}) ?(.*)$'),
                                                                  FrenchTransaction.TYPE_CARD)
                       ]

        In regexps, you can define this patterns:

            * text: part of label to store in simplified label
            * category: part of label representing the category
            * yy, mm, dd, HH, MM: date and time parts
        """
        self.date = self.parse_date(date)
        self.vdate = self.parse_date(vdate)
        self.rdate = self.date
        self.raw = to_unicode(raw.replace(u'\n', u' ').strip())
        self.category = NotAvailable

        if '  ' in self.raw:
            self.category, useless, self.label = [part.strip() for part in self.raw.partition('  ')]
        else:
            self.label = self.raw

        for pattern, _type in self.PATTERNS:
            m = pattern.match(self.raw)
            if m:
                args = m.groupdict()

                def inargs(key):
                    """
                    inner function to check if a key is in args,
                    and is not None.
                    """
                    return args.get(key, None) is not None

                self.type = _type
                if inargs('text'):
                    self.label = args['text'].strip()
                if inargs('category'):
                    self.category = args['category'].strip()

                # Set date from information in raw label.
                if inargs('dd') and inargs('mm'):
                    dd = int(args['dd'])
                    mm = int(args['mm'])

                    if inargs('yy'):
                        yy = int(args['yy'])
                    else:
                        d = self.date
                        try:
                            d = d.replace(month=mm, day=dd)
                        except ValueError:
                            d = d.replace(year=d.year-1, month=mm, day=dd)

                        yy = d.year
                        if d > self.date:
                            yy -= 1

                    if yy < 100:
                        yy += 2000

                    try:
                        if inargs('HH') and inargs('MM'):
                            self.rdate = datetime.datetime(yy, mm, dd, int(args['HH']), int(args['MM']))
                        else:
                            self.rdate = datetime.date(yy, mm, dd)
                    except ValueError as e:
                        self._logger.warning('Unable to date in label %r: %s' % (self.raw, e))

                return
