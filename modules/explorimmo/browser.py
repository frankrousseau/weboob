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

import urllib
from weboob.browser import PagesBrowser, URL
from weboob.capabilities.housing import Query
from .pages import CitiesPage, SearchPage, HousingPage, HousingPage2, PhonePage


class ExplorimmoBrowser(PagesBrowser):
    BASEURL = 'http://www.explorimmo.com'

    cities = URL('rest/locations\?q=(?P<city>.*)', CitiesPage)
    search = URL('resultat/annonces.html\?(?P<query>.*)', SearchPage)
    housing_html = URL('annonce-(?P<_id>.*).html', HousingPage)
    phone = URL('rest/classifieds/(?P<_id>.*)/phone', PhonePage)
    housing = URL('rest/classifieds/(?P<_id>.*)',
                  'rest/classifieds/\?(?P<js_datas>.*)', HousingPage2)

    TYPES = {Query.TYPE_RENT: 'location',
             Query.TYPE_SALE: 'vente'}

    RET = {Query.HOUSE_TYPES.HOUSE: 'Maison',
           Query.HOUSE_TYPES.APART: 'Appartement',
           Query.HOUSE_TYPES.LAND: 'Terrain',
           Query.HOUSE_TYPES.PARKING: 'Parking',
           Query.HOUSE_TYPES.OTHER: 'Divers'}

    def get_cities(self, pattern):
        return self.cities.open(city=pattern).get_cities()

    def search_housings(self, type, cities, nb_rooms, area_min, area_max, cost_min, cost_max, house_types):

        ret = []
        for house_type in house_types:
            if house_type in self.RET:
                ret.append(self.RET.get(house_type))

        data = {'location': ','.join(cities),
                'areaMin': area_min or '',
                'areaMax': area_max or '',
                'priceMin': cost_min or '',
                'priceMax': cost_max or '',
                'transaction': self.TYPES.get(type, 'location'),
                'recherche': '',
                'mode': '',
                'proximity': '0',
                'roomMin': nb_rooms or '',
                'page': '1'
                }

        query = '%s%s%s' % (urllib.urlencode(data), '&type=', '&type='.join(ret))

        return self.search.go(query=query).iter_housings()

    def get_housing(self, _id, housing=None):
        return self.housing.go(_id=_id).get_housing(obj=housing)

    def get_phone(self, _id):
        return self.phone.go(_id=_id).get_phone()

    def get_total_page(self, js_datas):
        return self.housing.open(js_datas=js_datas).get_total_page()
