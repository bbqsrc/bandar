bandar
======

Create development overlays for the ports tree.

Bandar creates a temporary unionfs overlay with your development tree on
top and the upstream ports tree on the bottom, allowing you to quickly
and easily test, develop and deploy new ports. Bandar takes advantage of
the fuse-based unionfs copy-on-write feature unavailable in the kernel
variant, and provides extra security and stability by running in
userspace.

The word `"bandar" <https://en.wikipedia.org/wiki/Bandar_(port)>`__ is
Persian for a port or haven, etymologically meaning an enclosed area.

Usage
-----

::

    usage: bandar [-h] [-d dev-ports-path] [-p ports-path]
                  {archive,check-git,lint,poudriere,test} ...

    positional arguments:
      {archive,check-git,lint,poudriere,test}
        archive             Generate archive files, only files committed to git
                            will be detected
        check-git           Check your git repo is configured optimally
        lint                Run `portlint` on development ports
        poudriere           Run `poudriere` on development ports
        test                Run `port test` on development ports

    optional arguments:
      -h, --help            show this help message and exit
      -d dev-ports-path     Directory of project ports (default: current working
                            directory)
      -p ports-path         Directory of upstream ports (default: /usr/ports)

Requirements
------------

-  ``devel/git``
-  ``lang/python32`` or greater
-  ``ports-mgmt/porttools``
-  ``ports-mgmt/poudriere``
-  ``sysutils/fusefs-unionfs>=1.0``

License
-------

BSD 2-clause. See LICENSE.
