# -*- coding: utf-8 -*-

# Copyright(C) 2013 Mathieu Jourdan
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

from weboob.capabilities.bill import ICapBill, SubscriptionNotFound,\
    BillNotFound, Subscription, Bill
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import ValueBackendPassword
from .browser import GdfSuez

__all__ = ['GdfSuezBackend']


class GdfSuezBackend(BaseBackend, ICapBill):
    NAME = 'gdfsuez'
    MAINTAINER = u'Mathieu Jourdan'
    EMAIL = 'mathieu.jourdan@gresille.org'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = u'GDF-Suez French energy provider'
    CONFIG = BackendConfig(ValueBackendPassword('login',
                                                label='Account ID (e-mail)',
                                                masked=False),
                           ValueBackendPassword('password',
                                                label='Password',
                                                masked=True)
                           )
    BROWSER = GdfSuez

    def create_default_browser(self):
        return self.create_browser(self.config['login'].get(),
                                   self.config['password'].get())

    def iter_subscription(self):
        for subscription in self.browser.get_subscription_list():
            yield subscription

    def get_subscription(self, _id):
        if not _id.isdigit():
            raise SubscriptionNotFound()
        with self.browser:
            subscription = self.browser.get_subscription(_id)
        if not subscription:
            raise SubscriptionNotFound()
        else:
            return subscription

    def iter_bills_history(self, subscription):
        if not isinstance(subscription, Subscription):
            subscription = self.get_subscription(subscription)
        with self.browser:
            for history in self.browser.get_history(subscription):
                yield history

    def get_details(self, subscription):
        if not isinstance(subscription, Subscription):
            subscription = self.get_subscription(subscription)
        with self.browser:
            for detail in self.browser.get_details(subscription):
                yield detail

    def iter_bills(self, subscription):
        if not isinstance(subscription, Subscription):
            subscription = self.get_subscription(subscription)
        with self.browser:
            for bill in self.browser.iter_bills():
                yield bill

    def get_bill(self, id):
        with self.browser:
            bill = self.browser.get_bill(id)
        if not bill:
            raise BillNotFound()
        else:
            return bill

    def download_bill(self, bill):
        if not isinstance(bill, Bill):
            bill = self.get_bill(bill)
        with self.browser:
            return self.browser.readurl(bill._url)
