# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013 Romain Bignon, Florent Fourcot
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


from .browser import DresdenWetterBrowser
from weboob.capabilities.gauge import ICapGauge, GaugeSensor, Gauge,\
        SensorNotFound
from weboob.tools.backend import BaseBackend


__all__ = ['DresdenWetterBackend']


class DresdenWetterBackend(BaseBackend, ICapGauge):
    NAME = 'dresdenwetter'
    MAINTAINER = u'Florent Fourcot'
    EMAIL = 'weboob@flo.fourcot.fr'
    VERSION = '0.i'
    LICENSE = 'AGPLv3+'
    DESCRIPTION = u"Private wetter station Dresden"
    BROWSER = DresdenWetterBrowser

    def iter_gauges(self, pattern=None):
        if pattern is None or pattern.lower() in u"dresden"\
                or pattern.lower() in "weather":
            gauge = Gauge("wetter")
            gauge.name = u"Private Wetterstation Dresden"
            gauge.city = u"Dresden"
            gauge.object = u"Weather"
            gauge.sensors = self.browser.get_sensors_list()
            yield gauge

    def _get_gauge_by_id(self, id):
        for gauge in self.iter_gauges():
            if id == gauge.id:
                return gauge
        return None

    def _get_sensor_by_id(self, id):
        for gauge in self.iter_gauges():
            for sensor in gauge.sensors:
                if id == sensor.id:
                    return sensor
        return None

    def iter_sensors(self, gauge, pattern=None):
        if not isinstance(gauge, Gauge):
            gauge = self._get_gauge_by_id(gauge)
        if pattern is None:
            for sensor in gauge.sensors:
                yield sensor
        else:
            lowpattern = pattern.lower()
            for sensor in gauge.sensors:
                if lowpattern in sensor.name.lower():
                    yield sensor

    # Not in the website
    def iter_gauge_history(self, sensor):
        raise NotImplementedError()

    def get_last_measure(self, sensor):
        if not isinstance(sensor, GaugeSensor):
            sensor = self._get_sensor_by_id(sensor)
        if sensor is None:
            raise SensorNotFound()
        return sensor.lastvalue
