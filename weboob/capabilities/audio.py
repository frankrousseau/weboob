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

import re

from datetime import timedelta

from .image import BaseImage
from .base import Field, StringField, IntField, CapBaseObject
from .file import ICapFile, BaseFile


__all__ = ['BaseAudio', 'ICapAudio']


def decode_id(decode_id):
    def wrapper(func):
        def inner(self, *args, **kwargs):
            arg = unicode(args[0])
            _id = decode_id(arg)
            if _id is None:
                return None

            new_args = [_id]
            new_args.extend(args[1:])
            return func(self, *new_args, **kwargs)
        return inner
    return wrapper


class Album(CapBaseObject):
    """
    Represent an album
    """
    title = StringField('album name')
    author = StringField('artist name')
    year = IntField('release year')
    thumbnail = Field('Image associated to the album', BaseImage)
    tracks_list = Field('list of tracks', list)

    def __init__(self, _id):
        CapBaseObject.__init__(self, unicode("album.%s" % _id))

    @classmethod
    def decode_id(cls, _id):
        if _id:
            m = re.match('^(album)\.(.*)', _id)
            if m:
                return m.group(2)
            return _id


class Playlist(CapBaseObject):
    """
    Represent a playlist
    """
    title = StringField('playlist name')
    tracks_list = Field('list of tracks', list)

    def __init__(self, _id):
        CapBaseObject.__init__(self, unicode("playlist.%s" % _id))

    @classmethod
    def decode_id(cls, _id):
        if _id:
            m = re.match('^(playlist)\.(.*)', _id)
            if m:
                return m.group(2)
            return _id


class BaseAudio(BaseFile):
    """
    Represent an audio file
    """
    duration =  Field('file duration', int, long, timedelta)
    bitrate =   Field('file bit rate in Kbps', int)
    format =    StringField('file format')
    thumbnail = Field('Image associated to the file', BaseImage)

    def __init__(self, _id):
        BaseFile.__init__(self, unicode("audio.%s" % _id))

    @classmethod
    def decode_id(cls, _id):
        if _id:
            m = re.match('^(audio)\.(.*)', _id)
            if m:
                return m.group(2)
            return _id


class ICapAudio(ICapFile):
    """
    Audio file provider
    """

    @classmethod
    def get_object_method(cls, _id):
        m = re.match('^(\w+)\.(.*)', _id)
        if m:
            if m.group(1) == 'album':
                return 'get_album'

            elif m.group(1) == 'playlist':
                return 'get_playlist'

            else:
                return 'get_audio'

    def search_audio(self, pattern, sortby=ICapFile.SEARCH_RELEVANCE):
        """
        search for a audio file

        :param pattern: pattern to search on
        :type pattern: str
        :param sortby: sort by ...(use SEARCH_* constants)
        :rtype: iter[:class:`BaseAudio`]
        """
        return self.search_file(pattern, sortby)

    def search_album(self, pattern, sortby=ICapFile.SEARCH_RELEVANCE):
        """
        search for an album
        :param pattern: pattern to search on
        :type pattern: str
        :rtype: iter[:class:`Album`]
        """
        raise NotImplementedError()

    def search_playlist(self, pattern, sortby=ICapFile.SEARCH_RELEVANCE):
        """
        search for an album
        :param pattern: pattern to search on
        :type pattern: str
        :rtype: iter[:class:`Playlist`]
        """
        raise NotImplementedError()

    @decode_id(BaseAudio.decode_id)
    def get_audio(self, _id):
        """
        Get an audio file from an ID.

        :param id: audio file ID
        :type id: str
        :rtype: :class:`BaseAudio`]
        """
        return self.get_file(_id)

    @decode_id(Playlist.decode_id)
    def get_playlist(self, _id):
        """
        Get a playlist from an ID.

        :param id: playlist ID
        :type id: str
        :rtype: :class:`Playlist`]
        """
        raise NotImplementedError()

    @decode_id(Album.decode_id)
    def get_album(self, _id):
        """
        Get an album from an ID.

        :param id: album ID
        :type id: str
        :rtype: :class:`Album`]
        """
        raise NotImplementedError()
