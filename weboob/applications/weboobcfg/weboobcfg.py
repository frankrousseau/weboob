# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Romain Bignon, Christophe Benz
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

from __future__ import print_function

import os
import re

from weboob.capabilities.account import CapAccount
from weboob.core.modules import ModuleLoadError
from weboob.tools.application.repl import ReplApplication
from weboob.tools.ordereddict import OrderedDict
from weboob.tools.application.formatters.iformatter import IFormatter

__all__ = ['WeboobCfg']


class CapabilitiesWrapper(list):
    """
    A wrapper class to keep the list nature of capabilities,
    but provide a comma separated list representation for
    formaters unable to display a list by themselves.

    Useful for having an array representation in JSON and
    comma separated list for simple format.
    """
    def __repr__(self):
        return ', '.join(self)


class ModuleInfoFormatter(IFormatter):
    def format_dict(self, minfo):
        result = '.------------------------------------------------------------------------------.\n'
        result += '| Module %-69s |\n' % minfo['name']
        result += "+-----------------.------------------------------------------------------------'\n"
        result += '| Version         | %s\n' % minfo['version']
        result += '| Maintainer      | %s\n' % minfo['maintainer']
        result += '| License         | %s\n' % minfo['license']
        result += '| Description     | %s\n' % minfo['description']
        result += '| Capabilities    | %s\n' % ', '.join(minfo['capabilities'])
        result += '| Installed       | %s\n' % minfo['installed']
        result += '| Location        | %s\n' % minfo['location']
        if 'config' in minfo:
            first = True
            for key, field in minfo['config'].iteritems():
                label = field['label']
                if field['default'] is not None:
                    label += ' (default: %s)' % field['default']

                if first:
                    result += '|                 | \n'
                    result += '| Configuration   | %s: %s\n' % (key, label)
                    first = False
                else:
                    result += '|                 | %s: %s\n' % (key, label)
        result += "'-----------------'\n"
        return result


class WeboobCfg(ReplApplication):
    APPNAME = 'weboob-config'
    VERSION = '1.1'
    COPYRIGHT = 'Copyright(C) 2010-YEAR Christophe Benz, Romain Bignon'
    DESCRIPTION = "Weboob-Config is a console application to add/edit/remove backends, " \
                  "and to register new website accounts."
    SHORT_DESCRIPTION = "manage backends or register new accounts"
    EXTRA_FORMATTERS = {'info_formatter': ModuleInfoFormatter}
    COMMANDS_FORMATTERS = {'modules':     'table',
                           'list':        'table',
                           'info':        'info_formatter',
                           }
    DISABLE_REPL = True

    def load_default_backends(self):
        pass

    def do_add(self, line):
        """
        add NAME [OPTIONS ...]

        Add a backend.
        """
        if not line:
            print('You must specify a module name. Hint: use the "modules" command.', file=self.stderr)
            return 2
        name, options = self.parse_command_args(line, 2, 1)
        if options:
            options = options.split(' ')
        else:
            options = ()

        params = {}
        # set backend params from command-line arguments
        for option in options:
            try:
                key, value = option.split('=', 1)
            except ValueError:
                print('Parameters have to be formatted "key=value"', file=self.stderr)
                return 2
            params[key] = value

        self.add_backend(name, params)

    def do_register(self, line):
        """
        register MODULE

        Register a new account on a module.
        """
        self.register_backend(line)

    def do_confirm(self, backend_name):
        """
        confirm BACKEND

        For a backend which support CapAccount, parse a confirmation mail
        after using the 'register' command to automatically confirm the
        subscribe.

        It takes mail from stdin. Use it with postfix for example.
        """
        # Do not use the ReplApplication.load_backends() method because we
        # don't want to prompt user to create backend.
        self.weboob.load_backends(names=[backend_name])
        try:
            backend = self.weboob.get_backend(backend_name)
        except KeyError:
            print('Error: backend "%s" not found.' % backend_name, file=self.stderr)
            return 1

        if not backend.has_caps(CapAccount):
            print('Error: backend "%s" does not support accounts management' % backend_name, file=self.stderr)
            return 1

        mail = self.acquire_input()
        if not backend.confirm_account(mail):
            print('Error: Unable to confirm account creation', file=self.stderr)
            return 1
        return 0

    def do_list(self, line):
        """
        list [CAPS ..]

        Show backends.
        """
        caps = line.split()
        for instance_name, name, params in sorted(self.weboob.backends_config.iter_backends()):
            try:
                module = self.weboob.modules_loader.get_or_load_module(name)
            except ModuleLoadError as e:
                self.logger.warning('Unable to load module %r: %s' % (name, e))
                continue

            if caps and not module.has_caps(*caps):
                continue
            row = OrderedDict([('Name', instance_name),
                               ('Module', name),
                               ('Configuration', ', '.join(
                                   '%s=%s' % (key, ('*****' if key in module.config and module.config[key].masked
                                                    else value))
                                   for key, value in params.iteritems())),
                               ])
            self.format(row)

    def do_remove(self, instance_name):
        """
        remove NAME

        Remove a backend.
        """
        if not self.weboob.backends_config.remove_backend(instance_name):
            print('Backend instance "%s" does not exist' % instance_name, file=self.stderr)
            return 1

    def _do_toggle(self, name, state):
        try:
            bname, items = self.weboob.backends_config.get_backend(name)
        except KeyError:
            print('Backend instance "%s" does not exist' % name, file=self.stderr)
            return 1
        self.weboob.backends_config.edit_backend(name, bname, {'_enabled': state})

    def do_enable(self, name):
        """
        enable BACKEND

        Enable a disabled backend
        """
        return self._do_toggle(name, 1)

    def do_disable(self, name):
        """
        disable BACKEND

        Disable a backend
        """
        return self._do_toggle(name, 0)

    def do_edit(self, line):
        """
        edit BACKEND

        Edit a backend
        """
        try:
            self.edit_backend(line)
        except KeyError:
            print('Error: backend "%s" not found' % line, file=self.stderr)
            return 1

    def do_modules(self, line):
        """
        modules [CAPS ...]

        Show available modules.
        """
        caps = line.split()
        for name, info in sorted(self.weboob.repositories.get_all_modules_info(caps).iteritems()):
            row = OrderedDict([('Name', name),
                               ('Capabilities', CapabilitiesWrapper(info.capabilities)),
                               ('Description', info.description),
                               ])
            self.format(row)

    def do_info(self, line):
        """
        info NAME

        Display information about a module.
        """
        if not line:
            print('You must specify a module name. Hint: use the "modules" command.', file=self.stderr)
            return 2

        minfo = self.weboob.repositories.get_module_info(line)
        if not minfo:
            print('Module "%s" does not exist.' % line, file=self.stderr)
            return 1

        try:
            module = self.weboob.modules_loader.get_or_load_module(line)
        except ModuleLoadError:
            module = None

        self.start_format()
        self.format(self.create_minfo_dict(minfo, module))


    def create_minfo_dict(self, minfo, module):
        module_info = {}
        module_info['name'] = minfo.name
        module_info['version'] = minfo.version
        module_info['maintainer'] = minfo.maintainer
        module_info['license'] = minfo.license
        module_info['description'] = minfo.description
        module_info['capabilities'] = minfo.capabilities
        module_info['installed'] = '%s%s' % (('yes' if module else 'no'), ' (new version available)' if self.weboob.repositories.versions.get(minfo.name) > minfo.version else '')
        module_info['location'] = '%s' % (minfo.url or os.path.join(minfo.path, minfo.name))
        if module:
            module_info['config'] = {}
            for key, field in module.config.iteritems():
                module_info['config'][key] = {'label': field.label,
                                              'default': field.default,
                                              'description': field.description,
                                              'regexp': field.regexp,
                                              'choices': field.choices,
                                              'masked': field.masked,
                                              'required': field.required}
        return module_info

    def do_applications(self, line):
        """
        applications

        Show applications.
        """
        applications = set()
        import weboob.applications
        for path in weboob.applications.__path__:
            regexp = re.compile('^%s/([\w\d_]+)$' % path)
            for root, dirs, files in os.walk(path):
                m = regexp.match(root)
                if m and '__init__.py' in files:
                    applications.add(m.group(1))
        print(' '.join(sorted(applications)).encode('utf-8'))

    def do_update(self, line):
        """
        update

        Update weboob.
        """
        self.weboob.update()
