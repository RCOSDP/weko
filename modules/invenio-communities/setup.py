# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Invenio module that adds support for communities."""

from __future__ import absolute_import, print_function

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

invenio_search_version = '1.2.2'

extras_require = {
    'admin': [
        'Flask-Admin>=1.3.0',
    ],
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'mail': [
        'Flask-Mail>=0.9.1',
    ],
    'oai': [
        'invenio-oaiserver>=1.0.3',
    ],
    # 'elasticsearch2': [
    #     'invenio-search[elasticsearch2]>={}'.format(invenio_search_version),
    # ],
    # 'elasticsearch5': [
    #     'invenio-search[elasticsearch5]>={}'.format(invenio_search_version),
    # ],
    # 'elasticsearch6': [
    #     'invenio-search[elasticsearch6]>={}'.format(invenio_search_version),
    # ],
    # 'elasticsearch7': [
    #     'invenio-search[elasticsearch7]>={}'.format(invenio_search_version),
    # ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in (
        'elasticsearch2', 'elasticsearch5', 'elasticsearch6',
        'elasticsearch7'
    ):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.7',
]

install_requires = [
    'bleach>=2.1.3',
    'Flask-BabelEx>=0.9.3',
    'Flask>=0.11.1',
    # 'elasticsearch-dsl>=6.0.0,<7.0.0',
    # 'elasticsearch>=6.0.0,<7.0.0',
    'invenio-access>=1.1.0',
    'invenio-accounts>=1.1.0',
    'invenio-files-rest>=1.0.0b1',
    'invenio-indexer>=1.0.2',
    'invenio-pidstore>=1.0.0',
    'invenio-records>=1.2.0',
    'invenio-rest[cors]>=1.0.0',
    # 'invenio-search>=1.0.0a9',
    'marshmallow>=2.15.0,<3',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_communities', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-communities',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio communities',
    license='GPLv2',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-communities',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'invenio_communities = invenio_communities:InvenioCommunities',
        ],
        'invenio_base.blueprints': [
            'invenio_communities = invenio_communities.views.ui:blueprint',
        ],
        'invenio_base.api_apps': [
            'invenio_communities = invenio_communities:InvenioCommunities',
        ],
        'invenio_base.api_blueprints': [
            'invenio_communities = invenio_communities.views.api:blueprint',
        ],
        'invenio_db.alembic': [
            'invenio_communities = invenio_communities:alembic',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_communities',
        ],
        'invenio_admin.views': [
            'invenio_communities_communities = '
            'invenio_communities.admin:community_adminview',
            'invenio_communities_requests = '
            'invenio_communities.admin:request_adminview',
            'invenio_communities_featured = '
            'invenio_communities.admin:featured_adminview',
        ],
        'invenio_celery.tasks': [
            'invenio_communities = invenio_communities.tasks',
        ],
        'invenio_assets.bundles': [
            'invenio_communities_js = invenio_communities.bundles:js',
            'invenio_communities_js_tree = invenio_communities.bundles:js_tree',
            'invenio_communities_js_tree_display = invenio_communities.bundles:js_tree_display',
            'invenio_communities_css = invenio_communities.bundles:css',
            'invenio_communities_css_tree = invenio_communities.bundles:css_tree',
            'invenio_communities_css_tree_display = invenio_communities.bundles:css_tree_display',
        ]
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
        'Development Status :: 3 - Alpha',
    ],
)
