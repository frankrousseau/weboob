# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Christophe Benz
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


import sys
from optparse import OptionGroup

from weboob.tools.application.base import BaseApplication


class WeboobDebug(BaseApplication):
    APPNAME = 'weboobdebug'
    VERSION = '0.i'
    COPYRIGHT = 'Copyright(C) 2010-2011 Christophe Benz'
    DESCRIPTION = "Weboob-Debug is a console application to debug backends."
    SHORT_DESCRIPTION = "debug backends"

    def __init__(self, option_parser=None):
        super(WeboobDebug, self).__init__(option_parser)
        options = OptionGroup(self._parser, 'Weboob-Debug options')
        options.add_option('-B', '--bpython', action='store_true', help='Prefer bpython over ipython')
        self._parser.add_option_group(options)

    def load_default_backends(self):
        pass

    def main(self, argv):
        """
        BACKEND

        Debug BACKEND.
        """
        try:
            backend_name = argv[1]
        except IndexError:
            print >>sys.stderr, 'Usage: %s BACKEND' % argv[0]
            return 1
        try:
            backend = self.weboob.load_backends(names=[backend_name])[backend_name]
        except KeyError:
            print >>sys.stderr, u'Unable to load backend "%s"' % backend_name
            return 1

        locs = dict(backend=backend, browser=backend.browser, application=self, weboob=self.weboob)
        banner = 'Weboob debug shell\nBackend "%s" loaded.\nAvailable variables:\n' % backend_name \
                 + '\n'.join(['  %s: %s' % (k, v) for k, v in locs.iteritems()])

        if self.options.bpython:
            funcs = [self.bpython, self.ipython, self.python]
        else:
            funcs = [self.ipython, self.bpython, self.python]

        for func in funcs:
            try:
                func(locs, banner)
            except ImportError:
                continue
            else:
                break

    def ipython(self, locs, banner):
        try:
            from IPython import embed
            embed(user_ns=locs, banner2=banner)
        except ImportError:
            from IPython.Shell import IPShellEmbed
            shell = IPShellEmbed(argv=[])
            shell.set_banner(shell.IP.BANNER + '\n\n' + banner)
            shell(local_ns=locs, global_ns={})

    def bpython(self, locs, banner):
        from bpython import embed
        embed(locs, banner=banner)

    def python(self, locs, banner):
        import code
        try:
            import readline
            import rlcompleter
            readline.set_completer(rlcompleter.Completer(locs).complete)
            readline.parse_and_bind("tab:complete")
        except ImportError:
            pass
        code.interact(banner=banner, local=locs)
