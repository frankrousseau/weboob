# -*- coding: utf-8 -*-
# Copyright(C) 2013 Thomas Lecavelier
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

from weboob.capabilities.radio import ICapRadio, Radio
from weboob.capabilities.collection import ICapCollection
from weboob.tools.backend import BaseBackend
from .browser import NihonNoOtoBrowser

__all__ = ['NihonNoOtoBackend']

class NihonNoOtoBackend(BaseBackend, ICapRadio, ICapCollection):
    NAME = 'nihonnooto'
    MAINTAINER = u'Thomas Lecavelier'
    EMAIL = 'thomas-weboob@lecavelier.name'
    VERSION = '0.j'
    DESCRIPTION = u'« Le son du Japon » french operated web radio, diffusing japanese music'
    # License of your module
    LICENSE = 'AGPLv3+'

    BROWSER = NihonNoOtoBrowser
    _RADIOS = {'nihonnooto': (u'Nihon no OTO', True) }

    def iter_resources(self, objs, split_path):
        if Radio in objs:
            self._restrict_level(split_path)
        for radio in self.browser.iter_radios_list():
            self.browser.get_current_emission()
            radio.current = self.browser.get_current_emission()
            yield radio

    def iter_radios_search(self, pattern):
        for radio in self.browser.iter_radios_list():
            if pattern.lower() in radio.title.lower() or pattern.lower() in radio.description.lower():
                self.browser.get_current_emission()
                radio.current = self.browser.get_current_emission()

                yield radio

    def get_radio(self, radio):
        if not isinstance(radio, Radio):
           for rad in self.browser.iter_radios_list():
               if rad.id == radio:
                  return rad
        return None

    def fill_radio(self, radio, fields):
        if 'current' in fields:
            return self.get_radio(radio.id)
        return radio

    OBJECTS = {Radio: fill_radio}
