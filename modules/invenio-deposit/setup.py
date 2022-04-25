# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Module for depositing record metadata and uploading files."""

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

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
    # Elasticsearch version
    'elasticsearch2': [
        'elasticsearch>=2.0.0,<3.0.0',
        'elasticsearch-dsl>=2.0.0,<3.0.0',
    ],
    'elasticsearch5': [
        'elasticsearch>=5.0.0,<6.0.0',
        'elasticsearch-dsl>=5.1.0,<6.0.0',
    ],
    'elasticsearch6': [
        'elasticsearch>=6.0.0,<7.0.0',
        'elasticsearch-dsl>=6.4.0,<7.0.0',
    ],

}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name[0] == ':' or name in (
            'elasticsearch2', 'elasticsearch5', 'elasticsearch6'):
        continue
    extras_require['all'].extend(reqs)


setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask-BabelEx>=0.9.3',
    'Flask-Login>=0.3.2',
    'Flask>=0.11.1',
    'SQLAlchemy-Continuum>=1.3',
    'SQLAlchemy-Utils[encrypted]>=0.32.6',
    'dictdiffer>=0.5.0.post1',
    'invenio-assets>=1.0.0b6',
    'invenio-db[versioning]>=1.0.0b3',
    'invenio-files-rest>=1.0.0a14',
    'invenio-jsonschemas>=1.0.0a3',
    'invenio-oauth2server>=1.0.0a12',
    'invenio-records-files>=1.0.0a8',
    'invenio-records-rest>=1.0.0b5',
    'invenio-records-ui>=1.0.0a8',
    'invenio-search-ui>=1.0.0a5',
    'invenio-search>=1.0.0a11',
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
    license='GPLv2',
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
        'invenio_search.mappings': [
            'deposits = invenio_deposit.mappings',
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
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
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
