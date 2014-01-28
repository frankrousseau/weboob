# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon, Christophe Benz, Noé Rubinstein
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

from .base import NotLoaded, Field, BytesField
from .file import ICapFile, BaseFile

__all__ = ['BaseImage', 'ICapImage']

class _BaseImage(BaseFile):
    """
    Fake class to allow the inclusion of a BaseImage property within
    the real BaseImage class
    """
    pass

class BaseImage(_BaseImage):
    """
    Represents an image file.
    """
    nsfw =      Field('Is this Not Safe For Work', bool, default=False)
    thumbnail = Field('Thumbnail of the image', _BaseImage)
    data =      BytesField('Data of image')

    def __str__(self):
        return self.url

    def __repr__(self):
        return '<Image url="%s">' % self.url

    def __iscomplete__(self):
        return self.data is not NotLoaded

class ICapImage(ICapFile):
    """
    Image file provider
    """
    def search_image(self, pattern, sortby=ICapFile.SEARCH_RELEVANCE, nsfw=False):
        """
        search for an image file

        :param pattern: pattern to search on
        :type pattern: str
        :param sortby: sort by ...(use SEARCH_* constants)
        :param nsfw: include non-suitable for work images if True
        :type nsfw: bool
        :rtype: iter[:class:`BaseImage`]
        """
        return self.search_file(pattern, sortby)

    def get_image(self, _id):
        """
        Get an image file from an ID.

        :param id: image file ID
        :type id: str
        :rtype: :class:`BaseImage`]
        """
        return self.get_file(_id)

