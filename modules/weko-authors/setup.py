# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module of weko-authors."""

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
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_authors', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-authors',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko authors',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-authors',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'authors = weko_authors.cli:authors',
        ],
        'invenio_base.apps': [
            'weko_authors = weko_authors:WekoAuthors',
        ],
        'invenio_base.api_apps': [
            'weko_authors = weko_authors:WekoAuthors',
            'weko_authors_rest = weko_authors:WekoAuthorsREST',
        ],
        'invenio_admin.views': [
            'weko_authors_management = '
            'weko_authors.admin:authors_list_adminview',
            'weko_authors_export = '
            'weko_authors.admin:authors_export_adminview',
            'weko_authors_import = '
            'weko_authors.admin:authors_import_adminview',
        ],
        'invenio_base.blueprints': [
            'weko_authors = weko_authors.views:blueprint',
        ],
        'invenio_base.api_blueprints': [
            'weko_authors = weko_authors.views:blueprint_api',
        ],
        'invenio_i18n.translations': [
            'messages = weko_authors',
        ],
        'invenio_db.models': [
            'weko_authors = weko_authors.models',
        ],
         'invenio_db.alembic': [
            'weko_authors = weko_authors:alembic',
        ],
        'invenio_search.mappings': [
            'authors = weko_authors.mappings',
        ],
        'invenio_assets.bundles': [
            'weko_authors_css = weko_authors.bundles:css',
            'weko_authors_js = weko_authors.bundles:js',
            'weko_authors_search_css = weko_authors.bundles:author_search_css',
            'weko_authors_search_js = weko_authors.bundles:author_search_js',
            'weko_authors_prefix_css = weko_authors.bundles:author_prefix_css',
            'weko_authors_prefix_js = weko_authors.bundles:author_prefix_js',
            'weko_authors_affiliation_css = weko_authors.bundles:author_affiliation_css',
            'weko_authors_affiliation_js = weko_authors.bundles:author_affiliation_js',
            'weko_authors_export_css = weko_authors.bundles:author_export_css',
            'weko_authors_export_js = weko_authors.bundles:author_export_js',
            'weko_authors_import_css = weko_authors.bundles:author_import_css',
            'weko_authors_import_js = weko_authors.bundles:author_import_js',
        ],
        'invenio_access.actions': [
            'author_access = weko_authors.permissions:action_author_access',
        ],
        'invenio_oauth2server.scopes': [
            'oauth_author_search_scope = weko_authors.scopes:author_search_scope',
            'oauth_author_create_scope = weko_authors.scopes:author_create_scope',
            'oauth_author_update_scope = weko_authors.scopes:author_update_scope',
            'oauth_author_delete_scope = weko_authors.scopes:author_delete_scope',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
