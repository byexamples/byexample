import sys

if not 'sdist' in sys.argv:
    sys.exit('''
*** Please install the `byexample` package instead of `byexamples` (notice the `s` at the end) ***
This is just a dummy package to prevent typo-squashing.

Install `byexample` from PyPI with

  pip install byexample

You can visit the home page and download it manually from

  https://byexamples.github.io/
  https://pypi.org/project/byexample/
''')

from setuptools import setup, find_packages
from codecs import open
from os import path, system

import sys, re

here = path.abspath(path.dirname(__file__))

# load __version__, __doc__, _author, _license and _url
exec(open(path.join(here, '..', 'byexample', '__init__.py')).read())
long_description = __doc__

setup(
    name='byexamples',
    version='0.0',
    description='Dummy package that points to byexample (without s at the end)',
    url=_url,
    author=_author,
    author_email='use-github-issues@example.com',

    license=_license
)
