# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013 Christophe Benz, Romain Bignon, Julien Hebert
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
from weboob.tools.date import new_date, new_datetime
from weboob.capabilities.base import Field


__all__ = ['DateField', 'TimeField', 'DeltaField']

class DateField(Field):
    """
    A field which accepts only :class:`datetime.date` and :class:`datetime.datetime` types.
    """
    def __init__(self, doc, **kwargs):
        Field.__init__(self, doc, datetime.date, datetime.datetime, **kwargs)

    def __setattr__(self, name, value):
        if name == 'value':
            # Force use of our date and datetime types, to fix bugs in python2
            # with strftime on year<1900.
            if type(value) is datetime.datetime:
                value = new_datetime(value)
            if type(value) is datetime.date:
                value = new_date(value)
        return object.__setattr__(self, name, value)


class TimeField(Field):
    """
    A field which accepts only :class:`datetime.time` and :class:`datetime.time` types.
    """
    def __init__(self, doc, **kwargs):
        Field.__init__(self, doc, datetime.time, datetime.datetime, **kwargs)


class DeltaField(Field):
    """
    A field which accepts only :class:`datetime.timedelta` type.
    """
    def __init__(self, doc, **kwargs):
        Field.__init__(self, doc, datetime.timedelta, **kwargs)
