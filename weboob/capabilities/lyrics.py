# -*- coding: utf-8 -*-

# Copyright(C) 2013
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


from .base import Capability, BaseObject, StringField


__all__ = ['SongLyrics', 'CapLyrics']


class SongLyrics(BaseObject):
    """
    Song lyrics object.
    """
    title =      StringField('Title of the song')
    artist =       StringField('Artist of the song')
    content =    StringField('Lyrics of the song')

    def __init__(self, id, title):
        BaseObject.__init__(self, id)
        self.title = title


class CapLyrics(Capability):
    """
    Lyrics websites.
    """

    def iter_lyrics(self, criteria, pattern):
        """
        Search lyrics by artist or by song
        and iterate on results.

        :param criteria: 'artist' or 'song'
        :type criteria: str
        :param pattern: pattern to search
        :type pattern: str
        :rtype: iter[:class:`SongLyrics`]
        """
        raise NotImplementedError()

    def get_lyrics(self, _id):
        """
        Get a lyrics object from an ID.

        :param _id: ID of lyrics
        :type _id: str
        :rtype: :class:`SongLyrics`
        """
        raise NotImplementedError()
