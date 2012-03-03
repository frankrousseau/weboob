# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon, Florent Fourcot
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


from .base import CapBaseObject
from .collection import ICapCollection, CollectionNotFound


__all__ = ['Subscription', 'SubscriptionNotFound', 'ICapBill', 'Detail']


class SubscriptionNotFound(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Subscription not found'
        Exception.__init__(self, msg)

class Detail(CapBaseObject):
    def __init__(self):
        CapBaseObject.__init__(self, 0)
        self.add_field('label', basestring)
        self.add_field('infos', basestring)
        self.add_field('price', float)

class Subscription(CapBaseObject):
    def __init__(self, id):
        CapBaseObject.__init__(self, id)
        self.add_field('label', basestring)
        self.add_field('subscriber', basestring)

class ICapBill(ICapCollection):
    def iter_resources(self, objs, split_path):
        if Subscription in objs:
            if len(split_path) > 0:
                raise CollectionNotFound(split_path)

            return self.iter_subscription()

    def iter_subscription(self):
        raise NotImplementedError()

    def get_subscription(self, _id):
        raise NotImplementedError()

    def iter_history(self, subscription):
        raise NotImplementedError()

    # XXX : should be an other Cap ? 
    def get_pdf(self, subscription):
        raise NotImplementedError()
  
    def get_details(self, subscription):
        raise NotImplementedError()