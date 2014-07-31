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


from .base import CapBase, BaseObject, StringField, Field, UserError


__all__ = ['AccountRegisterError', 'Account', 'StatusField', 'CapAccount']


class AccountRegisterError(UserError):
    """
    Raised when there is an error during registration.
    """


class Account(BaseObject):
    """
    Describe an account and its properties.
    """
    login =         StringField('Login')
    password =      StringField('Password')
    properties =    Field('List of key/value properties', dict)

    def __init__(self, id=None):
        BaseObject.__init__(self, id)


class StatusField(object):
    """
    Field of an account status.
    """
    FIELD_TEXT    = 0x001     # the value is a long text
    FIELD_HTML    = 0x002     # the value is HTML formated

    def __init__(self, key, label, value, flags=0):
        self.key = key
        self.label = label
        self.value = value
        self.flags = flags


class CapAccount(CapBase):
    """
    Capability for websites when you can create and manage accounts.

    :var ACCOUNT_REGISTER_PROPERTIES: This class constant may be a list of
                                      :class:`weboob.tools.value.Value` objects.
                                      If the value remains None, weboob considers
                                      that :func:`register_account` isn't supported.
    """
    ACCOUNT_REGISTER_PROPERTIES = None

    @staticmethod
    def register_account(account):
        """
        Register an account on website

        This is a static method, it would be called even if the backend is
        instancied.

        :param account: describe the account to create
        :type account: :class:`Account`
        :raises: :class:`AccountRegisterError`
        """
        raise NotImplementedError()

    def confirm_account(self, mail):
        """
        From an email go to the confirm link.
        """
        raise NotImplementedError()

    def get_account(self):
        """
        Get the current account.
        """
        raise NotImplementedError()

    def update_account(self, account):
        """
        Update the current account.
        """
        raise NotImplementedError()

    def get_account_status(self):
        """
        Get status of the current account.

        :returns: a list of fields
        """
        raise NotImplementedError()
