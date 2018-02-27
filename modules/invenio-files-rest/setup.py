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

"""Files download/upload REST API similar to S3 for Invenio."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'Flask-BabelEx>=0.9.3',
    'Flask-Menu>=0.4.0',
    'SQLAlchemy-Continuum>=1.2.1',
    'check-manifest>=0.25',
    'coverage>=4.0',
    'invenio-access>=1.0.0a11',
    'invenio-accounts>=1.0.0b3',
    'invenio-admin>=1.0.0b1',
    'invenio-celery>=1.0.0b2',
    'isort>=4.2.15',
    'mock>=1.3.0',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1',
        'sphinxcontrib-httpdomain>=1.4.0',
    ],
    'postgresql': [
        'invenio-db[postgresql]>=1.0.0b3',
    ],
    'mysql': [
        'invenio-db[mysql]>=1.0.0b3',
    ],
    'sqlite': [
        'invenio-db>=1.0.0b3',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('postgresql', 'mysql', 'sqlite'):
        continue
    extras_require['all'].extend(reqs)

install_requires = [
    'Flask-CeleryExt>=0.2.2',
    'Flask-Login>=0.3.2',
    'Flask-WTF>=0.13.1',
    'Flask>=0.11.1',
    'SQLAlchemy-Utils>=0.31.0',
    'WTForms>=2.0',
    'fs>=0.5.4,<2.0',
    'invenio-rest[cors]>=1.0.0a10',
    'webargs>=1.1.1',
]

setup_requires = [
    'pytest-runner>=2.7',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_files_rest', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-files-rest',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio files REST',
    license='GPLv2',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-files-rest',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_access.actions': [
            # Location related permissions
            'location_update_all'
            ' = invenio_files_rest.permissions:location_update_all',
            # Bucket related permissions.
            'bucket_read_all'
            ' = invenio_files_rest.permissions:bucket_read_all',
            'bucket_read_versions_all'
            ' = invenio_files_rest.permissions:bucket_read_versions_all',
            'bucket_update_all'
            ' = invenio_files_rest.permissions:bucket_update_all',
            'bucket_listmultiparts_all'
            ' = invenio_files_rest.permissions:bucket_listmultiparts_all',
            # Object related permissions.
            'object_read_all'
            ' = invenio_files_rest.permissions:object_read_all',
            'object_read_version_all'
            ' = invenio_files_rest.permissions:object_read_version_all',
            'object_delete_all'
            ' = invenio_files_rest.permissions:object_delete_all',
            'object_delete_version_all'
            ' = invenio_files_rest.permissions:object_delete_version_all',
            # Multipart related permissions.
            'multipart_read_all'
            ' = invenio_files_rest.permissions:multipart_read_all',
            'multipart_delete_all'
            ' = invenio_files_rest.permissions:multipart_delete_all',
        ],
        'invenio_admin.views': [
            'location_adminview = invenio_files_rest.admin:location_adminview',
            'bucket_adminview = invenio_files_rest.admin:bucket_adminview',
            'object_adminview = invenio_files_rest.admin:object_adminview',
            'fileinstance_adminview'
            ' = invenio_files_rest.admin:fileinstance_adminview',
            'multipartobject_adminview'
            ' = invenio_files_rest.admin:multipartobject_adminview',
        ],
        'invenio_base.api_apps': [
            'invenio_files_rest = invenio_files_rest:InvenioFilesREST',
        ],
        'invenio_base.api_blueprints': [
            'invenio_files_rest = invenio_files_rest.views:blueprint',
        ],
        'invenio_base.apps': [
            'invenio_files_rest = invenio_files_rest:InvenioFilesREST',
        ],
        'invenio_celery.tasks': [
            'invenio_files_rest = invenio_files_rest.tasks',
        ],
        'invenio_db.alembic': [
            'invenio_files_rest = invenio_files_rest:alembic',
        ],
        'invenio_db.models': [
            'invenio_files_rest = invenio_files_rest.models',
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
        'Development Status :: 3 - Alpha',
    ],
)
