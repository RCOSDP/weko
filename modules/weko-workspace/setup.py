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

"""Module of weko-workspace."""

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
    'Flask-Menu>=0.4.0',
    'Flask-Breadcrumbs>=0.3.0',
    'Flask-Security>=1.7.5',
    'Flask-WTF>=0.13',
    'Flask>=0.11.1',
    'invenio-accounts>=1.0.0a15',
    'invenio-admin>=1.0.0b4',
    'invenio-assets>=1.0.0b1',
    'invenio-db>=1.0.0b8',
    'WTForms>=2.1.0',
    'WTForms-Alchemy>=0.15.0',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_workspace', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-workspace',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='weko workspace',
    license='GPLv2',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/wekosoftware/weko-workspace',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'weko_workspace = weko_workspace:WekoWorkspace',
        ],
        'invenio_base.blueprints': [
            'weko_workspace = weko_workspace.views:workspace_blueprint',
        ],
        'invenio_base.api_apps': [
            'weko_workspace_api = weko_workspace:WekoWorkspace',
        ],
        'invenio_base.api_blueprints': [
            'weko_workspace_api = weko_workspace.views:blueprint_itemapi',
        ],
        'invenio_assets.bundles': [
            'workspace_item_list_js = weko_workspace.bundles:js_item_list',
            'workspace_css = weko_workspace.bundles:css_workspace',
        ],
        'invenio_i18n.translations': [
            'messages = weko_workspace',
        ],
        'invenio_db.models': [
            'weko_workspace = weko_workspace.models',
        ],
        'invenio_db.alembic': [
            'weko_workspace = weko_workspace:alembic',
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
