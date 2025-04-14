# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that implements OAI-PMH server."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'coverage>=4.5.3,<5.0.0',
    'mock>=3.0.0,<4.0.0',
    'pytest>=4.6.4,<5.0.0',
    'pytest-cache',
    'pytest-cov',
    'pytest-pep8',
    'pytest-invenio',
    'responses',
]

invenio_search_version = '1.0.0'

extras_require = {
    'admin': [
        'Flask-Admin>=1.3.0',
    ],
    'celery': [
        'Flask-CeleryExt>=0.3.0',
    ],
    'docs': [
        'Sphinx>=1.5.2',
    ],
    # Elasticsearch
    'elasticsearch2': [
        'invenio-search[elasticsearch2]>={}'.format(invenio_search_version)
    ],
    'elasticsearch5': [
        'invenio-search[elasticsearch5]>={}'.format(invenio_search_version)
    ],
    'elasticsearch6': [
        'invenio-search[elasticsearch6]>={}'.format(invenio_search_version)
    ],
    # Database
    'mysql': [
        'invenio-db[mysql]>=1.0.0',
    ],
    'postgresql': [
        'invenio-db[postgresql]>=1.0.0',
    ],
    'sqlite': [
        'invenio-db>=1.0.0',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name[0] == ':' or name in (
            'mysql', 'postgresql', 'sqlite',
            'elasticsearch2', 'elasticsearch5', 'elasticsearch6'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask>=0.11.1',
    'Flask-BabelEx>=0.9.2',
    'dojson>=1.2.0',
    'invenio-pidstore>=1.0.0b2',
    'invenio-records>=1.0.0b3',
    'lxml>=3.5.0',
    'marshmallow>=2.7.0',
    'webargs>=1.3.2',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_oaiserver', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-oaiserver',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio OAI-PMH',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-oaiserver',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'oaipmh_file_create = invenio_oaiserver.cli:oaipmh_file_create',
        ],
        'invenio_base.apps': [
            'invenio_oaiserver = invenio_oaiserver:InvenioOAIServer',
        ],
        'invenio_base.blueprints': [
            'invenio_oaiserver = invenio_oaiserver.views.server:blueprint',
        ],
        'invenio_base.api_apps': [
            'invenio_oaiserver = invenio_oaiserver:InvenioOAIServer',
        ],
        'invenio_db.alembic': [
            'invenio_oaiserver = invenio_oaiserver:alembic',
        ],
        'invenio_db.models': [
            'invenio_oaiserver = invenio_oaiserver.models',
        ],
        'invenio_admin.views': [
            'invenio_oaiserver = invenio_oaiserver.admin:set_adminview',
            'invenio_oaiserver_aa = invenio_oaiserver.admin:set_OAIPMHview'
        ],
        'invenio_jsonschemas.schemas': [
            'oaiserver = invenio_oaiserver.schemas',
        ],
        'invenio_pidstore.minters': [
            'oaiid = invenio_oaiserver.minters:oaiid_minter',
        ],
        'invenio_pidstore.fetchers': [
            'oaiid = invenio_oaiserver.fetchers:oaiid_fetcher',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 5 - Production/Stable',
    ],
)
