# -*- coding: utf-8 -*-

# Copyright(C) 2010-2011 Romain Bignon
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


from weboob.tools.test import BackendTest
from random import choice


class BNPorcTest(BackendTest):
    MODULE = 'bnporc'

    def test_bank(self):
        l = list(self.backend.iter_accounts())
        if len(l) > 0:
            a = l[0]
            list(self.backend.iter_coming(a))
            list(self.backend.iter_history(a))

    def test_msgs(self):
        threads = list(self.backend.iter_threads())
        thread = self.backend.fillobj(choice(threads), ['root'])
        assert len(thread.root.content)
