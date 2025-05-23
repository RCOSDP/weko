# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Mail is an integration layer between Invenio and Flask-Mail."""

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
    'pytest-mock==3.1.0',
    'responses',
]

extras_require = {
    'celery': [
        'Flask-CeleryExt>=0.2.2',
    ],
    'docs': [
        'Flask-CeleryExt>=0.2.2',
        'Sphinx>=1.4.2',
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
    'Flask>=0.11.1',
    'Flask-Mail>=0.9.1',
    'invenio-db>=1.0.0b9',
    'invenio-admin>=1.0.0b4'
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_mail', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-mail',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio mail',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-mail',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'invenio_mail = invenio_mail:InvenioMail',
        ],
        'invenio_base.api_apps': [
            'invenio_mail = invenio_mail:InvenioMail',
        ],
        'invenio_admin.views': [
            'invenio_mail = invenio_mail.admin:mail_adminview',
            'invenio_mail_templates = invenio_mail.admin:mail_templates_adminview',
        ],
        'invenio_db.models': [
            'invenio_mail = invenio_mail.models',
        ],
        'invenio_db.alembic': [
            'invenio_mail = invenio_mail:alembic',
        ],
        'invenio_celery.tasks': [
            'invenio_mail = invenio_mail.tasks',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_mail',
        ],
        'invenio_assets.bundles': [
            'invenio_mail_template = invenio_mail.bundles:invenio_mail_template_js',
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
