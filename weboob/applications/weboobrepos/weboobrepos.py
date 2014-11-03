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

from __future__ import print_function

from datetime import datetime
from time import mktime, strptime
import tarfile
import os
import shutil
import subprocess
from copy import copy
from contextlib import closing

from weboob.core.repositories import Repository

from weboob.tools.application.repl import ReplApplication


__all__ = ['WeboobRepos']


class WeboobRepos(ReplApplication):
    APPNAME = 'weboob-repos'
    VERSION = '1.1'
    COPYRIGHT = 'Copyright(C) 2012-YEAR Romain Bignon'
    DESCRIPTION = "Weboob-repos is a console application to manage a Weboob Repository."
    SHORT_DESCRIPTION = "manage a weboob repository"
    COMMANDS_FORMATTERS = {'backends':    'table',
                           'list':        'table',
                           }
    DISABLE_REPL = True

    weboob_commands = copy(ReplApplication.weboob_commands)
    weboob_commands.remove('backends')

    def load_default_backends(self):
        pass

    def do_create(self, line):
        """
        create NAME [PATH]

        Create a new repository. If PATH is missing, create repository
        on the current directory.
        """
        name, path = self.parse_command_args(line, 2, 1)
        if not path:
            path = os.getcwd()
        else:
            path = os.path.realpath(path)

        if not os.path.exists(path):
            os.mkdir(path)
        elif not os.path.isdir(path):
            print(u'"%s" is not a directory' % path)
            return 1

        r = Repository('http://')
        r.name = name
        r.maintainer = self.ask('Enter maintainer of the repository')
        r.save(os.path.join(path, r.INDEX))
        print(u'Repository "%s" created.' % path)

    def do_build(self, line):
        """
        build SOURCE REPOSITORY

        Build backends contained in SOURCE to REPOSITORY.

        Example:
        $ weboob-repos build $HOME/src/weboob/modules /var/www/updates.weboob.org/0.a/
        """
        source_path, repo_path = self.parse_command_args(line, 2, 2)
        index_file = os.path.join(repo_path, Repository.INDEX)

        r = Repository('http://')
        try:
            with open(index_file, 'r') as fp:
                r.parse_index(fp)
        except IOError as e:
            print('Unable to open repository: %s' % e, file=self.stderr)
            print('Use the "create" command before.', file=self.stderr)
            return 1

        r.build_index(source_path, index_file)

        if r.signed:
            sigfiles = [r.KEYRING, Repository.INDEX]
            gpg = self._find_gpg()
            if not gpg:
                raise Exception('Unable to find the gpg executable.')
            krname = os.path.join(repo_path, r.KEYRING)
            if os.path.exists(krname):
                kr_mtime = int(datetime.fromtimestamp(os.path.getmtime(krname)).strftime('%Y%m%d%H%M'))
            if not os.path.exists(krname) or kr_mtime < r.key_update:
                print('Generate keyring')
                # Remove all existing keys
                if os.path.exists(krname):
                    os.remove(krname)
                # Add all valid keys
                for keyfile in os.listdir(os.path.join(source_path, r.KEYDIR)):
                    print('Adding key %s' % keyfile)
                    keypath = os.path.join(source_path, r.KEYDIR, keyfile)
                    subprocess.check_call([
                        gpg,
                        '--no-options',
                        '--quiet',
                        '--no-default-keyring',
                        '--keyring', os.path.realpath(krname),
                        '--import', os.path.realpath(keypath)])
                # Does not make much sense in our case
                if os.path.exists(krname + '~'):
                    os.remove(krname + '~')
                if not os.path.exists(krname):
                    raise Exception('No valid key file found.')
                kr_mtime = mktime(strptime(str(r.key_update), '%Y%m%d%H%M'))
                os.chmod(krname, 0o644)
                os.utime(krname, (kr_mtime, kr_mtime))
            else:
                print('Keyring is up to date')

        for name, module in r.modules.iteritems():
            tarname = os.path.join(repo_path, '%s.tar.gz' % name)
            if r.signed:
                sigfiles.append(os.path.basename(tarname))
            module_path = os.path.join(source_path, name)
            if os.path.exists(tarname):
                tar_mtime = int(datetime.fromtimestamp(os.path.getmtime(tarname)).strftime('%Y%m%d%H%M'))
                if tar_mtime >= module.version:
                    continue

            print('Create archive for %s' % name)
            with closing(tarfile.open(tarname, 'w:gz')) as tar:
                tar.add(module_path, arcname=name, exclude=self._archive_excludes)
            tar_mtime = mktime(strptime(str(module.version), '%Y%m%d%H%M'))
            os.utime(tarname, (tar_mtime, tar_mtime))

            # Copy icon.
            icon_path = os.path.join(module_path, 'favicon.png')
            if os.path.exists(icon_path):
                shutil.copy(icon_path, os.path.join(repo_path, '%s.png' % name))

        if r.signed:
            # Find out which keys are allowed to sign
            fingerprints = [gpgline.strip(':').split(':')[-1]
                            for gpgline
                            in subprocess.Popen([
                                gpg,
                                '--no-options',
                                '--with-fingerprint', '--with-colons',
                                '--list-public-keys',
                                '--no-default-keyring',
                                '--keyring', os.path.realpath(krname)],
                                stdout=subprocess.PIPE).communicate()[0].splitlines()
                            if gpgline.startswith('fpr:')]
            # Find out the first secret key we have that is allowed to sign
            secret_fingerprint = None
            for fingerprint in fingerprints:
                proc = subprocess.Popen([
                    gpg,
                    '--no-options',
                    '--list-secret-keys', fingerprint],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                proc.communicate()
                # if failed
                if proc.returncode:
                    continue
                secret_fingerprint = fingerprint
            if secret_fingerprint is None:
                raise Exception('No suitable secret key found')

            # Check if all files have an up to date signature
            for filename in sigfiles:
                filepath = os.path.realpath(os.path.join(repo_path, filename))
                sigpath = filepath + '.sig'
                file_mtime = int(os.path.getmtime(filepath))
                if os.path.exists(sigpath):
                    sig_mtime = int(os.path.getmtime(sigpath))
                if not os.path.exists(sigpath) or sig_mtime < file_mtime:
                    print('Signing %s' % filename)
                    if os.path.exists(sigpath):
                        os.remove(sigpath)
                    subprocess.check_call([
                        gpg,
                        '--no-options',
                        '--quiet',
                        '--local-user', secret_fingerprint,
                        '--detach-sign',
                        '--output', sigpath,
                        '--sign', filepath])
                    os.utime(sigpath, (file_mtime, file_mtime))
            print('Signatures are up to date')

    @staticmethod
    def _find_gpg():
        if os.getenv('GPG_EXECUTABLE'):
            return os.getenv('GPG_EXECUTABLE')
        paths = os.getenv('PATH', os.defpath).split(os.pathsep)
        for path in paths:
            for ex in ('gpg2', 'gpg'):
                fpath = os.path.join(path, ex)
                if os.path.exists(fpath) and os.access(fpath, os.X_OK):
                    return fpath

    def _archive_excludes(self, filename):
        # Skip *.pyc files in tarballs.
        if filename.endswith('.pyc'):
            return True
        # Don't include *.png files in tarball
        if filename.endswith('.png'):
            return True
        return False
