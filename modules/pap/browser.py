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

from weboob.browser import PagesBrowser, URL
from weboob.capabilities.housing import Query

from .pages import SearchResultsPage, HousingPage, CitiesPage


__all__ = ['PapBrowser']


class PapBrowser(PagesBrowser):

    BASEURL = 'http://www.pap.fr'
    search_page = URL('annonce/.*', SearchResultsPage)
    housing = URL('annonces/(?P<_id>.*)', HousingPage)
    cities = URL('index/ac-geo2\?q=(?P<pattern>.*)', CitiesPage)

    def search_geo(self, pattern):
        return self.cities.open(pattern=pattern).iter_cities()

    TYPES = {Query.TYPE_RENT: 'location',
             Query.TYPE_SALE: 'vente'}

    RET = {Query.HOUSE_TYPES.HOUSE: 'maison',
           Query.HOUSE_TYPES.APART: 'appartement',
           Query.HOUSE_TYPES.LAND: 'terrain',
           Query.HOUSE_TYPES.PARKING: 'garage-parking',
           Query.HOUSE_TYPES.OTHER: 'divers'}

    def search_housings(self, type, cities, nb_rooms, area_min, area_max, cost_min, cost_max, house_types):
        self.session.headers.update({'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})

        data = {'geo_objets_ids': ','.join(cities),
                'surface[min]':   area_min or '',
                'surface[max]':   area_max or '',
                'prix[min]':      cost_min or '',
                'prix[max]':      cost_max or '',
                'produit':        self.TYPES.get(type, 'location'),
                'recherche':      1,
                'nb_resultats_par_page': 40,
                }

        if nb_rooms:
            data['nb_pieces[min]'] = nb_rooms
            data['nb_pieces[max]'] = nb_rooms

        ret = []
        for house_type in house_types:
            if house_type in self.RET:
                ret.append(self.RET.get(house_type))

        _data = '%s%s%s' % (urllib.urlencode(data), '&typesbien%5B%5D=', '&typesbien%5B%5D='.join(ret))
        return self.search_page.go(data=_data).iter_housings()

    def get_housing(self, _id, housing=None):
        return self.housing.go(_id=_id).get_housing(obj=housing)
