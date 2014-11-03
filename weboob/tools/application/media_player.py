# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Christophe Benz, Romain Bignon, John Obbele
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


from __future__ import print_function

import os
from subprocess import PIPE, Popen
import cookielib
import urllib2

from weboob.tools.log import getLogger

__all__ = ['InvalidMediaPlayer', 'MediaPlayer', 'MediaPlayerNotFound']


PLAYERS = (
    ('mpv',      '-'),
    ('mplayer2', '-'),
    ('mplayer',  '-'),
    ('vlc',      '-'),
    ('parole',   'fd://0'),
    ('totem',    'fd://0'),
    ('xine',     'stdin:/'),
)


class MediaPlayerNotFound(Exception):
    def __init__(self):
        Exception.__init__(self, u'No media player found on this system. Please install one of them: %s.' %
                           ', '.join(player[0] for player in PLAYERS))


class InvalidMediaPlayer(Exception):
    def __init__(self, player_name):
        Exception.__init__(self, u'Invalid media player: %s. Valid media players: %s.' % (
            player_name, ', '.join(player[0] for player in PLAYERS)))


class MediaPlayer(object):
    """
    Black magic invoking a media player to this world.

    Presently, due to strong disturbances in the holidays of the ether
    world, the media player used is chosen from a static list of
    programs. See PLAYERS for more information.
    """

    def __init__(self, logger=None):
        self.logger = getLogger('mediaplayer', logger)

    def guess_player_name(self):
        for player_name in [player[0] for player in PLAYERS]:
            if self._find_in_path(os.environ['PATH'], player_name):
                return player_name
        return None

    def play(self, media, player_name=None, player_args=None):
        """
        Play a media object, using programs from the PLAYERS list.

        This function dispatch calls to either _play_default or
        _play_rtmp for special rtmp streams using SWF verification.
        """
        player_names = [player[0] for player in PLAYERS]
        if not player_name:
            self.logger.debug(u'No media player given. Using the first available from: %s.' %
                              ', '.join(player_names))
            player_name = self.guess_player_name()
            if player_name is None:
                raise MediaPlayerNotFound()
        if media.url.startswith('rtmp'):
            self._play_rtmp(media, player_name, args=player_args)
        else:
            self._play_default(media, player_name, args=player_args)

    def _play_default(self, media, player_name, args=None):
        """
        Play media.url with the media player.
        """
        # if flag play_proxy...
        if hasattr(media, '_play_proxy') and media._play_proxy is True:
            # use urllib2 to handle redirect and cookies
            self._play_proxy(media, player_name, args)
            return None

        args = player_name.split(' ')

        player_name = args[0]
        args.append(media.url)

        print('Invoking "%s".' % (' '.join(args)))
        os.spawnlp(os.P_WAIT, player_name, *args)

    def _play_proxy(self, media, player_name, args):
        """
        Load data with python urllib2 and pipe data to a media player.

        We need this function for url that use redirection and cookies.
        This function is used if the non-standard,
        non-API compliant '_play_proxy' attribute of the 'media' object is defined and is True.
        """
        if args is None:
            for (binary, stdin_args) in PLAYERS:
                if binary == player_name:
                    args = stdin_args

        assert args is not None

        print(':: Play_proxy streaming from %s' % media.url)
        print(':: to %s %s' % (player_name, args))
        print(player_name + ' ' + args)
        proc = Popen(player_name + ' ' + args, stdin=PIPE, shell=True)

        # Handle cookies (and redirection 302...)
        cj = cookielib.CookieJar()
        url_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        url_handler = url_opener.open(media.url)
        file_size = int(url_handler.info().getheaders("Content-Length")[0])
        file_size_dl = 0
        block_sz = 8192
        while file_size_dl < file_size:
            _buffer = url_handler.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(_buffer)
            try:
                proc.stdin.write(_buffer)
            except:
                print("play_proxy broken pipe. Can't write anymore.")
                break

    def _play_rtmp(self, media, player_name, args):
        """
        Download data with rtmpdump and pipe them to a media player.

        You need a working version of rtmpdump installed and the SWF
        object url in order to comply with SWF verification requests
        from the server. The last one is retrieved from the non-standard
        non-API compliant 'swf_player' attribute of the 'media' object.
        """
        if not self._find_in_path(os.environ['PATH'], 'rtmpdump'):
            self.logger.warning('"rtmpdump" binary not found')
            return self._play_default(media, player_name)
        media_url = media.url
        try:
            player_url = media.swf_player
            if media.swf_player:
                rtmp = 'rtmpdump -r %s --swfVfy %s' % (media_url, player_url)
            else:
                rtmp = 'rtmpdump -r %s' % media_url
        except AttributeError:
            self.logger.warning('Your media object does not have a "swf_player" attribute. SWF verification will be '
                                'disabled and may prevent correct media playback.')
            return self._play_default(media, player_name)

        rtmp += ' --quiet'

        if args is None:
            for (binary, stdin_args) in PLAYERS:
                if binary == player_name:
                    args = stdin_args

        assert args is not None

        player_name = player_name.split(' ')
        args = args.split(' ')

        print(':: Streaming from %s' % media_url)
        print(':: to %s %s' % (player_name, args))
        print(':: %s' % rtmp)
        p1 = Popen(rtmp.split(), stdout=PIPE)
        Popen(player_name + args, stdin=p1.stdout, stderr=PIPE)

    def _find_in_path(self, path, filename):
        for i in path.split(':'):
            if os.path.exists('/'.join([i, filename])):
                return True
        return False
