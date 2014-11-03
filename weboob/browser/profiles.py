# -*- coding: utf-8 -*-

# Copyright(C) 2012-2014 Laurent Bachelier
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


class Profile(object):
    """
    A profile represents the way Browser should act.
    Usually it is to mimic a real browser.
    """

    def setup_session(self, session):
        """
        Change default headers, set up hooks, etc.

        Warning: Do not enable lzma, bzip or bzip2, sdch encodings
        as python-requests does not support it yet.
        Supported as of 2.2: gzip, deflate, compress.
        In doubt, do not change the default Accept-Encoding header
        of python-requests.
        """
        raise NotImplementedError()


class Weboob(Profile):
    """
    It's us!
    Recommended for Weboob-friendly websites only.
    """

    def __init__(self, version):
        self.version = version

    def setup_session(self, session):
        session.headers['User-Agent'] = 'weboob/%s' % self.version


class Firefox(Profile):
    """
    Try to mimic a specific version of Firefox.
    Ideally, it should follow the current ESR Firefox:
    https://www.mozilla.org/en-US/firefox/organizations/all.html
    Do not change the Firefox version without checking the Gecko one!
    """

    def setup_session(self, session):
        """
        Set up headers for a standard Firefox request
        (except for DNT which isn't on by default but is a good idea).

        The goal is to be unidentifiable.
        """
        # Replace all base requests headers
        # https://developer.mozilla.org/en/Gecko_user_agent_string_reference
        # https://bugzilla.mozilla.org/show_bug.cgi?id=572650
        session.headers = {
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:31.0) Gecko/20100101 Firefox/31.0',
            'DNT': '1'}


class Wget(Profile):
    """
    Common alternative user agent.
    Some websites will give you a version with less JavaScript.
    Some others could ban you (after all, wget is not a real browser).
    """

    def __init__(self, version='1.11.4'):
        self.version = version

    def setup_session(self, session):
        # Don't remove base headers, if websites want to block fake browsers,
        # they will probably block any wget user agent anyway.
        session.headers.update({
            'Accept': '*/*',
            'User-Agent': 'Wget/%s' % self.version})


class Android(Profile):
    """
    An android profile for mobile websites
    """

    def setup_session(self, session):
        """
        Set up user agent.
        """
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.0.3; fr-fr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30'})
