# -*- coding: utf-8 -*-

# Copyright(C) 2013      Romain Bignon
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


from weboob.capabilities.parcel import ICapParcel
from weboob.tools.backend import BaseBackend

from .browser import UpsBrowser


__all__ = ['UpsBackend']


class UpsBackend(BaseBackend, ICapParcel):
    NAME = 'ups'
    DESCRIPTION = u'UPS website'
    MAINTAINER = u'Romain Bignon'
    EMAIL = 'romain@weboob.org'
    VERSION = '0.j'

    BROWSER = UpsBrowser

    def get_parcel_tracking(self, id):
        with self.browser:
            return self.browser.get_tracking_info(id)
