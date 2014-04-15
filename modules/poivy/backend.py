# -*- coding: utf-8 -*-

# Copyright(C) 2013-2014 Florent Fourcot
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


from weboob.capabilities.bill import ICapBill, Subscription, SubscriptionNotFound, Detail
from weboob.capabilities.base import find_object
from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import ValueBackendPassword

from .browser import PoivyBrowser


__all__ = ['PoivyBackend']


class PoivyBackend(BaseBackend, ICapBill):
    NAME = 'poivy'
    MAINTAINER = u'Florent Fourcot'
    EMAIL = 'weboob@flo.fourcot.fr'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = 'Poivy website'
    CONFIG = BackendConfig(ValueBackendPassword('login',
                                                label='login',
                                                masked=False),
                           ValueBackendPassword('password',
                                                label='Password')
                           )
    BROWSER = PoivyBrowser

    def create_default_browser(self):
        return self.create_browser(self.config['login'].get(),
                                   self.config['password'].get())

    def iter_subscription(self):
        return self.browser.get_subscription_list()

    def get_subscription(self, _id):
        return find_object(self.iter_subscription(), id=_id, error=SubscriptionNotFound)

    def iter_bills_history(self, subscription):
        # Try if we have a real subscription before to load the history
        if not isinstance(subscription, Subscription):
            subscription = self.get_subscription(subscription)
        return self.browser.get_history()

    # No details on the website
    def get_details(self, subscription):
        raise NotImplementedError()

    def get_balance(self, subscription):
        if not isinstance(subscription, Subscription):
            subscription = self.get_subscription(subscription)
        balance = Detail()
        balance.id = "%s-balance" % subscription.id
        balance.price = subscription._balance
        balance.label = u"Balance %s" % subscription.id
        balance.currency = u'EUR'
        return balance
