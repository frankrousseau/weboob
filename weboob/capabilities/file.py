# -*- coding: utf-8 -*-

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


from .base import IBaseCap, CapBaseObject, NotAvailable, Field, StringField, DateField


__all__ = ['BaseFile', 'ICapFile']


class BaseFile(CapBaseObject):
    """
    Represent a file.
    """
    title =         StringField('File title')
    url =           StringField('File URL')
    ext =           StringField('File extension')
    author =        StringField('File author')
    description =   StringField('File description')
    date =          DateField('File publication date')
    size =          Field('File size in bytes',int,long, default=NotAvailable)
    rating =        Field('Rating', int, long, float, default=NotAvailable)
    rating_max =    Field('Maximum rating', int, long, float, default=NotAvailable)

    @classmethod
    def id2url(cls, _id):
        """
        Overloaded in child classes provided by backends.
        """
        raise NotImplementedError()

    @property
    def page_url(self):
        """
        Get file page URL
        """
        return self.id2url(self.id)


class ICapFile(IBaseCap):
    """
    Provide file download
    """
    (SEARCH_RELEVANCE,
     SEARCH_RATING,
     SEARCH_VIEWS,
     SEARCH_DATE) = range(4)

    def search_file(self, pattern, sortby=SEARCH_RELEVANCE):
        """
        :param pattern: pattern to search on
        :type pattern: str
        :param sortby: sort by ... (user SEARCH_* constants)
        :rtype: iter[:class:`BaseFile`]
        """
        raise NotImplementedError()

    def get_file(self, _id):
        """
        Get a file from an ID

        :param _id: the file id. I can be a numeric ID, or a page url
        :type _id: str
        :rtype: :class:`BaseFile` or None if not found.
        """
        raise NotImplementedError()
