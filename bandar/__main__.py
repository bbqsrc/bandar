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

import argparse
import atexit
from collections import namedtuple
import logging
import os
import os.path
import sys

from bandar import Bandar

Target = namedtuple('Target', ['parser', 'handler', 'help', 'needs_overlay'])

DEBUG = True
logging.basicConfig(level=logging.ERROR if DEBUG is False else logging.DEBUG)

logger = logging.getLogger(os.path.basename(__file__))


def archive_args(p):
    p.add_argument('-o', metavar='output', dest='output', required=True,
        help="Output directory for archive files")
    p.add_argument('packages', nargs='*',
        help="Packages to be archive'd (default: all)")
    return p

def archive_handler(args, bandar):
    pass

def check_git_args(p):
    return p

def check_git_handler(args):
    print("All good!")
    # TODO check .gitignore contains `work` directories and `.` files

def diff_args(p):
    return p

def diff_handler(args):
    pass

def poudriere_args(p):
    return p

def poudriere_handler(args, bandar):
    pass

def test_args(p):
    p.add_argument('packages', nargs='*',
        help="Packages to be tested (default: all)")
    return p

def test_handler(args, bandar):
    if len(args.packages) > 0:
        bandar.test_ports(args.packages)
        print("Please wait, unmounting overlay...", file=sys.stderr)
    else:
        print("TODO: gen all pkgs")

commands = {
    'archive': Target(archive_args, archive_handler,
        'Generate archive files, only files committed to git will be detected',
        False),
    'diff': Target(diff_args, diff_handler, 'Generate diff patches', False),
    'poudriere': Target(poudriere_args, poudriere_handler,
        'Run poudriere on ports', True),
    'test': Target(test_args, test_handler, 'Run `port test` on ports', True),
    'check-git': Target(check_git_args, check_git_handler,
        'Check your git repo is configured optimally', False)
}

p = argparse.ArgumentParser(prog='bandar')

p.add_argument('-d', metavar='dev-ports', dest='dir',
    default=os.getcwd(),
    help='Directory of project ports (default: current working dir)')
p.add_argument('-p', metavar='ports', dest='ports',
    default='/usr/ports',
    help='Directory of upstream ports (default: /usr/ports)')

sub = p.add_subparsers(dest='command')
for k, target in sorted(commands.items()):
    target.parser(sub.add_parser(k, help=target.help))

args = p.parse_args()
logger.debug(args)

if args.command is None:
    p.print_help()
    sys.exit(0)

cmd = commands[args.command]

try:
    if cmd.needs_overlay:
        bandar = Bandar(args.dir, args.ports)
        ret = cmd.handler(args, bandar)
    else:
        ret = cmd.handler(args)
    sys.exit(0 if ret is None else ret)
except KeyboardInterrupt:
    sys.exit(0)
except ValueError as e:
    print(e)
    sys.exit(1)
except Exception as e:
    print("An unknown error occurred.")
    if DEBUG:
        raise e
    print(e)
    sys.exit(2)
