# -*- coding: utf-8 -*-

# Copyright(C) 2014      Alexandre Morignot
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
from weboob.capabilities.calendar import Query

from datetime import datetime, timedelta


class ResidentadvisorTest(BackendTest):
    MODULE = 'residentadvisor'

    def test_searchcity(self):
        query = Query()
        query.city = u'Melbourne'

        self.assertTrue(len(list(self.backend.search_events(query))) > 0)

        event = self.backend.search_events(query).next()
        self.assertTrue(self.backend.get_event(event.id))

    def test_datefrom(self):
        query = Query()
        later = (datetime.now() + timedelta(days=31))
        query.start_date = later

        event = self.backend.search_events(query).next()
        self.assertTrue(later.date() <= event.start_date.date())

        event = self.backend.get_event(event.id)
        self.assertTrue(later.date() <= event.start_date.date())
