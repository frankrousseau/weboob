# -*- coding: utf-8 -*-

# Copyright(C) 2010-2012 Romain Bignon, Laurent Bachelier
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
import imp
import tarfile
import posixpath
import shutil
import re
import sys
import os
import subprocess
import hashlib
from tempfile import NamedTemporaryFile
from datetime import datetime
from contextlib import closing
from compileall import compile_dir
from io import BytesIO

from .modules import Module
from weboob.tools.log import getLogger
from weboob.tools.misc import to_unicode
from weboob.tools.browser2.browser import BaseBrowser, Weboob as WeboobProfile
from requests.exceptions import HTTPError
try:
    from configparser import RawConfigParser, DEFAULTSECT
except ImportError:
    from ConfigParser import RawConfigParser, DEFAULTSECT


__all__ = ['IProgress', 'ModuleInstallError', 'ModuleInfo', 'RepositoryUnavailable',
           'Repository', 'Versions', 'Repositories', 'InvalidSignature', 'Keyring']


class ModuleInfo(object):
    """
    Information about a module available on a repository.
    """
    def __init__(self, name):
        self.name = name

        # path to the local directory containing this module.
        self.path = None
        self.url = None
        self.repo_url = None

        self.version = 0
        self.capabilities = ()
        self.description = u''
        self.maintainer = u''
        self.license = u''
        self.icon = u''
        self.urls = u''

    def load(self, items):
        self.version = int(items['version'])
        self.capabilities = items['capabilities'].split()
        self.description = to_unicode(items['description'])
        self.maintainer = to_unicode(items['maintainer'])
        self.license = to_unicode(items['license'])
        self.icon = items['icon'].strip() or None
        self.urls = items['urls']

    def has_caps(self, caps):
        if not isinstance(caps, (list, tuple)):
            caps = [caps]
        for c in caps:
            if type(c) == type:
                c = c.__name__
            if c in self.capabilities:
                return True
        return False

    def is_installed(self):
        return self.path is not None

    def is_local(self):
        return self.url is None

    def dump(self):
        return (('version', self.version),
                ('capabilities', ' '.join(self.capabilities)),
                ('description', self.description),
                ('maintainer', self.maintainer),
                ('license', self.license),
                ('icon', self.icon or ''),
                ('urls', self.urls),
               )


class RepositoryUnavailable(Exception):
    """
    Repository in not available.
    """


class Repository(object):
    """
    Represents a repository.
    """
    INDEX = 'modules.list'
    KEYDIR = '.keys'
    KEYRING = 'trusted.gpg'

    def __init__(self, url):
        self.url = url
        self.name = u''
        self.update = 0
        self.maintainer = u''
        self.local = None
        self.signed = False
        self.key_update = 0

        self.modules = {}

        if self.url.startswith('file://'):
            self.local = True
        elif re.match('https?://.*', self.url):
            self.local = False
        else:
            # This is probably a file in ~/.weboob/repositories/, we
            # don't know if this is a local or a remote repository.
            with open(self.url, 'r') as fp:
                self.parse_index(fp)

    def __repr__(self):
        return '<Repository %r>' % self.name

    def localurl2path(self):
        """
        Get a local path of a file:// URL.
        """
        assert self.local is True

        if self.url.startswith('file://'):
            return self.url[len('file://'):]
        return self.url

    def retrieve_index(self, browser, repo_path):
        """
        Retrieve the index file of this repository. It can use network
        if this is a remote repository.

        :param repo_path: path to save the downloaded index file.
        :type repo_path: str
        """
        if self.local:
            # Repository is local, open the file.
            filename = os.path.join(self.localurl2path(), self.INDEX)
            try:
                fp = open(filename, 'r')
            except IOError as e:
                # This local repository doesn't contain a built modules.list index.
                self.name = Repositories.url2filename(self.url)
                self.build_index(self.localurl2path(), filename)
                fp = open(filename, 'r')
        else:
            # This is a remote repository, download file
            try:
                fp = BytesIO(browser.open(posixpath.join(self.url, self.INDEX)).content)
            except HTTPError as e:
                raise RepositoryUnavailable(unicode(e))

        self.parse_index(fp)

        if self.local:
            # Always rebuild index of a local repository.
            self.build_index(self.localurl2path(), filename)

        # Save the repository index in ~/.weboob/repositories/
        self.save(repo_path, private=True)

    def retrieve_keyring(self, browser, keyring_path):
        # ignore local
        if self.local:
            return

        keyring = Keyring(keyring_path)
        # prevent previously signed repos from going unsigned
        if not self.signed and keyring.exists():
            raise RepositoryUnavailable('Previously signed repository can not go unsigned')
        if not self.signed:
            return

        if not keyring.exists() or self.key_update > keyring.version:
            # This is a remote repository, download file
            try:
                keyring_data = browser.open(posixpath.join(self.url, self.KEYRING)).content
                sig_data = browser.open(posixpath.join(self.url, self.KEYRING + '.sig')).content
            except HTTPError as e:
                raise RepositoryUnavailable(unicode(e))
            if keyring.exists():
                if not keyring.is_valid(keyring_data, sig_data):
                    raise InvalidSignature('the keyring itself')
                print('The keyring was updated (and validated by the previous one).')
            else:
                print('First time saving the keyring, blindly accepted.')
            keyring.save(keyring_data, self.key_update)
            print(keyring)

    def parse_index(self, fp):
        """
        Parse index of a repository

        :param fp: file descriptor to read
        :type fp: buffer
        """
        config = RawConfigParser()
        config.readfp(fp)

        # Read default parameters
        items = dict(config.items(DEFAULTSECT))
        try:
            self.name = items['name']
            self.update = int(items['update'])
            self.maintainer = items['maintainer']
            self.signed = bool(int(items.get('signed', '0')))
            self.key_update = int(items.get('key_update', '0'))
        except KeyError as e:
            raise RepositoryUnavailable('Missing global parameters in repository: %s' % e)
        except ValueError as e:
            raise RepositoryUnavailable('Incorrect value in repository parameters: %s' % e)

        if len(self.name) == 0:
            raise RepositoryUnavailable('Name is empty')

        if 'url' in items:
            self.url = items['url']
            self.local = self.url.startswith('file://')
        elif self.local is None:
            raise RepositoryUnavailable('Missing "url" key in settings')

        # Load modules
        self.modules.clear()
        for section in config.sections():
            module = ModuleInfo(section)
            module.load(dict(config.items(section)))
            if not self.local:
                module.url = posixpath.join(self.url, '%s.tar.gz' % module.name)
                module.repo_url = self.url
                module.signed = self.signed
            self.modules[section] = module

    def build_index(self, path, filename):
        """
        Rebuild index of modules of repository.

        :param path: path of the repository
        :type path: str
        :param filename: file to save index
        :type filename: str
        """
        print('Rebuild index')
        self.modules.clear()

        if os.path.isdir(os.path.join(path, self.KEYDIR)):
            self.signed = True
            self.key_update = self.get_tree_mtime(os.path.join(path, self.KEYDIR), True)
        else:
            self.signed = False
            self.key_update = 0

        for name in sorted(os.listdir(path)):
            module_path = os.path.join(path, name)
            if not os.path.isdir(module_path) or '.' in name or name == self.KEYDIR:
                continue

            try:
                fp, pathname, description = imp.find_module(name, [path])
                try:
                    module = Module(imp.load_module(name, fp, pathname, description))
                finally:
                    if fp:
                        fp.close()
            except Exception as e:
                print('Unable to build module %s: [%s] %s' % (name, type(e).__name__, e), file=sys.stderr)
            else:
                m = ModuleInfo(module.name)
                m.version = self.get_tree_mtime(module_path)
                m.capabilities = list(set([c.__name__ for c in module.iter_caps()]))
                m.description = module.description
                m.maintainer = module.maintainer
                m.license = module.license
                m.icon = module.icon or ''
                self.modules[module.name] = m

        self.update = int(datetime.now().strftime('%Y%m%d%H%M'))
        self.save(filename)

    @staticmethod
    def get_tree_mtime(path, include_root=False):
        mtime = 0
        if include_root:
            mtime = int(datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y%m%d%H%M'))
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith('.pyc'):
                    continue
                m = int(datetime.fromtimestamp(os.path.getmtime(os.path.join(root, f))).strftime('%Y%m%d%H%M'))
                mtime = max(mtime, m)

        return mtime

    def save(self, filename, private=False):
        """
        Save repository into a file (modules.list for example).

        :param filename: path to file to save repository.
        :type filename: str
        :param private: if enabled, save URL of repository.
        :type private: bool
        """
        config = RawConfigParser()
        config.set(DEFAULTSECT, 'name', self.name)
        config.set(DEFAULTSECT, 'update', self.update)
        config.set(DEFAULTSECT, 'maintainer', self.maintainer)
        config.set(DEFAULTSECT, 'signed', int(self.signed))
        config.set(DEFAULTSECT, 'key_update', self.key_update)
        if private:
            config.set(DEFAULTSECT, 'url', self.url)

        for module in self.modules.itervalues():
            config.add_section(module.name)
            for key, value in module.dump():
                config.set(module.name, key, to_unicode(value).encode('utf-8'))

        with open(filename, 'wb') as f:
            config.write(f)


class Versions(object):
    VERSIONS_LIST = 'versions.list'

    def __init__(self, path):
        self.path = path
        self.versions = {}

        try:
            with open(os.path.join(self.path, self.VERSIONS_LIST), 'r') as fp:
                config = RawConfigParser()
                config.readfp(fp)

                # Read default parameters
                for key, value in config.items(DEFAULTSECT):
                    self.versions[key] = int(value)
        except IOError:
            pass

    def get(self, name):
        return self.versions.get(name, None)

    def set(self, name, version):
        self.versions[name] = int(version)
        self.save()

    def save(self):
        config = RawConfigParser()
        for name, version in self.versions.iteritems():
            config.set(DEFAULTSECT, name, version)
        with open(os.path.join(self.path, self.VERSIONS_LIST), 'wb') as fp:
            config.write(fp)


class IProgress(object):
    def progress(self, percent, message):
        print('=== [%3.0f%%] %s' % (percent*100, message))

    def error(self, message):
        print('ERROR: %s' % message, file=sys.stderr)


class ModuleInstallError(Exception):
    pass


DEFAULT_SOURCES_LIST = \
"""# List of Weboob repositories
#
# The entries below override the entries above (with
# backends of the same name).

http://updates.weboob.org/%(version)s/main/

# DEVELOPMENT
# If you want to hack on Weboob modules, you may add a
# reference to sources, for example:
#file:///home/rom1/src/weboob/modules/
"""


class Repositories(object):
    SOURCES_LIST = 'sources.list'
    MODULES_DIR = 'modules'
    REPOS_DIR = 'repositories'
    KEYRINGS_DIR = 'keyrings'
    ICONS_DIR = 'icons'

    SHARE_DIRS = [MODULES_DIR, REPOS_DIR, KEYRINGS_DIR, ICONS_DIR]

    def __init__(self, workdir, datadir, version):
        self.logger = getLogger('repositories')
        self.version = version

        class WeboobBrowser(BaseBrowser):
            PROFILE = WeboobProfile(version)

        self.browser = WeboobBrowser()

        self.workdir = workdir
        self.datadir = datadir
        self.sources_list = os.path.join(self.workdir, self.SOURCES_LIST)
        self.modules_dir = os.path.join(self.datadir, self.MODULES_DIR, self.version)
        self.repos_dir = os.path.join(self.datadir, self.REPOS_DIR)
        self.keyrings_dir = os.path.join(self.datadir, self.KEYRINGS_DIR)
        self.icons_dir = os.path.join(self.datadir, self.ICONS_DIR)

        self.create_dir(self.datadir)
        self.create_dir(self.modules_dir)
        self.create_dir(self.repos_dir)
        self.create_dir(self.keyrings_dir)
        self.create_dir(self.icons_dir)

        self.versions = Versions(self.modules_dir)

        self.repositories = []

        if not os.path.exists(self.sources_list):
            with open(self.sources_list, 'w') as f:
                f.write(DEFAULT_SOURCES_LIST)
            self.update()
        else:
            self.load()

    def create_dir(self, name):
        if not os.path.exists(name):
            os.makedirs(name)
        elif not os.path.isdir(name):
            self.logger.error(u'"%s" is not a directory' % name)

    def _extend_module_info(self, repo, info):
        if repo.local:
            info.path = repo.localurl2path()
        elif self.versions.get(info.name) is not None:
            info.path = self.modules_dir

        return info

    def get_all_modules_info(self, caps=None):
        """
        Get all ModuleInfo instances available.

        :param caps: filter on capabilities:
        :type caps: list[str]
        :rtype: dict[:class:`ModuleInfo`]
        """
        modules = {}
        for repos in reversed(self.repositories):
            for name, info in repos.modules.iteritems():
                if not name in modules and (not caps or info.has_caps(caps)):
                    modules[name] = self._extend_module_info(repos, info)
        return modules

    def get_module_info(self, name):
        """
        Get ModuleInfo object of a module.

        It tries all repositories from last to first, and set
        the 'path' attribute of ModuleInfo if it is installed.
        """
        for repos in reversed(self.repositories):
            if name in repos.modules:
                m = repos.modules[name]
                self._extend_module_info(repos, m)
                return m
        return None

    def load(self):
        """
        Load repositories from ~/.local/share/weboob/repositories/.
        """
        self.repositories = []
        for name in sorted(os.listdir(self.repos_dir)):
            path = os.path.join(self.repos_dir, name)
            try:
                repository = Repository(path)
                self.repositories.append(repository)
            except RepositoryUnavailable as e:
                print('Unable to load repository %s (%s), try to update repositories.' % (name, e), file=sys.stderr)

    def get_module_icon_path(self, module):
        return os.path.join(self.icons_dir, '%s.png' % module.name)

    def retrieve_icon(self, module):
        """
        Retrieve the icon of a module and save it in ~/.local/share/weboob/icons/.
        """
        if not isinstance(module, ModuleInfo):
            module = self.get_module_info(module)

        dest_path = self.get_module_icon_path(module)

        icon_url = module.icon
        if not icon_url:
            if module.is_local():
                icon_path = os.path.join(module.path, module.name, 'favicon.png')
                if module.path and os.path.exists(icon_path):
                    shutil.copy(icon_path, dest_path)
                return
            else:
                icon_url = module.url.replace('.tar.gz', '.png')

        try:
            icon = self.browser.open(icon_url)
        except HTTPError:
            pass  # no icon, no problem
        else:
            with open(dest_path, 'wb') as fp:
                fp.write(icon.content)

    def _parse_source_list(self):
        l = []
        with open(self.sources_list, 'r') as f:
            for line in f:
                line = line.strip() % {'version': self.version}
                m = re.match('(file|https?)://.*', line)
                if m:
                    l.append(line)
        return l

    def update_repositories(self, progress=IProgress()):
        """
        Update list of repositories by downloading them
        and put them in ~/.local/share/weboob/repositories/.

        :param progress: observer object.
        :type progress: :class:`IProgress`
        """
        self.repositories = []
        for name in os.listdir(self.repos_dir):
            os.remove(os.path.join(self.repos_dir, name))

        gpgv = Keyring.find_gpgv()
        for line in self._parse_source_list():
            progress.progress(0.0, 'Getting %s' % line)
            repository = Repository(line)
            filename = self.url2filename(repository.url)
            prio_filename = '%02d-%s' % (len(self.repositories), filename)
            repo_path = os.path.join(self.repos_dir, prio_filename)
            keyring_path = os.path.join(self.keyrings_dir, filename)
            try:
                repository.retrieve_index(self.browser, repo_path)
                if gpgv:
                    repository.retrieve_keyring(self.browser, keyring_path)
                else:
                    progress.error('Cannot find gpgv to check for repository authenticity.\n'
                                    'You should install GPG for better security.')
            except RepositoryUnavailable as e:
                progress.error('Unable to load repository: %s' % e)
            else:
                self.repositories.append(repository)

    def check_repositories(self):
        """
        Check if sources.list is consistent with repositories
        """
        l = []
        for line in self._parse_source_list():
            repository = Repository(line)
            filename = self.url2filename(repository.url)
            prio_filename = '%02d-%s' % (len(l), filename)
            repo_path = os.path.join(self.repos_dir, prio_filename)
            if not os.path.isfile(repo_path):
                return False
            l.append(repository)
        return True

    def update(self, progress=IProgress()):
        """
        Update repositories and install new packages versions.

        :param progress: observer object.
        :type progress: :class:`IProgress`
        """
        self.update_repositories()

        to_update = []
        for name, info in self.get_all_modules_info().iteritems():
            if not info.is_local() and info.is_installed():
                to_update.append(info)

        class InstallProgress(IProgress):
            def __init__(self, n):
                self.n = n

            def progress(self, percent, message):
                progress.progress(float(self.n)/len(to_update) + 1.0/len(to_update)*percent, message)

        for n, info in enumerate(to_update):
            inst_progress = InstallProgress(n)
            try:
                self.install(info, inst_progress)
            except ModuleInstallError as e:
                inst_progress.progress(1.0, unicode(e))

    def install(self, module, progress=IProgress()):
        """
        Install a module.

        :param module: module to install
        :type module: :class:`str` or :class:`ModuleInfo`
        :param progress: observer object
        :type progress: :class:`IProgress`
        """
        if isinstance(module, ModuleInfo):
            info = module
        elif isinstance(module, basestring):
            progress.progress(0.0, 'Looking for module %s' % module)
            info = self.get_module_info(module)
            if not info:
                raise ModuleInstallError('Module "%s" does not exist' % module)
        else:
            raise ValueError('"module" parameter might be a ModuleInfo object or a string, not %r' % module)

        module = info

        if module.is_local():
            raise ModuleInstallError('%s is available on local.' % module.name)

        module_dir = os.path.join(self.modules_dir, module.name)
        installed = self.versions.get(module.name)
        if installed is None or not os.path.exists(module_dir):
            progress.progress(0.3, 'Module %s is not installed yet' % module.name)
        elif module.version > installed:
            progress.progress(0.3, 'A new version of %s is available' % module.name)
        else:
            raise ModuleInstallError('The latest version of %s is already installed' % module.name)

        progress.progress(0.2, 'Downloading module...')
        try:
            tardata = self.browser.open(module.url).content
        except HTTPError as e:
            raise ModuleInstallError('Unable to fetch module: %s' % e)

        # Check signature
        if module.signed and Keyring.find_gpgv():
            progress.progress(0.5, 'Checking module authenticity...')
            sig_data = self.browser.open(posixpath.join(module.url + '.sig')).content
            keyring_path = os.path.join(self.keyrings_dir, self.url2filename(module.repo_url))
            keyring = Keyring(keyring_path)
            if not keyring.exists():
                raise ModuleInstallError('No keyring found, please update repos.')
            if not keyring.is_valid(tardata, sig_data):
                raise ModuleInstallError('Invalid signature for %s.' % module.name)

        # Extract module from tarball.
        if os.path.isdir(module_dir):
            shutil.rmtree(module_dir)
        progress.progress(0.7, 'Setting up module...')
        with closing(tarfile.open('', 'r:gz', BytesIO(tardata))) as tar:
            tar.extractall(self.modules_dir)
        if not os.path.isdir(module_dir):
            raise ModuleInstallError('The archive for %s looks invalid.' % module.name)
        # Precompile
        compile_dir(module_dir, quiet=True)

        self.versions.set(module.name, module.version)

        progress.progress(0.9, 'Downloading icon...')
        self.retrieve_icon(module)

        progress.progress(1.0, 'Module %s has been installed!' % module.name)

    @staticmethod
    def url2filename(url):
        """
        Get a safe file name for an URL.

        All non-alphanumeric characters are replaced by _.
        """
        return ''.join([l if l.isalnum() else '_' for l in url])


class InvalidSignature(Exception):
    def __init__(self, filename):
        self.filename = filename
        Exception.__init__(self, 'Invalid signature for %s' % filename)


class Keyring(object):
    EXTENSION = '.gpg'

    def __init__(self, path):
        self.path = path + self.EXTENSION
        self.vpath = path + '.version'
        self.version = 0

        if self.exists():
            with open(self.vpath, 'r') as f:
                self.version = int(f.read().strip())
        else:
            if os.path.exists(self.path):
                os.remove(self.path)
            if os.path.exists(self.vpath):
                os.remove(self.vpath)

    def exists(self):
        if not os.path.exists(self.vpath):
            return False
        if os.path.exists(self.path):
            # Check the file is not empty.
            # This is because there was a bug creating empty keyring files.
            with open(self.path, 'r') as fp:
                if len(fp.read().strip()):
                    return True
        return False

    def save(self, keyring_data, version):
        with open(self.path, 'wb') as fp:
            fp.write(keyring_data)
        self.version = version
        with open(self.vpath, 'wb') as fp:
            fp.write(str(version))

    @staticmethod
    def find_gpgv():
        if os.getenv('GPGV_EXECUTABLE'):
            return os.getenv('GPGV_EXECUTABLE')
        paths = os.getenv('PATH', os.defpath).split(os.pathsep)
        for path in paths:
            for ex in ('gpgv2', 'gpgv'):
                fpath = os.path.join(path, ex)
                if os.path.exists(fpath) and os.access(fpath, os.X_OK):
                    return fpath

    def is_valid(self, data, sigdata):
        """
        Check if the data is signed by an accepted key.
        data and sigdata should be strings.
        """
        gpgv = self.find_gpgv()
        with NamedTemporaryFile(suffix='.sig') as sigfile:
            sigfile.write(sigdata)
            sigfile.flush()  # very important
            assert isinstance(data, basestring)
            # Yes, all of it is necessary
            proc = subprocess.Popen([gpgv,
                    '--status-fd', '1',
                    '--keyring', os.path.realpath(self.path),
                    os.path.realpath(sigfile.name),
                    '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            out, err = proc.communicate(data)
            if proc.returncode or 'GOODSIG' not in out or 'VALIDSIG' not in out:
                print(out, err, file=sys.stderr)
                return False
        return True

    def __str__(self):
        if self.exists():
            with open(self.vpath, 'r') as f:
                h = hashlib.sha1(f.read()).hexdigest()
            return 'Keyring version %s, checksum %s' % (self.version, h)
        return 'NO KEYRING'
