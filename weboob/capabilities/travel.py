# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon, Julien Hebert
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


import datetime

from .base import IBaseCap, CapBaseObject, StringField, TimeField, DeltaField, \
                  DateField, DecimalField, UserError


__all__ = ['Station', 'Departure', 'RoadStep', 'RoadmapError', 'RoadmapFilters', 'ICapTravel']


class Station(CapBaseObject):
    """
    Describes a station.
    """
    name =  StringField('Name of station')

    def __init__(self, id, name):
        CapBaseObject.__init__(self, id)
        self.name = name

    def __repr__(self):
        return "<Station id=%r name=%r>" % (self.id, self.name)


class Departure(CapBaseObject):
    """
    Describes a departure.
    """
    type =              StringField('Type of train')
    time =              TimeField('Departure time')
    departure_station = StringField('Departure station')
    arrival_station =   StringField('Destination of the train')
    arrival_time =      TimeField('Arrival time')
    late =              TimeField('Optional late', default=datetime.time())
    information =       StringField('Informations')
    plateform =         StringField('Where the train will leave')
    price =             DecimalField('Price of ticket')
    currency =          StringField('Currency', default=None)

    def __init__(self, id, _type, _time):
        CapBaseObject.__init__(self, id)

        self.type = _type
        self.time = _time

    def __repr__(self):
        return u"<Departure id=%r type=%r time=%r departure=%r arrival=%r>" % (
            self.id, self.type, self.time.strftime('%H:%M'), self.departure_station, self.arrival_station)


class RoadStep(CapBaseObject):
    """
    A step on a roadmap.
    """
    line =          StringField('When line')
    start_time =    TimeField('Start of step')
    end_time =      TimeField('End of step')
    departure =     StringField('Departure station')
    arrival =       StringField('Arrival station')
    duration =      DeltaField('Duration of this step')


class RoadmapError(UserError):
    """
    Raised when the roadmap is unable to be calculated.
    """


class RoadmapFilters(CapBaseObject):
    """
    Filters to get a roadmap.
    """
    departure_time =    DateField('Wanted departure time')
    arrival_time =      DateField('Wanted arrival time')

    def __init__(self):
        CapBaseObject.__init__(self, '')


class ICapTravel(IBaseCap):
    """
    Travel websites.
    """
    def iter_station_search(self, pattern):
        """
        Iterates on search results of stations.

        :param pattern: the search pattern
        :type pattern: str
        :rtype: iter[:class:`Station`]
        """
        raise NotImplementedError()

    def iter_station_departures(self, station_id, arrival_id=None, date=None):
        """
        Iterate on departures.

        :param station_id: the station ID
        :type station_id: str
        :param arrival_id: optionnal arrival station ID
        :type arrival_id: str
        :param date: optional date
        :type date: datetime.datetime
        :rtype: iter[:class:`Departure`]
        """
        raise NotImplementedError()

    def iter_roadmap(self, departure, arrival, filters):
        """
        Get a roadmap.

        :param departure: name of departure station
        :type departure: str
        :param arrival: name of arrival station
        :type arrival: str
        :param filters: filters on search
        :type filters: :class:`RoadmapFilters`
        :rtype: iter[:class:`RoadStep`]
        """
        raise NotImplementedError()
