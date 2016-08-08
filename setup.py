# -*- coding: utf-8 -*-

import re
from setuptools import setup
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

with open('anpy/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

with open(path.join(here, 'README.md'), encoding='utf-8') as readme:
    LONG_DESC = readme.read()

setup(
    name='anpy',
    version=version,
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

    install_requires=[
        'pathlib',
        'click',
        'requests',
        'beautifulsoup4',
        'xmltodict',
        'html5lib'
    ],

    scripts=['bin/anpy-cli.py'],
)
