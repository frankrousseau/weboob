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

import urllib

from weboob.capabilities.housing import Query

from weboob.browser import PagesBrowser, URL
from .pages import SearchResultsPage, HousingPage, CitiesPage
from weboob.browser.profiles import Android

__all__ = ['SeLogerBrowser']


class SeLogerBrowser(PagesBrowser):
    BASEURL = 'http://www.seloger.com'
    PROFILE = Android()
    cities = URL('js,ajax,villequery_v3.htm\?ville=(?P<pattern>.*)', CitiesPage)
    search = URL('http://ws.seloger.com/search.xml\?(?P<request>.*)', SearchResultsPage)
    housing = URL('http://ws.seloger.com/annonceDetail.xml\?idAnnonce=(?P<_id>\d+)&noAudiotel=(?P<noAudiotel>\d)', HousingPage)

    def search_geo(self, pattern):
        return self.cities.open(pattern=pattern.encode('utf-8')).iter_cities()

    TYPES = {Query.TYPE_RENT: 1,
             Query.TYPE_SALE: 2
             }

    RET = {Query.HOUSE_TYPES.HOUSE: '2',
           Query.HOUSE_TYPES.APART: '1',
           Query.HOUSE_TYPES.LAND: '4',
           Query.HOUSE_TYPES.PARKING: '3',
           Query.HOUSE_TYPES.OTHER: '10'}

    def search_housings(self, type, cities, nb_rooms, area_min, area_max, cost_min, cost_max, house_types):
        data = {'ci':            ','.join(cities),
                'idtt':          self.TYPES.get(type, 1),
                'org':           'advanced_search',
                'surfacemax':    area_max or '',
                'surfacemin':    area_min or '',
                'tri':           'd_dt_crea',
                }

        if type == Query.TYPE_SALE:
            data['pxmax'] = cost_max or ''
            data['pxmin'] = cost_min or ''
        else:
            data['px_loyermax'] = cost_max or ''
            data['px_loyermin'] = cost_min or ''

        if nb_rooms:
            data['nb_pieces'] = nb_rooms

        ret = []
        for house_type in house_types:
            if house_type in self.RET:
                ret.append(self.RET.get(house_type))

        if ret:
            data['idtypebien'] = ','.join(ret)

        return self.search.go(request=urllib.urlencode(data)).iter_housings()

    def get_housing(self, _id, obj=None):
        return self.housing.go(_id=_id, noAudiotel=1).get_housing(obj=obj)
