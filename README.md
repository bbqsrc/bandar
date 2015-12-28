# bandar

Create development overlays for the ports tree

## Usage

```
usage: bandar [-h] [-d dev-ports-path] [-p ports-path]
              {archive,check-git,diff,poudriere,test} ...

positional arguments:
  {archive,check-git,diff,poudriere,test}
    archive             Generate archive files, only files committed to git
                        will be detected
    check-git           Check your git repo is configured optimally
    diff                Generate diff patches
    poudriere           Run `poudriere` on development ports
    test                Run `port test` on development ports

optional arguments:
  -h, --help            show this help message and exit
  -d dev-ports-path     Directory of project ports (default: current working
                        directory)
  -p ports-path         Directory of upstream ports (default: /usr/ports)
```

## License

BSD 2-clause. See LICENSE.
