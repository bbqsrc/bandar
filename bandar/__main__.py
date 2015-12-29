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
import locale
import logging
import os
import os.path
import sys

from bandar import Bandar
from .archivers import generate_shar, git_list_ports

Target = namedtuple('Target', ['parser', 'handler', 'help', 'needs_overlay'])

DEBUG = False
logging.basicConfig(level=logging.ERROR if DEBUG is False else logging.DEBUG)

logger = logging.getLogger(os.path.basename(__file__))

def success():
    enc = locale.getlocale()[1]
    if enc is not None and enc.upper() == "UTF-8":
        return "\u2713"
    return "PASS"

def failure():
    enc = locale.getlocale()[1]
    if enc is not None and enc.upper() == "UTF-8":
        return "\u2718"
    return "FAIL"

def leaf():
    enc = locale.getlocale()[1]
    if enc is not None and enc.upper() == "UTF-8":
        return "├"
    return "|"

def leaf_end():
    enc = locale.getlocale()[1]
    if enc is not None and enc.upper() == "UTF-8":
        return "└"
    return "\\"

def leaf_arm():
    enc = locale.getlocale()[1]
    if enc is not None and enc.upper() == "UTF-8":
        return "─"
    return "-"

def pipe():
    enc = locale.getlocale()[1]
    if enc is not None and enc.upper() == "UTF-8":
        return "│"
    return "|"

def write(*args):
    sys.stdout.write("".join(args))
    sys.stdout.flush()

def archive_args(p):
    p.add_argument('-o', metavar='path', dest='output_path',
        help='Output path (default: relevant port directory)')
    p.add_argument('ports', nargs='+',
        help="Ports to be archived, provide 'all' to generate all")
    return p

def archive_handler(args):
    out = None

    if args.output_path is not None:
        os.makedirs(args.output_path, exist_ok=True)
        out = args.output_path

    if args.ports[0] == 'all':
        ports = git_list_ports(args.dev_path)
    else:
        ports = args.ports

    for port in ports:
        fn = '%s.shar' % port.replace("/", "_")
        write('[-] ', port, " -> ")
        if out is None:
            shar_path = os.path.join(args.dev_path, port, fn)
        else:
            shar_path = os.path.join(out, fn)
        generate_shar(args.dev_path, port, shar_path)
        print(shar_path)

def check_git_args(p):
    return p

def check_git_handler(args):
    if not os.path.isdir(os.path.join(args.dev_path, '.git')):
        print("[!] ERROR: '%s' is not a git repository." % args.dev_path)
        return 2

    ignore_fn = os.path.join(args.dev_path, '.gitignore')

    reqs = {'work'}
    if not os.path.isfile(ignore_fn):
        print("[!] WARN: You have no .gitignore file!")
    else:
        with open(ignore_fn) as f:
            for line in f:
                if line in reqs:
                    reqs.remove(line)
    if len(reqs) > 0:
        print("[-] For best results, add the following to your .gitignore:")
        print("\n".join(sorted(reqs)))
        return 1

    print("Optimal repository configuration!")

def diff_args(p):
    return p

def diff_handler(args):
    pass

def poudriere_args(p):
    p.add_argument('-j', metavar='jail', dest='jail', required=True,
        help='Jail to use for build')
    p.add_argument('ports', nargs='+',
        help="Ports to be archived, provide 'all' to generate all")
    return p

def poudriere_handler(args, bandar):
    if args.ports[0] == 'all':
        ports = git_list_ports(args.dev_path)
    else:
        ports = args.ports

    print(bandar.bulk_build(args.jail, ports))

def test_args(p):
    p.add_argument('ports', nargs='+',
        help="Ports to be tested, provide 'all' to test all")
    return p

def test_handler(args, bandar):
    if args.ports[0] == 'all':
        ports = git_list_ports(args.dev_path)
    else:
        ports = args.ports

    bandar.test_ports(ports)
    print("Please wait, unmounting overlay...", file=sys.stderr)

def tree_args(p):
    p.add_argument('port', help="Port for which a tree shall be printed")
    return p

def print_tree(nodes, depth=-1, prefix=None):
    if prefix is None:
        prefix = []

    last = len(nodes) - 1
    for i, node in enumerate(nodes):
        p = prefix[:]
        if depth == -1:
            print(node[0])
        elif i == last:
            print(' %s%s%s%s' % (''.join(prefix), leaf_end(), leaf_arm(), node[0]))
            p.append('   ')
        else:
            print(' %s%s%s%s' % (''.join(prefix), leaf(), leaf_arm(), node[0]))
            p.append(' %s ' % pipe())

        print_tree(node[1], depth + 1, p)

def tree_handler(args, bandar):
    port = args.port
    tree = bandar.generate_dependency_tree(port)

    print_tree(tree)

    print("Please wait, unmounting overlay...", file=sys.stderr)

def lint_args(p):
    p.add_argument('ports', nargs='+',
        help="Ports to be tested, provide 'all' to test all")
    return p

def lint_handler(args, bandar):
    if args.ports[0] == 'all':
        ports = git_list_ports(args.dev_path)
    else:
        ports = args.ports

    for port in ports:
        write('[-] %s -> ' % port)
        res = bandar.lint_port(port, '-gAC')
        if len(res.warnings) or len(res.errors):
            print(failure())
            print("\n".join(res.errors + res.warnings))
        else:
            print(success())

    print("Please wait, unmounting overlay...", file=sys.stderr)

commands = {
    'archive': Target(archive_args, archive_handler,
        'Generate archive files, only files committed to git will be detected',
        False),
    #'diff': Target(diff_args, diff_handler,
    #    'Generate diff patches', False),
    'lint': Target(lint_args, lint_handler,
        'Run `portlint` on development ports', True),
    'tree': Target(tree_args, tree_handler,
        'Print dependency tree for a port', True),
    'poudriere': Target(poudriere_args, poudriere_handler,
        'Run `poudriere` on development ports', True),
    'test': Target(test_args, test_handler,
        'Run `port test` on development ports', True),
    'check-git': Target(check_git_args, check_git_handler,
        'Check your git repo is configured optimally', False)
}

def main():
    p = argparse.ArgumentParser(prog='bandar')

    p.add_argument('-d', metavar='dev-ports-path', dest='dev_path',
        default=os.getcwd(),
        help='Directory of project ports (default: current working directory)')
    p.add_argument('-p', metavar='ports-path', dest='ports_path',
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
            bandar = Bandar(args.dev_path, args.ports_path)
            ret = cmd.handler(args, bandar)
        else:
            ret = cmd.handler(args)
        sys.exit(0 if ret is None else ret)
    except KeyboardInterrupt:
        sys.exit(0)
    except ValueError as e:
        print("[!] ERROR: %s" % e)
        sys.exit(1)
    except Exception as e:
        print("[!] An unknown error occurred!")
        if DEBUG:
            raise e
        print(e)
        sys.exit(2)

if __name__ == "__main__":
    main()
