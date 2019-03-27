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

"""Module for displaying search results."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=3.3.0',
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
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    'Flask-Assets>=0.12',
    'ipaddress>=1.0.19',
    'angular-gettext-babel>=0.3',
    'elasticsearch_dsl<3.0.0,>=2.0.0',
    'invenio-assets>=1.0.0b7',
    'invenio-db>=1.0.0b9',
    'invenio-records-rest==1.0.0b3',
    'invenio-search>=1.0.0b4',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_search_ui', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-search-ui',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko search ui',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-search-ui',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'babel.extractors': [
            'angular_gettext = angular_gettext_babel.extract:extract_angular',
        ],
        'invenio_base.apps': [
            'weko_search_ui = weko_search_ui:WekoSearchUI',
        ],
        'invenio_base.api_apps': [
            'weko_search_rest = weko_search_ui:WekoSearchREST',
        ],
        'invenio_base.api_blueprints': [
            'weko_search_ui = weko_search_ui.views:blueprint_api',
        ],
        'invenio_config.module': [
            'weko_search_ui = weko_search_ui.config',
        ],
        'invenio_assets.bundles': [
            'weko_search_ui_css = weko_search_ui.bundles:css',
            'weko_search_ui_search_i18n = weko_search_ui.bundles:i18n',
            'weko_search_ui_js = weko_search_ui.bundles:js',
            'weko_search_ui_dependencies_js = weko_search_ui.bundles:'
            'js_dependecies',
        ],
        'invenio_i18n.translations': [
            'messages = weko_search_ui',
        ],
        'invenio_access.actions': [
            'search_access = weko_search_ui.permissions:action_search_access',
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
