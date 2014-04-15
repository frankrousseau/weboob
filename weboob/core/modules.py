# -*- coding: utf-8 -*-

# Copyright(C) 2010-2013 Romain Bignon
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

import os
import imp
import logging

from weboob.tools.backend import BaseBackend
from weboob.tools.log import getLogger


__all__ = ['Module', 'ModulesLoader', 'RepositoryModulesLoader', 'ModuleLoadError']


class ModuleLoadError(Exception):
    def __init__(self, module_name, msg):
        Exception.__init__(self, msg)
        self.module = module_name


class Module(object):
    def __init__(self, package):
        self.logger = getLogger('backend')
        self.package = package
        self.klass = None
        for attrname in dir(self.package):
            attr = getattr(self.package, attrname)
            if isinstance(attr, type) and issubclass(attr, BaseBackend) and attr != BaseBackend:
                self.klass = attr
        if not self.klass:
            raise ImportError('%s is not a backend (no BaseBackend class found)' % package)

    @property
    def name(self):
        return self.klass.NAME

    @property
    def maintainer(self):
        return u'%s <%s>' % (self.klass.MAINTAINER, self.klass.EMAIL)

    @property
    def version(self):
        return self.klass.VERSION

    @property
    def description(self):
        return self.klass.DESCRIPTION

    @property
    def license(self):
        return self.klass.LICENSE

    @property
    def config(self):
        return self.klass.CONFIG

    @property
    def website(self):
        if self.klass.BROWSER and hasattr(self.klass.BROWSER, 'BASEURL') and self.klass.BROWSER.BASEURL:
            return self.klass.BROWSER.BASEURL
        if self.klass.BROWSER and hasattr(self.klass.BROWSER, 'DOMAIN') and self.klass.BROWSER.DOMAIN:
            return '%s://%s' % (self.klass.BROWSER.PROTOCOL, self.klass.BROWSER.DOMAIN)
        else:
            return None

    @property
    def icon(self):
        return self.klass.ICON

    def iter_caps(self):
        return self.klass.iter_caps()

    def has_caps(self, *caps):
        for c in caps:
            if (isinstance(c, basestring) and c in [cap.__name__ for cap in self.iter_caps()]) or \
               (type(c) == type and issubclass(self.klass, c)):
                return True
        return False

    def create_instance(self, weboob, instance_name, config, storage):
        backend_instance = self.klass(weboob, instance_name, config, storage, self.logger)
        self.logger.debug(u'Created backend instance "%s" for backend "%s"' % (instance_name, self.name))
        return backend_instance


class ModulesLoader(object):
    """
    Load modules.
    """
    def __init__(self, path, version=None):
        self.version = version
        self.path = path
        self.loaded = {}
        self.logger = getLogger('modules')

    def get_or_load_module(self, module_name):
        """
        Can raise a ModuleLoadError exception.
        """
        if module_name not in self.loaded:
            self.load_module(module_name)
        return self.loaded[module_name]

    def iter_existing_module_names(self):
        for name in os.listdir(self.path):
            try:
                if '__init__.py' in os.listdir(os.path.join(self.path, name)):
                    yield name
            except OSError:
                # if path/name is not a directory
                continue

    def load_all(self):
        for existing_module_name in self.iter_existing_module_names():
            try:
                self.load_module(existing_module_name)
            except ModuleLoadError as e:
                self.logger.warning(e)

    def load_module(self, module_name):
        if module_name in self.loaded:
            self.logger.debug('Module "%s" is already loaded from %s' % (module_name, self.loaded[module_name].package.__path__[0]))
            return

        path = self.get_module_path(module_name)

        try:
            fp, pathname, description = imp.find_module(module_name, [path])
            try:
                module = Module(imp.load_module(module_name, fp, pathname, description))
            finally:
                if fp:
                    fp.close()
        except Exception as e:
            if logging.root.level == logging.DEBUG:
                self.logger.exception(e)
            raise ModuleLoadError(module_name, e)

        if module.version != self.version:
            raise ModuleLoadError(module_name, "Module requires Weboob %s, but you use Weboob %s. Hint: use 'weboob-config update'"
                                               % (module.version, self.version))

        self.loaded[module_name] = module
        self.logger.debug('Loaded module "%s" from %s' % (module_name, module.package.__path__[0]))

    def get_module_path(self, module_name):
        return self.path

class RepositoryModulesLoader(ModulesLoader):
    """
    Load modules from repositories.
    """
    def __init__(self, repositories):
        super(RepositoryModulesLoader, self).__init__(repositories.modules_dir, repositories.version)
        self.repositories = repositories

    def iter_existing_module_names(self):
        for name in self.repositories.get_all_modules_info().iterkeys():
            yield name

    def get_module_path(self, module_name):
        minfo = self.repositories.get_module_info(module_name)
        if minfo is None:
            raise ModuleLoadError(module_name, 'No such module %s' % module_name)
        if minfo.path is None:
            raise ModuleLoadError(module_name, 'Module %s is not installed' % module_name)

        return minfo.path
