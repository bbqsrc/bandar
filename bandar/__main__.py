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
import logging
import os
import os.path
import sys

from bandar import Bandar

DEBUG = True
logging.basicConfig(level=logging.ERROR if DEBUG is False else logging.DEBUG)

logger = logging.getLogger(os.path.basename(__file__))

def check_git(dir):
    print("All good!")
    # TODO check .gitignore contains `work` directories and `.` files
    return 0

commands = {
    'shar': None,
    'poudriere': None,
    'test': None,
    'help': None,
    'check-git': None
}

p = argparse.ArgumentParser(prog='bandar')

p.add_argument('-d', '--directory', metavar='dev-ports', dest='dir',
    default=os.getcwd(),
    help='Directory of project ports (default: current working dir)')
p.add_argument('-p', '--ports-dir', metavar='ports', dest='ports',
    default='/usr/ports',
    help='Directory of upstream ports (default: /usr/ports)')
p.add_argument('command',
    help="Command to run. (%s)" % ", ".join(sorted(commands.keys())))
p.add_argument('packages', nargs='*',
    help='Packages to run command upon (default: all)')

args = p.parse_args()
logger.debug(args)
cmd = args.command
pkgs = args.packages

if cmd == 'help':
    if len(pkgs) == 0:
        print("You must provide a command to receive help.")
        sys.exit(1)
    print("No help for '%s'." % pkgs[0])
    sys.exit(0)

elif cmd == 'check-git':
    sys.exit(check_git(args.dir))

try:
    atexit.register(lambda x: print("Please wait, unmounting overlay..."))
    bandar = Bandar(args.dir, args.ports)
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

if cmd == 'test':
    if len(pkgs) > 0:
        bandar.test_ports(pkgs)
        sys.exit(0)
    else:
        print("TODO: gen all pkgs")

print("Command '%s' unknown." % cmd)
sys.exit(1)
