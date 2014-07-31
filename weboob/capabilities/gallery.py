# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon, Christophe Benz, Noé Rubinstein
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


from weboob.tools.capabilities.thumbnail import Thumbnail
from .base import CapBase, BaseObject, NotLoaded, Field, StringField, \
                  BytesField, IntField, FloatField
from .date import DateField


__all__ = ['BaseGallery', 'BaseImage', 'CapGallery']


class BaseGallery(BaseObject):
    """
    Represents a gallery.

    This object has to be inherited to specify how to calculate the URL of the gallery from its ID.
    """
    title =         StringField('Title of gallery')
    url =           StringField('Direct URL to gallery')
    description =   StringField('Description of gallery')
    cardinality =   IntField('Cardinality of gallery')
    date =          DateField('Date of gallery')
    rating =        FloatField('Rating of this gallery')
    rating_max =    FloatField('Max rating available')
    thumbnail =     Field('Thumbnail', Thumbnail)

    def __init__(self, _id, title=NotLoaded, url=NotLoaded, cardinality=NotLoaded, date=NotLoaded,
                 rating=NotLoaded, rating_max=NotLoaded, thumbnail=NotLoaded, thumbnail_url=None, nsfw=False):
        BaseObject.__init__(self, unicode(_id))

        self.title = title
        self.url = url
        self.date = date
        self.rating = rating
        self.rating_max = rating_max
        self.thumbnail = thumbnail

    @classmethod
    def id2url(cls, _id):
        """Overloaded in child classes provided by backends."""
        raise NotImplementedError()

    @property
    def page_url(self):
        """
        Get URL to page of this gallery.
        """
        return self.id2url(self.id)

    def iter_image(self):
        """
        Iter images.
        """
        raise NotImplementedError()


class BaseImage(BaseObject):
    """
    Base class for images.
    """
    index =     IntField('Usually page number')
    thumbnail = Field('Thumbnail of the image', Thumbnail)
    url =       StringField('Direct URL to image')
    ext =       StringField('Extension of image')
    data =      BytesField('Data of image')
    gallery =   Field('Reference to the Gallery object', BaseGallery)

    def __init__(self, _id, index=None, thumbnail=NotLoaded, url=NotLoaded,
            ext=NotLoaded, gallery=None):

        BaseObject.__init__(self, unicode(_id))

        self.index = index
        self.thumbnail = thumbnail
        self.url = url
        self.ext = ext
        self.gallery = gallery

    def __str__(self):
        return self.url

    def __repr__(self):
        return '<Image url="%s">' % self.url

    def __iscomplete__(self):
        return self.data is not NotLoaded


class CapGallery(CapBase):
    """
    This capability represents the ability for a website backend to provide videos.
    """
    (SEARCH_RELEVANCE,
     SEARCH_RATING,
     SEARCH_VIEWS,
     SEARCH_DATE) = range(4)

    def search_gallery(self, pattern, sortby=SEARCH_RELEVANCE):
        """
        Iter results of a search on a pattern.

        :param pattern: pattern to search on
        :type pattern: str
        :param sortby: sort by...
        :type sortby: SEARCH_*
        :rtype: :class:`BaseGallery`
        """
        raise NotImplementedError()

    def get_gallery(self, _id):
        """
        Get gallery from an ID.

        :param _id: the gallery id. It can be a numeric ID, or a page url, or so.
        :type _id: str
        :rtype: :class:`Gallery`
        """
        raise NotImplementedError()

    def iter_gallery_images(self, gallery):
        """
        Iterate images from a Gallery.

        :type gallery: BaseGallery
        :rtype: iter(BaseImage)
        """
        raise NotImplementedError()
