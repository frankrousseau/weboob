# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013 Romain Bignon, Christophe Benz
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

from datetime import timedelta

from .base import Field
from .image import ICapImage, BaseImage


__all__ = ['BaseVideo', 'ICapVideo']


class BaseVideo(BaseImage):
    """
    Represents a video.

    This object has to be inherited to specify how to calculate the URL of the video from its ID.
    """
    duration =  Field('file duration', int, long, timedelta)

class ICapVideo(ICapImage):
    """
    Video file provider.
    """

    def search_videos(self, pattern, sortby=ICapImage.SEARCH_RELEVANCE, nsfw=False):
        """
        search for a video file

        :param pattern: pattern to search on
        :type pattern: str
        :param sortby: sort by... (use SEARCH_* constants)
        :param nsfw: include non-suitable for work videos if True
        :type nsfw: bool
        :rtype: iter[:class:`BaseVideo`]
        """
        return self.search_image(pattern, sortby, nsfw)

    def get_video(self, _id):
        """
        Get a video file from an ID.

        :param _id: video file ID
        :type _id: str
        :rtype: :class:`BaseVideo` or None is fot found.
        """
        return self.get_image(_id)
