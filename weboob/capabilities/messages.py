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


import datetime
import time

from .base import IBaseCap, CapBaseObject, NotLoaded, Field, StringField, \
                  DateField, IntField, UserError


__all__ = ['Thread', 'Message', 'ICapMessages', 'CantSendMessage', 'ICapMessagesPost']


# Message and Thread's attributes refer to themselves, and it isn't possible
# in python, so these base classes are used instead.
class _Message(CapBaseObject):
    """ Base message. """
    pass


class _Thread(CapBaseObject):
    """ Base Thread. """
    pass


class Message(_Message):
    """
    Represents a message read or to send.
    """
    IS_HTML = 0x001          # The content is HTML formatted
    IS_UNREAD = 0x002        # The message is unread
    IS_RECEIVED = 0x004       # The receiver has read this message
    IS_NOT_RECEIVED = 0x008   # The receiver has not read this message

    thread =        Field('Reference to the thread', _Thread)
    title =         StringField('Title of message')
    sender =        StringField('Author of this message')
    receivers =     Field('Receivers of the message', list)
    date =          DateField('Date when the message has been sent')
    content =       StringField('Body of message')
    signature =     StringField('Optional signature')
    parent =        Field('Parent message', _Message)
    children =      Field('Children fields', list)
    flags =         IntField('Flags (IS_* constants)', default=0)

    def __init__(self, thread=NotLoaded,
                       id=NotLoaded,
                       title=NotLoaded,
                       sender=NotLoaded,
                       receivers=NotLoaded,
                       date=None,
                       parent=NotLoaded,
                       content=NotLoaded,
                       signature=NotLoaded,
                       children=NotLoaded,
                       flags=0):
        CapBaseObject.__init__(self, id)
        self.thread = thread
        self.title = title
        self.sender = sender
        self.receivers = receivers
        self.content = content
        self.signature = signature
        self.children = children
        self.flags = flags

        if date is None:
            date = datetime.datetime.utcnow()
        self.date = date

        if isinstance(parent, Message):
            self.parent = parent
        else:
            self.parent = NotLoaded
            self._parent_id = parent

    @property
    def date_int(self):
        """
        Date of message as an integer.
        """
        return int(time.strftime('%Y%m%d%H%M%S', self.date.timetuple()))

    @property
    def full_id(self):
        """
        Full ID of message (in form '**THREAD_ID.MESSAGE_ID**')
        """
        return '%s.%s' % (self.thread.id, self.id)

    @property
    def full_parent_id(self):
        """
        Get the full ID of the parent message (in form '**THREAD_ID.MESSAGE_ID**').
        """
        if self.parent:
            return self.parent.full_id
        elif self._parent_id is None:
            return ''
        elif self._parent_id is NotLoaded:
            return NotLoaded
        else:
            return '%s.%s' % (self.thread.id, self._parent_id)

    def __eq__(self, msg):
        if not isinstance(msg, Message):
            return False

        if self.thread:
            return unicode(self.thread.id) == unicode(msg.thread.id) and \
                   unicode(self.id) == unicode(msg.id)
        else:
            return unicode(self.id) == unicode(msg.id)

    def __repr__(self):
        return '<Message id=%r title=%r date=%r from=%r>' % (
                   self.full_id, self.title, self.date, self.sender)


class Thread(_Thread):
    """
    Thread containing messages.
    """
    IS_THREADS =    0x001
    IS_DISCUSSION = 0x002

    root =      Field('Root message', Message)
    title =     StringField('Title of thread')
    date =      DateField('Date of thread')
    flags =     IntField('Flags (IS_* constants)', default=IS_THREADS)

    def iter_all_messages(self):
        """
        Iter all messages of the thread.

        :rtype: iter[:class:`Message`]
        """
        if self.root:
            yield self.root
            for m in self._iter_all_messages(self.root):
                yield m

    def _iter_all_messages(self, message):
        if message.children:
            for child in message.children:
                yield child
                for m in self._iter_all_messages(child):
                    yield m


class ICapMessages(IBaseCap):
    """
    Capability to read messages.
    """
    def iter_threads(self):
        """
        Iterates on threads, from newers to olders.

        :rtype: iter[:class:`Thread`]
        """
        raise NotImplementedError()

    def get_thread(self, id):
        """
        Get a specific thread.

        :rtype: :class:`Thread`
        """
        raise NotImplementedError()

    def iter_unread_messages(self):
        """
        Iterates on messages which hasn't been marked as read.

        :rtype: iter[:class:`Message`]
        """
        raise NotImplementedError()

    def set_message_read(self, message):
        """
        Set a message as read.

        :param message: message read (or ID)
        :type message: :class:`Message` or str
        """
        raise NotImplementedError()


class CantSendMessage(UserError):
    """
    Raised when a message can't be send.
    """


class ICapMessagesPost(IBaseCap):
    """
    This capability allow user to send a message.
    """
    def post_message(self, message):
        """
        Post a message.

        :param message: message to send
        :type message: :class:`Message`
        :raises: :class:`CantSendMessage`
        """
        raise NotImplementedError()
