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

"""Module for displaying records."""

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
    'invenio-previewer>=1.0.0a11',
    'pypdf>=4.3.1,<5.0.0',
    'invenio-pidrelations>=1.0.0a3',
    'invenio-records>=1.0.0b4',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_records_ui', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-records-ui',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko records ui',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-records-ui',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'weko_records_ui = weko_records_ui:WekoRecordsUI',
        ],
        'invenio_base.api_apps': [
            'weko_records_ui_rest = weko_records_ui:WekoRecordsREST',
            'weko_records_ui_cites_rest = weko_records_ui:WekoRecordsCitesREST',
        ],
        'invenio_admin.views': [
            'weko_records_ui_setting = weko_records_ui.admin:item_adminview',
            'weko_records_ui_pdfcoverpage = weko_records_ui.admin:pdfcoverpage_adminview',
            'weko_records_ui_institution = weko_records_ui.admin:institution_adminview',
            'weko_records_ui_bulk_update = weko_records_ui.admin:item_management_bulk_update_adminview',
        ],
        'invenio_i18n.translations': [
            'messages = weko_records_ui',
        ],
        'invenio_config.module': [
            'weko_records_ui = weko_records_ui.config',
        ],
        'invenio_assets.bundles': [
            'weko_records_ui_css = weko_records_ui.bundles:style',
            'weko_records_ui_dependencies_js = weko_records_ui.bundles:js_dependecies',
            'weko_records_ui_js = weko_records_ui.bundles:js',
            'weko_records_ui_preview_carousel_js = weko_records_ui.bundles:preview_carousel',
            'weko_records_ui_file_action_js = weko_records_ui.bundles:file_action_js',
            'weko_records_ui_bucket_js = weko_records_ui.bundles:bucket_js',
            'weko_records_ui_bootstrap_popover_js = weko_records_ui.bundles:bootstrap_popover_js',
            'weko_records_ui_bootstrap_popover_css = weko_records_ui.bundles:bootstrap_popover_css',
        ],
        'invenio_access.actions': [
            'detail_page_access'
            ' = weko_records_ui.permissions:action_detail_page_access',
            'download_original_pdf_access = weko_records_ui.permissions:action_download_original_pdf_access',
        ],
        'invenio_db.alembic': [
            'weko_records_ui = weko_records_ui:alembic',
        ],
        'invenio_db.models': [
            'weko_records_ui = weko_records_ui.models',
        ],
        'invenio_oauth2server.scopes': [
            'file_read_scope = weko_records_ui.scopes:file_read_scope',
            'item_read_scope = weko_records_ui.scopes:item_read_scope',
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
