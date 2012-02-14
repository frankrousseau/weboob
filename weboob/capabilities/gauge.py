# -*- coding: utf-8 -*-

# Copyright(C) 2010  Romain Bignon, Florent Fourcot
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


from datetime import datetime
from .base import IBaseCap, CapBaseObject


__all__ = ['ICapWaterLevel']


class Gauge(CapBaseObject):
    def __init__(self, id):
        CapBaseObject.__init__(self, id)

        self.add_field('name', basestring)
        self.add_field('river', basestring)
        self.add_field('level', float)
        self.add_field('flow', float)
        self.add_field('lastdate', datetime)
        self.add_field('forecast', basestring)

class GaugeMeasure(CapBaseObject):
    def __init__(self):
        CapBaseObject.__init__(self, None)

        self.add_field('level', float)
        self.add_field('flow', float)
        self.add_field('date', datetime)

class ICapWaterLevel(IBaseCap):
    def iter_gauge_history(self, id):
        """
        Get history of a gauge.

        @param id [str]  ID of the river
        @return [iter(GaugeMeasure)]
        """
        raise NotImplementedError()

    def get_last_measure(self, id):
        """
        Get last measure of the gauge.

        @param id [str] ID of the gauge.
        @return [GaugeMeasure]
        """
        raise NotImplementedError()

    def iter_gauges(self, pattern=None):
        """
        Iter gauges.

        @param pattern [str] if specified, used to search gauges
        @return [iter(Gauge)]
        """
        raise NotImplementedError()
