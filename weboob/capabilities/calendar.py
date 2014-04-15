# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013 Bezleputh
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

from .base import CapBaseObject, IBaseCap, StringField, DateField, IntField, FloatField, Field

__all__ = ['BaseCalendarEvent', 'ICapCalendarEvent']


def enum(**enums):
    _values = enums.values()
    _items = enums.items()
    _index = dict((value, i) for i, value in enumerate(enums.values()))
    _types = list((type(value) for value in enums.values()))
    enums['values'] = _values
    enums['items'] = _items
    enums['index'] = _index
    enums['types'] = _types
    return type('Enum', (), enums)

CATEGORIES = enum(CONCERT=u'Concert', CINE=u'Cinema', THEATRE=u'Theatre', TELE=u'Television')

#the following elements deal with ICalendar stantdards
#see http://fr.wikipedia.org/wiki/ICalendar#Ev.C3.A9nements_.28VEVENT.29
TRANSP = enum(OPAQUE=u'OPAQUE', TRANSPARENT=u'TRANSPARENT')
STATUS = enum(TENTATIVE=u'TENTATIVE', CONFIRMED=u'CONFIRMED', CANCELLED=u'CANCELLED')


class BaseCalendarEvent(CapBaseObject):
    """
    Represents a calendar event
    """

    url = StringField('URL of the event')
    start_date = DateField('Start date of the event')
    end_date = DateField('End date of the event')
    summary = StringField('Title of the event')
    city = StringField('Name of the city in witch event will take place')
    location = StringField('Location of the event')
    category = Field('Category of the event', *CATEGORIES.types)
    description = StringField('Description of the event')
    price = FloatField('Price of the event')
    booked_entries = IntField('Entry number')
    max_entries = IntField('Max entry number')
    event_planner = StringField('Name of the event planner')

    #the following elements deal with ICalendar stantdards
    #see http://fr.wikipedia.org/wiki/ICalendar#Ev.C3.A9nements_.28VEVENT.29
    sequence = IntField('Number of updates, the first is number 1')

    # (TENTATIVE, CONFIRMED, CANCELLED)
    status = Field('Status of theevent', *STATUS.types)
    # (OPAQUE, TRANSPARENT)
    transp = Field('Describes if event is available', *TRANSP.types)

    @classmethod
    def id2url(cls, _id):
        """Overloaded in child classes provided by backends."""
        raise NotImplementedError()

    @property
    def page_url(self):
        """
        Get page URL of the announce.
        """
        return self.id2url(self.id)


class Query(CapBaseObject):
    """
    Query to find events
    """

    start_date = DateField('Start date of the event')
    end_date = DateField('End date of the event')
    city = StringField('Name of the city in witch event will take place')
    categories = Field('List of categories of the event', list, tuple)

    def __init__(self):
        CapBaseObject.__init__(self, '')
        self.categories = []
        for value in CATEGORIES.values:
            self.categories.append(value)


class ICapCalendarEvent(IBaseCap):
    """
    Capability of calendar event type sites
    """

    ASSOCIATED_CATEGORIES = 'ALL'

    def has_matching_categories(self, query):
        if self.ASSOCIATED_CATEGORIES == 'ALL':
            return True

        for category in query.categories:
            if category in self.ASSOCIATED_CATEGORIES:
                return True
        return False

    def search_events(self, query):
        """
        Search event

        :param query: search query
        :type query: :class:`Query`
        :rtype: iter[:class:`BaseCalendarEvent`]
        """
        raise NotImplementedError()

    def list_events(self, date_from, date_to=None):
        """
        list coming event.

        :param date_from: date of beguinning of the events list
        :type date_from: date
        :param date_to: date of ending of the events list
        :type date_to: date
        :rtype: iter[:class:`BaseCalendarEvent`]
        """
        raise NotImplementedError()

    def get_event(self, _id):
        """
        Get an event from an ID.

        :param _id: id of the event
        :type _id: str
        :rtype: :class:`BaseCalendarEvent` or None is fot found.
        """
        raise NotImplementedError()

    def attends_event(self, event, is_attending=True):
        """
        Attends or not to an event
        :param event : the event
        :type event : BaseCalendarEvent
        :param is_attending : is attending to the event or not
        :type is_attending : bool
        """
        raise NotImplementedError()
