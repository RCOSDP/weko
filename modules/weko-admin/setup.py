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
    'Sphinx>=1.6.5',
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
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
    'WTForms>=2.0.1',
    'Flask-BabelEx>=0.9.3',
    'Flask-Breadcrumbs>=0.3.0',
    'Flask-WTF>=0.13.1',
    'Flask-Mail>=0.9.1',
    'invenio-db>=1.0.0b9',
    'invenio-accounts>=1.0.0b3',
    'invenio-assets>=1.0.0b7',
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
        ],
        'invenio_base.apps': [
            'weko_admin = weko_admin:WekoAdmin',
        ],
        'invenio_admin.views': [
            'weko_admin_style = weko_admin.admin:style_adminview',
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
            'weko_admin_css = weko_admin.bundles:css',
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
