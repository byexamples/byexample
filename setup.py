"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

#with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
#    long_description = f.read() # TODO XXX -----------
long_description = 'bla'

setup(
    name='byexample',
    version='1.0.0',

    description='Write snippets of code as documentation and execute them ' +\
                'as tests. Execute your docs!.',
    long_description=long_description,

    url='https://github.com/XXXXXXXXXXXXXXXXXXXXXXX', # TODO XXX -----------

    # Author details
    author='Di Paola Martin',
    author_email='no-email@example.com',

    license='GNU LGPLv3', # TODO XXX also add a LICENSE file

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Testing',

        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)', # TODO XXX------------

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Ruby',
        'Programming Language :: Unix Shell',
    ],

    python_requires='>=2.6',
    install_requires=['pexpect>=4,<5'], # pexpect 4.x.x required

    keywords='doctest documentation test testing',

    py_modules=['byexample'],
    packages=['byexample_interpreters']

)

