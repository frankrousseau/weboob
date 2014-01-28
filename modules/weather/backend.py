# -*- coding: utf-8 -*-

# Copyright(C) 2012 Arno Renevier
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


from weboob.capabilities.weather import ICapWeather
from weboob.tools.backend import BaseBackend

from .browser import WeatherBrowser

__all__ = ['WeatherBackend']


class WeatherBackend(BaseBackend, ICapWeather):
    NAME = 'weather'
    MAINTAINER = u'Arno Renevier'
    EMAIL = 'arno@renevier.net'
    VERSION = '0.i'
    DESCRIPTION = 'Get forecasts from weather.com'
    LICENSE = 'AGPLv3+'
    BROWSER = WeatherBrowser

    def iter_city_search(self, pattern):
        return self.browser.iter_city_search(pattern)

    def get_current(self, city_id):
        return self.browser.get_current(city_id)

    def iter_forecast(self, city_id):
        return self.browser.iter_forecast(city_id)
