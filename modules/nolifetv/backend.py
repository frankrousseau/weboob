# -*- coding: utf-8 -*-

# Copyright(C) 2011 Romain Bignon
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


from __future__ import with_statement

from weboob.capabilities.video import ICapVideo
from weboob.tools.backend import BaseBackend

from .browser import NolifeTVBrowser
from .video import NolifeTVVideo


__all__ = ['NolifeTVBackend']


class NolifeTVBackend(BaseBackend, ICapVideo):
    NAME = 'nolifetv'
    MAINTAINER = 'Romain Bignon'
    EMAIL = 'romain@weboob.org'
    VERSION = '0.a'
    DESCRIPTION = 'NolifeTV videos website'
    LICENSE = 'AGPLv3+'
    BROWSER = NolifeTVBrowser

    def get_video(self, _id):
        with self.browser:
            video = self.browser.get_video(_id)
        return video

    def iter_search_results(self, pattern=None, sortby=ICapVideo.SEARCH_RELEVANCE, nsfw=False, max_results=None):
        with self.browser:
            return self.browser.iter_search_results(pattern)

    def fill_video(self, video, fields):
        if fields != ['thumbnail']:
            # if we don't want only the thumbnail, we probably want also every fields
            with self.browser:
                video = self.browser.get_video(NolifeTVVideo.id2url(video.id), video)
        if 'thumbnail' in fields and video.thumbnail:
            with self.browser:
                video.thumbnail.data = self.browser.readurl(video.thumbnail.url)

        return video

    OBJECTS = {NolifeTVVideo: fill_video}