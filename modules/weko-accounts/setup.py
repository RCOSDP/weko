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

"""Module providing accounts capabilities."""

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
    'invenio-accounts>=1.0.0b10',
    'invenio-logging>=1.0.0b3',
    'invenio-db>=1.0.0b9',
    'invenio-admin>=1.0.0b4',
    'invenio-accounts>=1.0.0b3',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_accounts', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-accounts',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko accounts',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-accounts',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'weko_accounts = weko_accounts:WekoAccounts',
        ],
        'invenio_base.api_apps': [
            'weko_accounts_rest = weko_accounts:WekoAccountsREST',
        ],
        'invenio_admin.views': [
            'weko_accounts_shibboleth = weko_accounts.admin:shib_adminview',
        ],
        'invenio_i18n.translations': [
            'messages = weko_accounts',
        ],
        'invenio_assets.bundles': [
            # 'weko_accounts_embedded_wayf_config_js = weko_accounts.bundles:embedded_wayf_config_js',
            'weko_accounts_css = weko_accounts.bundles:embedded_wayf_custom',
            # 'weko_accounts_embedded_ds_P1_js = '
            # 'weko_accounts.bundles:embedded_ds_P1_js',
            # 'weko_accounts_embedded_ds_P2_js = '
            # 'weko_accounts.bundles:embedded_ds_P2_js',
            'weko_accounts_embedded_ds_multi_lang_js = '
            'weko_accounts.bundles:embedded_ds_multi_language_js',
            'weko_accounts_suggest_js = weko_accounts.bundles:suggest_js',
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
