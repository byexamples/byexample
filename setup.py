"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

import sys

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# the following are the required dependencies
# without them, we cannot run byexample
required_deps=[
    'pexpect>=4,<5',  # pexpect 4.x.x required
    ]

# these, on the other hand, are optional nice to have
# dependencies. we'll install them by default but if they
# are not present, byexample will run normally.
nice_to_have_deps=[
    'tqdm>=4,<5',     # tqdm 4.x.x required
    'pygments>=2,<3', # pygments 2.x.x required
    ]

# run
# python setup.py install --byexample-minimal
# to install only the required dependencies
if '--byexample-minimal' in sys.argv:
    sys.argv.remove('--byexample-minimal')
    install_deps = required_deps

else:
    install_deps = required_deps + nice_to_have_deps

setup(
    name='byexample',
    version='3.0.0',

    description='Write snippets of code in Python, Ruby, and others as ' +\
                'documentation and execute them as regression tests.',
    long_description=long_description,

    url='https://github.com/eldipa/byexample',

    # Author details
    author='Di Paola Martin',
    author_email='use-github-issues@example.com',

    license='GNU GPLv3',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Testing',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Ruby',
        'Programming Language :: Unix Shell',
    ],

    python_requires='>=2.6',
    install_requires=install_deps,

    keywords='doctest documentation test testing',

    packages=['byexample', 'byexample.modules'],

    entry_points={
        'console_scripts': [
            'byexample = byexample.byexample:main',
            ],
        }
)

