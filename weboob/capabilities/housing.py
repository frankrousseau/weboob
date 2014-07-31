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


from .base import CapBase, BaseObject, Field, IntField, DecimalField, \
                  StringField, BytesField
from .date import DateField

__all__ = ['HousingPhoto', 'Housing', 'Query', 'City', 'CapHousing']


class HousingPhoto(BaseObject):
    """
    Photo of a housing.
    """
    url =       StringField('Direct URL to photo')
    data =      BytesField('Data of photo')

    def __init__(self, url):
        BaseObject.__init__(self, url.split('/')[-1])
        self.url = url

    def __iscomplete__(self):
        return self.data

    def __str__(self):
        return self.url

    def __repr__(self):
        return u'<HousingPhoto "%s" data=%do>' % (self.id, len(self.data) if self.data else 0)


class Housing(BaseObject):
    """
    Content of a housing.
    """
    title =         StringField('Title of housing')
    area =          DecimalField('Area of housing, in m2')
    cost =          DecimalField('Cost of housing')
    currency =      StringField('Currency of cost')
    date =          DateField('Date when the housing has been published')
    location =      StringField('Location of housing')
    station =       StringField('What metro/bus station next to housing')
    text =          StringField('Text of the housing')
    phone =         StringField('Phone number to contact')
    photos =        Field('List of photos', list)
    details =       Field('Key/values of details', dict)


class Query(BaseObject):
    """
    Query to find housings.
    """
    TYPE_RENT = 0
    TYPE_SALE = 1

    type =      IntField('Type of housing to find (TYPE_* constants)')
    cities =    Field('List of cities to search in', list, tuple)
    area_min =  IntField('Minimal area (in m2)')
    area_max =  IntField('Maximal area (in m2)')
    cost_min =  IntField('Minimal cost')
    cost_max =  IntField('Maximal cost')
    nb_rooms =  IntField('Number of rooms')

    def __init__(self):
        BaseObject.__init__(self, '')


class City(BaseObject):
    """
    City.
    """
    name =      StringField('Name of city')


class CapHousing(CapBase):
    """
    Capability of websites to search housings.
    """
    def search_housings(self, query):
        """
        Search housings.

        :param query: search query
        :type query: :class:`Query`
        :rtype: iter[:class:`Housing`]
        """
        raise NotImplementedError()

    def get_housing(self, housing):
        """
        Get an housing from an ID.

        :param housing: ID of the housing
        :type housing: str
        :rtype: :class:`Housing` or None if not found.
        """
        raise NotImplementedError()

    def search_city(self, pattern):
        """
        Search a city from a pattern.

        :param pattern: pattern to search
        :type pattern: str
        :rtype: iter[:class:`City`]
        """
        raise NotImplementedError()
