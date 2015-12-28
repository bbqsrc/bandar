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
import subprocess
from tempfile import NamedTemporaryFile
import uuid

class Poudriere:
    def __init__(self, ports_path, name=None):
        self.__cleaned = False

        self.name = name or uuid.uuid4().hex
        self.ports_path = ports_path

        subprocess.check_output(['poudriere', 'ports', '-c', '-F', '-f',
            'none', '-M', self.ports_path, '-p', self.name])
        atexit.register(self.__cleanup)

    def __del__(self):
        if not self.__cleaned:
            self.__cleanup()

    def __cleanup(self):
        atexit.unregister(self.__cleanup)
        subprocess.call(['poudriere', 'ports', '-d', '-k', '-p', self.name])
        self.__cleaned = True

    def bulk(self, jail_name, *args):
        build = uuid.uuid4().hex

        with NamedTemporaryFile('w', prefix='bandar-bulk-%s-' % build) as f:
            for arg in args:
                f.write("%s\n" % arg)
            f.flush()
            subprocess.call(['poudriere', 'bulk', '-C', '-j', jail_name,
                '-p', self.name, '-B', build, '-f', f.name])

        return build
