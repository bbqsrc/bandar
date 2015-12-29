# Copyright (c) 2015  Brendan Molloy <brendan+freebsd@bbqsrc.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

import atexit
from collections import namedtuple
import logging
import os
import os.path
import subprocess
import sys
from tempfile import TemporaryDirectory

from .poudriere import Poudriere

logger = logging.getLogger(os.path.basename(__file__))


LintResult = namedtuple('LintResult', ['warnings', 'errors'])


def extend_env(**kwargs):
    env = os.environ.copy()
    env.update(kwargs)
    return env


def check_path(path, rel=None):
    if rel is not None:
        path = os.path.join(rel, path)
    abspath = os.path.abspath(path)
    if os.path.isdir(abspath):
        return abspath
    raise ValueError("The path '%s' does not exist!" % abspath)


class Overlay:
    @property
    def workspace(self):
        return self._workspace.name

    @property
    def mountpoint(self):
        return self._mountpoint.name

    def __init__(self, layers, workspace=None, mountpoint=None, max_files=65536):
        ufs_layers = self.__gen_layers(layers)

        self._workspace = workspace or TemporaryDirectory(prefix="bandar-work-")
        self._mountpoint = mountpoint or TemporaryDirectory(prefix="bandar-mnt-")

        cmd = ['unionfs', '-o', 'cow,max_files=%s' % max_files,
                "%s=RW:%s" % (self.workspace, ufs_layers),
                self.mountpoint]
        logger.debug(cmd)

        subprocess.check_output(cmd)

        self.__unmounted = False
        atexit.register(self.__unmount)

    def __del__(self):
        if self.__unmounted is False:
            self.__unmount()

    def __unmount(self):
        atexit.unregister(self.__unmount)
        subprocess.call(['umount', '-f', self.mountpoint])
        self.__unmounted = True

    def __gen_layers(self, layers):
        abslayers = ["%s=RO" % check_path(layer) for layer in layers]
        return ":".join(abslayers)


class Bandar:
    def __init__(self, proj_dir, ports_dir):
        self.proj_dir = check_path(proj_dir)
        self.ports_dir = check_path(ports_dir)
        self.overlay = Overlay([self.proj_dir, self.ports_dir])

    def __test_port(self, port_path):
        cmd = ['port', 'test']
        env = extend_env(PORTSDIR=self.overlay.mountpoint)
        ret = subprocess.call(cmd, cwd=port_path, env=env)
        return ret == 0

    def test_ports(self, port_paths):
        paths = [check_path(p, self.overlay.mountpoint) for p in port_paths]
        for p in paths:
            self.__test_port(p)

    def test_port(self, port_path):
        p = check_path(port_path, self.overlay.mountpoint)
        self.__test_port(p)

    def bulk_build(self, jail_name, ports):
        p = Poudriere(self.overlay.mountpoint)
        return p.bulk(jail_name, *ports)

    def lint_port(self, port_path, *args):
        mnt = self.overlay.mountpoint
        cmd = ['portlint'] + list(args) + [port_path]
        env = extend_env(PORTSDIR=mnt)

        try:
            data = subprocess.check_output(cmd, cwd=mnt, env=env)
        except subprocess.CalledProcessError as e:
            # if >= 0, just means linting found an error
            if e.returncode >= 0:
                data = e.output
            else:
                # Otherwise, propagate
                raise e

        results = data.decode().strip().split('\n')

        out = LintResult(
            warnings=[x.replace(mnt + '/', '') for x in results if x.startswith("WARN")],
            errors=[x.replace(mnt + '/', '') for x in results if x.startswith("FATAL")])

        return out

    def generate_dependency_tree(self, port_path):
        root = []

        mnt = self.overlay.mountpoint
        path = os.path.join(mnt, port_path)
        cmd = ['make', 'run-depends-list']
        env = extend_env(PORTSDIR=mnt)

        ports = subprocess.check_output(cmd, cwd=path, env=env)\
            .decode().strip().split('\n')

        for port in ports:
            # Strip mnt prefix
            if port.startswith(mnt):
                port = port[len(mnt):]
            root.append((port, self.generate_dependency_tree(port)))

        return root
