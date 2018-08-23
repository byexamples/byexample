# https://packaging.python.org/en/latest/distributing.html
# https://github.com/pypa/sampleproject

from setuptools import setup, find_packages
from codecs import open
from os import path, system

import sys

here = path.abspath(path.dirname(__file__))

try:
    system('''pandoc -o '%(dest_rst)s' '%(src_md)s' ''' % {
                'dest_rst': path.join(here, 'README.rst'),
                'src_md':   path.join(here, 'README.md'),
                })
except:
    print("Generation of the documentation failed. " + \
          "Do you have 'pandoc' installed?")

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# hack: this is a workaround for a limitation of pandoc
# the README.md (markdown) has raw html code that it is not
# copied into the README.rst file (reStructuredText)
try:
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        orig_descr = f.read()

    t1 = r'<!-- demo.gif begin -->'
    t2 = r'<!-- demo.gif end -->'

    p1 = long_description.find(t1)
    p2 = long_description.find(t2)
    o1 = orig_descr.find(t1)
    o2 = orig_descr.find(t2)
    if p1 < 0 or p2 < 0 or p1 >= p2 or o1 < 0 or o2 < 0 or o1 >= o2:
        raise Exception("Invalid state for README* (workaround failed). " \
                        ".md's positions (%i, %i); .rst's positions (%i, %i)."
                            % (o1, o2, p1, p2))

    raw_html = orig_descr[o1+len(t1):o2].strip()
    if not raw_html:
        raise Exception("Invalid state for README* (workaround failed). " \
                        ".md's html (%i bytes)."
                            % (len(raw_html)))

    long_description = long_description[:p1] + raw_html + '\n' + \
                       long_description[p2+len(t2):]

    with open(path.join(here, 'README.rst'), 'w', encoding='utf-8') as f:
        f.write(long_description)

except Exception as ex:
    print("Documentation fix failed: %s" % str(ex))

#
# god forgive me for that hack
#
########


# load __version__, __doc__, _author, _license and _url
exec(open(path.join(here, 'byexample', '__init__.py')).read())

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

