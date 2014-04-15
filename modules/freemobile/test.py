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


from weboob.tools.test import BackendTest


__all__ = ['FreeMobileTest']


class FreeMobileTest(BackendTest):
    BACKEND = 'freemobile'

    def test_details(self):
        for subscription in self.backend.iter_subscription():
            details = list(self.backend.get_details(subscription))
            self.assertTrue(len(details) > 4, msg="Not enough details")

    def test_history(self):
        for subscription in self.backend.iter_subscription():
            self.assertTrue(len(list(self.backend.iter_bills_history(subscription))) > 0)

    def test_downloadbills(self):
        """
        Iter all bills and try to download it.
        """
        for subscription in self.backend.iter_subscription():
            for bill in self.backend.iter_bills(subscription.id):
                self.backend.download_bill(bill.id)

    def test_list(self):
        """
        Test listing of subscriptions.
        """
        subscriptions = list(self.backend.iter_subscription())
        self.assertTrue(len(subscriptions) > 0, msg="Account listing failed")
