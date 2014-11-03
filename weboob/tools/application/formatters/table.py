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


from prettytable import PrettyTable

from weboob.capabilities.base import empty

from .iformatter import IFormatter


__all__ = ['TableFormatter', 'HTMLTableFormatter']


class TableFormatter(IFormatter):
    HTML = False

    def __init__(self):
        IFormatter.__init__(self)
        self.queue = []
        self.keys = None
        self.header = None

    def flush(self):
        s = self.get_formatted_table()
        if s is not None:
            self.output(s.encode('utf-8'))

    def get_formatted_table(self):
        if len(self.queue) == 0:
            return

        queue = [() for i in xrange(len(self.queue))]
        column_headers = []
        # Do not display columns when all values are NotLoaded or NotAvailable
        for i in xrange(len(self.keys)):
            available = False
            for line in self.queue:
                if not empty(line[i]):
                    available = True
                    break
            if available:
                column_headers.append(self.keys[i].capitalize().replace('_', ' '))
                for j in xrange(len(self.queue)):
                    queue[j] += (self.queue[j][i],)

        s = ''
        if self.display_header and self.header:
            if self.HTML:
                s += '<p>%s</p>' % self.header
            else:
                s += self.header
            s += "\n"
        table = PrettyTable(list(column_headers))
        for column_header in column_headers:
            # API changed in python-prettytable. The try/except is a bad hack to support both versions
            # Note: two versions are not exactly the same...
            # (first one: header in center. Second one: left align for header too)
            try:
                table.set_field_align(column_header, 'l')
            except:
                table.align[column_header] = 'l'
        for line in queue:
            table.add_row(line)

        if self.HTML:
            s += table.get_html_string()
        else:
            s += table.get_string()

        self.queue = []

        return s

    def format_dict(self, item):
        if self.keys is None:
            self.keys = item.keys()
        self.queue.append(item.values())

    def set_header(self, string):
        self.header = string


class HTMLTableFormatter(TableFormatter):
    HTML = True


def test():
    from .iformatter import formatter_test_output as fmt
    assert fmt(TableFormatter, {'foo': 'bar'}) == \
        '+-----+\n' \
        '| Foo |\n' \
        '+-----+\n' \
        '| bar |\n' \
        '+-----+\n'
