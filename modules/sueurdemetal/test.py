# -*- coding: utf-8 -*-

# Copyright(C) 2013      Vincent A
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
from weboob.capabilities.calendar import Query, CATEGORIES
from datetime import datetime, timedelta


class SueurDeMetalTest(BackendTest):
    MODULE = 'sueurdemetal'

    def test_sueurdemetal_searchcity(self):
        q = Query()
        q.city = u'paris'
        self.assertTrue(len(list(self.backend.search_events(q))) > 0)

        ev = self.backend.search_events(q).next()
        self.assertTrue(self.backend.get_event(ev.id))

    def test_sueurdemetal_datefrom(self):
        q = Query()
        later = (datetime.now() + timedelta(days=31))
        q.start_date = later

        ev = self.backend.search_events(q).next()
        self.assertTrue(later.date() <= ev.start_date.date())

    def test_sueurdemetal_nocategory(self):
        q = Query()
        q.categories = [CATEGORIES.CINE]
        self.assertTrue(len(list(self.backend.search_events(q))) == 0)
