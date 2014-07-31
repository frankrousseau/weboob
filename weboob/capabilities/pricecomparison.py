# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
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


from .base import CapBase, BaseObject, Field, DecimalField, \
                  StringField
from .date import DateField

__all__ = ['Shop', 'Price', 'Product', 'CapPriceComparison']


class Product(BaseObject):
    """
    A product.
    """
    name =      StringField('Name of product')


class Shop(BaseObject):
    """
    A shop where the price is.
    """
    name =      StringField('Name of shop')
    location =  StringField('Location of the shop')
    info =      StringField('Information about the shop')


class Price(BaseObject):
    """
    Price.
    """
    date =      DateField('Date when this price has been published')
    cost =      DecimalField('Cost of the product in this shop')
    currency =  StringField('Currency of the price')
    message =   StringField('Message related to this price')
    shop =      Field('Shop information', Shop)
    product =   Field('Product', Product)


class CapPriceComparison(CapBase):
    """
    Capability for price comparison websites.
    """

    def search_products(self, pattern=None):
        """
        Search products from a pattern.

        :param pattern: pattern to search
        :type pattern: str
        :rtype: iter[:class:`Product`]
        """
        raise NotImplementedError()

    def iter_prices(self, product):
        """
        Iter prices for a product.

        :param product: product to search
        :type product: :class:`Product`
        :rtype: iter[:class:`Price`]
        """
        raise NotImplementedError()

    def get_price(self, id):
        """
        Get a price from an ID

        :param id: ID of price
        :type id: str
        :rtype: :class:`Price`
        """
        raise NotImplementedError()
