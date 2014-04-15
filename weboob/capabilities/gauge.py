# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012  Romain Bignon, Florent Fourcot
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


from .base import IBaseCap, CapBaseObject, StringField, FloatField, DateField, Field, UserError, empty

__all__ = ['Gauge', 'GaugeSensor', 'GaugeMeasure', 'ICapGauge', 'SensorNotFound']


class SensorNotFound(UserError):
    """
    Not found a sensor
    """


class Gauge(CapBaseObject):
    """
    Gauge class.
    """
    name =       StringField('Name of gauge')
    city =       StringField('City of the gauge')
    object =     StringField('What is evaluate') # For example, name of a river
    sensors =    Field('List of sensors on the gauge', list)


class GaugeMeasure(CapBaseObject):
    """
    Measure of a gauge sensor.
    """
    level =     FloatField('Level of measure')
    date =      DateField('Date of measure')
    alarm =     StringField('Alarm level')

    def __init__(self):
        CapBaseObject.__init__(self)

    def __repr__(self):
        if empty(self.level):
            return "<GaugeMeasure is %s>" % self.level
        else:
            return "<GaugeMeasure level=%f alarm=%s date=%s>" % (self.level, self.alarm, self.date)


class GaugeSensor(CapBaseObject):
    """
    GaugeSensor class.
    """
    name =      StringField('Name of the sensor')
    unit =      StringField('Unit of values')
    forecast =  StringField('Forecast')
    address =   StringField('Address')
    lastvalue = Field('Last value', GaugeMeasure)
    history =   Field('Value history', list)  # lastvalue not included
    gaugeid =   StringField('Id of the gauge')

    def __repr__(self):
        return "<GaugeSensor id=%s name=%s>" % (self.id, self.name)


class ICapGauge(IBaseCap):
    def iter_gauges(self, pattern=None):
        """
        Iter gauges.

        :param pattern: if specified, used to search gauges.
        :type pattern: str
        :rtype: iter[:class:`Gauge`]
        """
        raise NotImplementedError()

    def iter_sensors(self, id, pattern=None):
        """
        Iter instrument of a gauge.

        :param: ID of the gauge
        :param pattern: if specified, used to search sensors.
        :type pattern: str
        :rtype: iter[:class:`GaugeSensor`]
        """
        raise NotImplementedError()

    def iter_gauge_history(self, id):
        """
        Get history of a gauge sensor.

        :param id: ID of the gauge sensor
        :type id: str
        :rtype: iter[:class:`GaugeMeasure`]
        """
        raise NotImplementedError()

    def get_last_measure(self, id):
        """
        Get last measures of a censor.

        :param id: ID of the censor.
        :type id: str
        :rtype: :class:`GaugeMeasure`
        """
        raise NotImplementedError()
