# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013 Romain Bignon
# Copyright(C) 2013 Pierre Mazière
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


from .base import IBaseCap, CapBaseObject, Field, StringField
from weboob.tools.capabilities.streaminfo import StreamInfo


__all__ = ['Radio', 'ICapRadio']


class Radio(CapBaseObject):
    """
    Radio object.
    """
    title =         StringField('Title of radio')
    description =   StringField('Description of radio')
    current =       Field('Current emission', StreamInfo)
    streams =       Field('List of streams', list)

class ICapRadio(IBaseCap):
    """
    Capability of radio websites.
    """
    def iter_radios_search(self, pattern):
        """
        Search a radio.

        :param pattern: pattern to search
        :type pattern: str
        :rtype: iter[:class:`Radio`]
        """
        raise NotImplementedError()

    def get_radio(self, id):
        """
        Get a radio from an ID.

        :param id: ID of radio
        :type id: str
        :rtype: :class:`Radio`
        """
        raise NotImplementedError()
