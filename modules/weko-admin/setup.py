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

"""Module providing admin capabilities."""

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
    'WTForms>=2.0.1',
    'Flask-BabelEx>=0.9.3',
    'Flask-Breadcrumbs>=0.3.0',
    'Flask-WTF>=0.13.1',
    'Flask-Mail>=0.9.1',
    'invenio-db>=1.0.0b9',
    'SQLAlchemy-Continuum>=1.3.6',
    'invenio-accounts>=1.0.0b3',
    "elasticsearch_dsl<7.0.0,>=6.0.0",
    'invenio-assets>=1.0.0b7',
    'invenio-admin>=1.1.2',
    'requests>=2.18.4',
    'invenio-cache>=1.0.0',
    'invenio-indexer>=1.0.0',
    'invenio-search>=1.0.0',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_admin', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-admin',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko admin',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-admin',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'lifetime = weko_admin.cli:lifetime',
            'language = weko_admin.cli:language',
            'cert = weko_admin.cli:cert',
            'report = weko_admin.cli:report',
            'billing = weko_admin.cli:billing',
            'admin_settings = weko_admin.cli:admin_settings',
            'authors_prefix = weko_admin.cli:authors_prefix',
            'authors_affiliation = weko_admin.cli:authors_affiliation',
            'facet_search_setting = weko_admin.cli:facet_search_setting'
        ],
        'invenio_celery.tasks': [
            'weko_admin = weko_admin.tasks',
        ],
        'invenio_base.apps': [
            'weko_admin = weko_admin:WekoAdmin',
        ],
        'invenio_base.api_blueprints': [
            'weko_admin = weko_admin.views:blueprint_api',
        ],
        'invenio_admin.views': [
            'weko_admin_style = weko_admin.admin:style_adminview',
            'weko_admin_report = weko_admin.admin:report_adminview',
            'weko_admin_feedback_mail = weko_admin.admin:feedback_mail_adminview',
            'weko_admin_language = weko_admin.admin:language_adminview',
            'weko_admin_web_api_account = weko_admin.admin:web_api_account_adminview',
            'weko_admin_stats_settings = weko_admin.admin:stats_settings_adminview',
            'weko_admin_log_analysis = weko_admin.admin:log_analysis_settings_adminview',
            'weko_admin_ranking_settings = weko_admin.admin:ranking_settings_adminview',
            'weko_admin_search_settings = weko_admin.admin:search_settings_adminview',
            'weko_admin_site_license_settings = weko_admin.admin:site_license_settings_adminview',
            'weko_admin_site_license_send_mail_settings = weko_admin.admin:site_license_send_mail_settings_adminview',
            'weko_admin_file_preview_settings = weko_admin.admin:file_preview_settings_adminview',
            'weko_admin_item_export_settings = weko_admin.admin:item_export_settings_adminview',
            'weko_admin_site_info = weko_admin.admin:site_info_settings_adminview',
            'weko_admin_identifier = weko_admin.admin:identifier_adminview',
            'weko_admin_sword_api = weko_admin.admin:sword_api_settings_adminview',
            'weko_admin_sword_jsonld_api = weko_admin.admin:sword_api_settings_jsonld_adminview',
            'weko_admin_sword_jsonld_mapping_api = weko_admin.admin:sword_api_jsonld_mapping_adminview',
            'restricted_access_adminview = weko_admin.admin:restricted_access_adminview',
            'facet_search_adminview = weko_admin.admin:facet_search_adminview',
            'reindex_elasticsearch_adminview = weko_admin.admin:reindex_elasticsearch_adminview'
        ],
        'invenio_access.actions': [
            'page_style_access = weko_admin.permissions:action_admin_access',
            'page_style_update = weko_admin.permissions:action_admin_update',
        ],
        'invenio_db.alembic': [
            'weko_admin = weko_admin:alembic',
        ],
        'invenio_assets.bundles': [
            'weko_admin_js = weko_admin.bundles:js',
            'weko_admin_search_js = weko_admin.bundles:search_management_js',
            'weko_admin_stats_report_js = weko_admin.bundles:stats_report_js',
            'weko_admin_react_bootstrap_js = weko_admin.bundles:react_bootstrap_js',
            'weko_admin_css = weko_admin.bundles:css',
            'weko_admin_quill_css = weko_admin.bundles:weko_admin_quill_sknow_css',
            'weko_admin_feedback_mail_css = weko_admin.bundles:weko_admin_feedback_mail_css',
            'weko_admin_date_picker_js = weko_admin.bundles:date_picker_js',
            'weko_admin_date_picker_css = weko_admin.bundles:date_picker_css',
            'weko_admin_custom_report = weko_admin.bundles:custom_report_js',
            'weko_admin_feedback_mail = weko_admin.bundles:feedback_mail_js',
            'weko_admin_statistics_reactjs_lib = weko_admin.bundles:statistics_reactjs_lib',
            'weko_admin_log_analysis_js = weko_admin.bundles:log_analysis_js',
            'weko_admin_admin_lte_js_dependecies = weko_admin.bundles:admin_lte_js_dependecies',
            'weko_admin_admin_lte_js = weko_admin.bundles:admin_lte_js',
            'weko_admin_angular_js = weko_admin.bundles:angular_js',
            'weko_admin_jsonld_js = weko_admin.bundles:weko_admin_jsonld_js',
            'weko_admin_site_info = weko_admin.bundles:weko_admin_site_info_js',
            'weko_admin_site_info_css = weko_admin.bundles:weko_admin_site_info_css',
            'weko_admin_ng_js_tree = weko_admin.bundles:weko_admin_ng_js_tree_js',
            'weko_admin_restricted_access = weko_admin.bundles:weko_admin_restricted_access_js',
            'weko_admin_facet_search = weko_admin.bundles:weko_admin_facet_search_js',
            'weko_admin_reindex_elasticsearch_js = weko_admin.bundles:reindex_elasticsearch_js'
        ],
        'invenio_db.models': [
            'weko_admin = weko_admin.models',
        ],
        'invenio_i18n.translations': [
            'messages = weko_admin',
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
