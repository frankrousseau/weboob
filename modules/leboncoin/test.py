# -*- coding: utf-8 -*-

# Copyright(C) 2014      Bezleputh
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

import itertools
from weboob.tools.test import BackendTest
from weboob.capabilities.housing import Query


class LeboncoinTest(BackendTest):
    MODULE = 'leboncoin'

    def test_leboncoin(self):
        query = Query()
        query.cities = []
        for city in self.backend.search_city('lille'):
            city.backend = self.backend.name
            query.cities.append(city)

        results = list(itertools.islice(self.backend.search_housings(query), 0, 20))
        self.assertTrue(len(results) > 0)

        obj = self.backend.fillobj(results[0])
        self.assertTrue(obj.area is not None, 'Area for "%s"' % (obj.id))
