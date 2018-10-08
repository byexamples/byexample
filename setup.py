# https://packaging.python.org/en/latest/distributing.html
# https://github.com/pypa/sampleproject

from setuptools import setup, find_packages
from codecs import open
from os import path, system

import sys, re

here = path.abspath(path.dirname(__file__))

try:
    system('''pandoc -f markdown-raw_html -o '%(dest_rst)s' '%(src_md)s' ''' % {
                'dest_rst': path.join(here, 'README.rst'),
                'src_md':   path.join(here, 'README.md'),
                })

    with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()

    # strip out any HTML comment|tag
    long_description = re.sub(r'<!--.*?-->', '', long_description,
                                                flags=re.DOTALL|re.MULTILINE)
    long_description = re.sub(r'<img.*?src=.*?>', '', long_description,
                                                flags=re.DOTALL|re.MULTILINE)

    with open(path.join(here, 'README.rst'), 'w', encoding='utf-8') as f:
        f.write(long_description)

except:
    print("Generation of the documentation failed. " + \
          "Do you have 'pandoc' installed?")

    long_description = __doc__

# load __version__, __doc__, _author, _license and _url
exec(open(path.join(here, 'byexample', '__init__.py')).read())

# the following are the required dependencies
# without them, we cannot run byexample
required_deps=[
    'pexpect>=4,<5',    # pexpect 4.x.x required
    'appdirs>=1.4.3<2', # appdirs 1.4.x (x >= 3) required
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
    version=__version__,

    description=__doc__,
    long_description=long_description,

    url=_url,

    # Author details
    author=_author,
    author_email='use-github-issues@example.com',

    license=_license,

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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Ruby',
        'Programming Language :: C++',
        'Programming Language :: Unix Shell',
    ],

    python_requires='>=2.7',
    install_requires=install_deps,

    keywords='doctest documentation test testing',

    packages=['byexample', 'byexample.modules'],

    entry_points={
        'console_scripts': [
            'byexample = byexample.byexample:main',
            ],
        }
)

