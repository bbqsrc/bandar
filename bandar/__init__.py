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
import logging
import os
import os.path
import subprocess
import sys
from tempfile import TemporaryDirectory

logger = logging.getLogger(os.path.basename(__file__))


def extend_env(**kwargs):
    env = os.environ.copy()
    env.update(kwargs)
    return env


def check_path(path, rel=None):
    if rel is not None:
        path = os.path.relpath(path, rel)
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

    def __del__(self):
        logging.debug("__del__ %r" % self)
        try:
            subprocess.check_output(['umount', self.mountpoint])
        except OSError as e:
            pass

    def __init__(self, layers, workspace=None, mountpoint=None, max_files=65536):
        ufs_layers = self.__gen_layers(layers)

        self._workspace = workspace or TemporaryDirectory(prefix="bandar-work")
        self._mountpoint = mountpoint or TemporaryDirectory(prefix="bandar-mnt")

        cmd = ['unionfs', '-o', 'cow,max_files=%s' % max_files,
                "%s=RW:%s" % (self.workspace, ufs_layers),
                self.mountpoint]
        logger.debug(cmd)

        subprocess.check_output(cmd)
        atexit.register(self.__del__)

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
        p = subprocess.call(cmd, cwd=port_path, env=env)
        p.wait()
        return p.returncode == 0

    def test_ports(self, port_paths):
        for p in port_paths:
            check_path(p, self.overlay.mountpoint)
        for p in port_paths:
            self.__test_port(p)

    def test_port(self, port_path):
        check_path(port_path, self.overlay.mountpoint)
        self.__test_port(port_path)
