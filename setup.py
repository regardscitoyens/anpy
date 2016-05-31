# -*- coding: utf-8 -*-

from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

__version__ = None
with open(path.join(here, 'anpy', '__version.py')) as __version:
    exec(__version.read())
assert __version__ is not None

with open(path.join(here, 'README.md')) as readme:
    LONG_DESC = readme.read().decode('utf-8')

setup(
    name='anpy',
    version=__version__,

    description='Python client for assemblee-nationale.fr website',
    long_description=LONG_DESC,
    license="MIT",

    url='https://github.com/regardscitoyens/anpy',
    author='Regards Citoyens',
    author_email='contact@regardscitoyens.org',

    include_package_data=True,

    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],

    keywords='scraping politics data',

    packages=['anpy', 'anpy.parsing'],

    install_requires=['pathlib', 'Click', 'requests', 'beautifulsoup4', 'xmltodict', 'html5lib'],

    scripts=['bin/anpy-cli.py'],
)
