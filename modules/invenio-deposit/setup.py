# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module for depositing record metadata and uploading files."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'invenio-access>=1.0.0',
    'invenio-accounts>=1.0.0',
    'invenio-db[postgresql]>=1.0.1',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=3.0.4',
    'reportlab>=3.3.0',
]

invenio_search_version = '1.2.0'

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'elasticsearch2': [
        'invenio-search[elasticsearch2]>={}'.format(invenio_search_version),
    ],
    'elasticsearch5': [
        'invenio-search[elasticsearch5]>={}'.format(invenio_search_version),
    ],
    'elasticsearch6': [
        'invenio-search[elasticsearch6]>={}'.format(invenio_search_version),
    ],
    'elasticsearch7': [
        'invenio-search[elasticsearch7]>={}'.format(invenio_search_version),
    ],
    'tests': tests_require,
}


extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in (
            'elasticsearch2', 'elasticsearch5', 'elasticsearch6',
            'elasticsearch7'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.3',
    'Flask-Login>=0.3.2',
    'Flask>=0.11.1',
    'SQLAlchemy-Continuum>=1.3.6',
    'SQLAlchemy-Utils[encrypted]>=0.33',
    'dictdiffer>=0.5.0.post1',
    'invenio-assets>=1.0.0',
    'invenio-db[versioning]>=1.0.1',
    'invenio-files-rest>=1.0.0a23',
    'invenio-jsonschemas>=1.0.0a3',
    'invenio-oauth2server>=1.0.3',
    'invenio-records-files>=1.0.0a10',
    'invenio-records-rest>=1.6.2',
    'invenio-records-ui>=1.0.1',
    'invenio-search-ui>=1.0.0',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_deposit', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-deposit',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio deposit upload',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-deposit',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'deposit = invenio_deposit.cli:deposit',
        ],
        'invenio_base.apps': [
            'invenio_deposit = invenio_deposit:InvenioDeposit',
        ],
        'invenio_base.api_apps': [
            'invenio_deposit_rest = invenio_deposit:InvenioDepositREST',
        ],
        'invenio_access.actions': [
            'deposit_admin_access'
            ' = invenio_deposit.permissions:action_admin_access',
        ],
        'invenio_assets.bundles': [
            'invenio_deposit_css = invenio_deposit.bundles:css',
            'invenio_deposit_js = invenio_deposit.bundles:js',
            'invenio_deposit_dependencies_js = invenio_deposit.bundles:'
            'js_dependecies',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_deposit',
        ],
        'invenio_pidstore.fetchers': [
            'deposit = invenio_deposit.fetchers:deposit_fetcher',
        ],
        'invenio_pidstore.minters': [
            'deposit = invenio_deposit.minters:deposit_minter',
        ],
        'invenio_jsonschemas.schemas': [
            'deposits = invenio_deposit.jsonschemas',
        ],
        'invenio_oauth2server.scopes': [
            'deposit_write = invenio_deposit.scopes:write_scope',
            'deposit_actions = invenio_deposit.scopes:actions_scope',
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
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 1 - Planning',
    ],
)
