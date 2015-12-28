from setuptools import setup, find_packages

with open('README.md') as f:
    desc = f.read()

setup(
    name = "bandar",
    version = "0.0.0",
    packages = find_packages(),
    author = "Brendan Molloy",
    author_email = "brendan+pypi@bbqsrc.net",
    description = "Create development overlays for the FreeBSD ports tree",
    license = "BSD-2-Clause",
    keywords = "freebsd ports poudriere git",
    url = "https://github.com/bbqsrc/bandar/",
    long_description=desc,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Archiving :: Packaging",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: BSD :: FreeBSD",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
    ],
    entry_points = {
        'console_scripts': [
            'bandar = bandar.__main__:main'
        ]
    }
)
