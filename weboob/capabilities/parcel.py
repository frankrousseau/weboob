# -*- coding: utf-8 -*-

# Copyright(C) 2013 Romain Bignon
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


from .base import CapBase, BaseObject, Field, StringField
from .date import DateField


class Event(BaseObject):
    date = DateField('Date')
    activity = StringField('Activity')
    location = StringField('Location')

    def __repr__(self):
        return u'<Event date=%r activity=%r location=%r>' % (self.date, self.activity, self.location)

class Parcel(BaseObject):
    STATUS_UNKNOWN = 0
    STATUS_PLANNED = 1
    STATUS_IN_TRANSIT = 2
    STATUS_ARRIVED = 3

    arrival = DateField('Scheduled arrival date')
    status = Field('Status of parcel', int, default=STATUS_UNKNOWN)
    info = StringField('Information about parcel status')
    history = Field('History', list)


class CapParcel(CapBase):
    def get_parcel_tracking(self, id):
        """
        Get information abouut a parcel.

        :param id: ID of the parcel
        :type id: :class:`str`
        :rtype: :class:`Parcel`
        """

        raise NotImplementedError()
