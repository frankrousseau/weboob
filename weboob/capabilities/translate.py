# -*- coding: utf-8 -*-

# Copyright(C) 2012 Lucien Loiseau
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


from .base import CapBase, BaseObject, StringField, UserError


__all__ = ['TranslationFail', 'LanguageNotSupported', 'CapTranslate']


class LanguageNotSupported(UserError):
    """
    Raised when the language is not supported
    """

    def __init__(self, msg='language is not supported'):
        UserError.__init__(self, msg)


class TranslationFail(UserError):
    """
    Raised when no translation matches the given request
    """

    def __init__(self, msg='No Translation Available'):
        UserError.__init__(self, msg)


class Translation(BaseObject):
    """
    Translation.
    """
    lang_src =      StringField('Source language')
    lang_dst =      StringField('Destination language')
    text =          StringField('Translation')


class CapTranslate(CapBase):
    """
    Capability of online translation website to translate word or sentence
    """

    def translate(self, source_language, destination_language, request):
        """
        Perfom a translation.

        :param source_language: language in which the request is written
        :param destination_language: language to translate the request into
        :param request: the sentence to be translated
        :rtype: Translation
        """
        raise NotImplementedError()
