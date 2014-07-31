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


from weboob.capabilities.base import BaseObject, StringField

__all__ = ['StreamInfo']


class StreamInfo(BaseObject):
    """
    Stream related information.
    """
    who = StringField('Who is currently on air')
    what = StringField('What is currently on air')

    def __iscomplete__(self):
        # This volatile information may be reloaded everytimes.
        return False

    def __unicode__(self):
        if self.who:
            return u'%s - %s' % (self.who, self.what)
        else:
            return self.what

