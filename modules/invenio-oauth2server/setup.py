# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module that implements OAuth 2 server."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'SQLAlchemy-Continuum>=1.2.1',
    'check-manifest>=0.25',
    'coverage>=4.0',
    'invenio-assets>=1.0.0',
    'invenio-i18n>=1.0.0',
    'invenio-theme>=1.0.0',
    'isort>=4.2.2',
    'mock>=1.3.0',
    'pydocstyle>=1.0.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.3',
]

extras_require = {
    'admin': [
        'invenio-admin>=1.0.0'
    ],
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'redis': [
        'redis>=2.10.5',
    ],
    'mysql': [
        'invenio-db[mysql]>=1.0.0',
    ],
    'postgresql': [
        'invenio-db[postgresql]>=1.0.0',
    ],
    'sqlite': [
        'invenio-db>=1.0.0',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in {'mysql', 'postgresql', 'sqlite'}:
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    'Flask-Breadcrumbs>=0.4.0',
    'Flask-Login>=0.3.0',
    'Flask-OAuthlib>=0.9.3',
    'Flask-WTF>=0.13.1',
    'Flask>=0.11.1',
    'future>=0.16.0',
    'invenio-accounts>=1.0.0',
    'oauthlib>=1.1.2,!=2.0.0,!=2.0.3,!=2.0.4,!=2.0.5',
    'pyjwt>=1.5.0',
    'six>=1.10.0',
    'SQLAlchemy-Utils[encrypted]>=0.33.0',
    'WTForms-Alchemy>=0.15.0',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_oauth2server', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-oauth2server',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio OAuth2 server',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-oauth2server',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_admin.views': [
            'invenio_oauth2server_clients_adminview = '
            'invenio_oauth2server.admin:oauth2server_clients_adminview',
            'invenio_oauth2server_tokens_adminview = '
            'invenio_oauth2server.admin:oauth2server_tokens_adminview',
        ],
        'invenio_base.apps': [
            'invenio_oauth2server = invenio_oauth2server:InvenioOAuth2Server',
        ],
        'invenio_base.api_apps': [
            'invenio_oauth2server = invenio_oauth2server:InvenioOAuth2Server',
            'invenio_oauth2server_rest ='
            ' invenio_oauth2server:InvenioOAuth2ServerREST',
        ],
        'invenio_base.blueprints': [
            'invenio_oauth2server ='
            ' invenio_oauth2server.views.server:blueprint',
            'invenio_oauth2server_settings ='
            ' invenio_oauth2server.views.settings:blueprint',
        ],
        'invenio_db.alembic': [
            'invenio_oauth2server = invenio_oauth2server:alembic',
        ],
        'invenio_db.models': [
            'invenio_oauth2server = invenio_oauth2server.models',
        ],
        'invenio_oauth2server.scopes': [
            'oauth_email = invenio_oauth2server.scopes:email_scope',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_oauth2server',
        ],
        'invenio_base.secret_key': [
            'invenio_oauth2server = '
            'invenio_oauth2server.utils:rebuild_access_tokens',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 5 - Production/Stable',
    ],
)
