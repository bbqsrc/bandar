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

import os.path
import subprocess

def git_list_ports(path, *args, **kwargs):
    files = git_ls_files(path, *args, **kwargs)
    o = set()
    for fn in files:
        chunks = fn.split('/')
        if len(chunks) < 2:
            continue
        port = "/".join(chunks[:2])

        if os.path.isdir(os.path.join(path, port)):
            o.add(port)
    return list(sorted(o))

def git_ls_files(path, *args, **kwargs):
    cwd = kwargs.get('cwd', path)
    data = subprocess.check_output(['git', 'ls-files', '-z', path], cwd=cwd,
        *args, **kwargs)
    return [x.decode() for x in data.split(b'\x00')[:-1]]

def generate_shar(git_root, path, output_path):
    files = git_ls_files(path, cwd=git_root)
    data = subprocess.check_output(['shar'] + files, cwd=git_root)
    with open(output_path, 'wb') as f:
        f.write(data)
