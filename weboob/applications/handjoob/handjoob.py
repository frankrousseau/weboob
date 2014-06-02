# -*- coding: utf-8 -*-

# Copyright(C) 2013 Bezleputh
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

from weboob.capabilities.job import ICapJob
from weboob.tools.application.repl import ReplApplication, defaultcount
from weboob.tools.application.formatters.iformatter import IFormatter, PrettyFormatter

__all__ = ['Handjoob']


class JobAdvertFormatter(IFormatter):

    MANDATORY_FIELDS = ('id', 'url', 'publication_date', 'title')

    def format_obj(self, obj, alias):
        result = u'%s%s%s\n' % (self.BOLD, obj.title, self.NC)
        result += 'url: %s\n' % obj.url
        if hasattr(obj, 'publication_date') and obj.publication_date:
            result += 'Publication date : %s\n' % obj.publication_date.strftime('%Y-%m-%d')
        if hasattr(obj, 'place') and obj.place:
            result += 'Location: %s\n' % obj.place
        if hasattr(obj, 'society_name') and obj.society_name:
            result += 'Society : %s\n' % obj.society_name
        if hasattr(obj, 'job_name') and obj.job_name:
            result += 'Job name : %s\n' % obj.job_name
        if hasattr(obj, 'contract_type') and obj.contract_type:
            result += 'Contract : %s\n' % obj.contract_type
        if hasattr(obj, 'pay') and obj.pay:
            result += 'Pay : %s\n' % obj.pay
        if hasattr(obj, 'formation') and obj.formation:
            result += 'Formation : %s\n' % obj.formation
        if hasattr(obj, 'experience') and obj.experience:
            result += 'Experience : %s\n' % obj.experience
        if hasattr(obj, 'description') and obj.description:
            result += 'Description : %s\n' % obj.description
        return result


class JobAdvertListFormatter(PrettyFormatter):
    MANDATORY_FIELDS = ('id', 'title')

    def get_title(self, obj):
        return '%s' % (obj.title)

    def get_description(self, obj):
        result = u''
        if hasattr(obj, 'publication_date') and obj.publication_date:
            result += '\tPublication date : %s\n' % obj.publication_date.strftime('%Y-%m-%d')
        if hasattr(obj, 'place') and obj.place:
            result += '\tLocation: %s\n' % obj.place
        if hasattr(obj, 'society_name') and obj.society_name:
            result += '\tSociety : %s\n' % obj.society_name
        if hasattr(obj, 'contract_type') and obj.contract_type:
            result += '\tContract : %s\n' % obj.contract_type
        return result.strip('\n\t')


class Handjoob(ReplApplication):
    APPNAME = 'handjoob'
    VERSION = '0.j'
    COPYRIGHT = 'Copyright(C) 2012 Bezleputh'
    DESCRIPTION = "Console application to search for a job."
    SHORT_DESCRIPTION = "search for a job"
    CAPS = ICapJob
    EXTRA_FORMATTERS = {'job_advert_list': JobAdvertListFormatter,
                        'job_advert': JobAdvertFormatter,
                        }
    COMMANDS_FORMATTERS = {'search': 'job_advert_list',
                           'ls': 'job_advert_list',
                           'info': 'job_advert',
                           }

    @defaultcount(10)
    def do_search(self, pattern):
        """
        search PATTERN

        Search for an advert  matching a PATTERN.
        """
        self.change_path([u'search'])
        self.start_format(pattern=pattern)
        for backend, job_advert in self.do('search_job', pattern):
            self.cached_format(job_advert)

    @defaultcount(10)
    def do_ls(self, line):
        """
        advanced search

        Search for an advert matching to advanced filters.
        """
        self.change_path([u'advanced'])
        for backend, job_advert in self.do('advanced_search_job'):
            self.cached_format(job_advert)

    def complete_info(self, text, line, *ignored):
        args = line.split(' ')
        if len(args) == 2:
            return self._complete_object()

    def do_info(self, _id):
        """
        info ID

        Get information about an advert.
        """
        if not _id:
            print >>sys.stderr, 'This command takes an argument: %s' % self.get_command_help('info', short=True)
            return 2

        job_advert = self.get_object(_id, 'get_job_advert')

        if not job_advert:
            print >>sys.stderr, 'Job advert not found: %s' % _id
            return 3

        self.start_format()
        self.format(job_advert)
