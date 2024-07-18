# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for collecting statistics."""

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

invenio_search_version = '1.0.0'

extras_require = {
    'docs': [
        'Sphinx>=1.4',
    ],
    'elasticsearch2': [
        'invenio-search[elasticsearch2]>={}'.format(invenio_search_version)
    ],
    'elasticsearch5': [
        'invenio-search[elasticsearch5]>={}'.format(invenio_search_version)
    ],
    'elasticsearch6': [
        'invenio-search[elasticsearch6]>={}'.format(invenio_search_version)
    ],
    'tests': tests_require,
}

extras_require['all'] = [
    'invenio-records-ui>=1.0.1',
]

for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'arrow>=0.7.0',
    'counter-robots>=2018.6',
    'Flask>=0.11.1',
    'invenio-cache>=1.0.0',
    'invenio-files-rest>=1.0.0a23',
    'invenio-queues>=1.0.0a1',
    'maxminddb-geolite2>=2017.0404',
    'python-dateutil>=2.6.1',
    'python-geoip>=1.2',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_stats', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-stats',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio statistics',
    license='MIT',
    author='CERN',
    author_email='info@invenio-software.org',
    url='https://github.com/inveniosoftware/invenio-stats',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'stats = invenio_stats.cli:stats',
        ],
        'invenio_base.apps': [
            'invenio_stats = invenio_stats:InvenioStats',
        ],
        'invenio_base.api_apps': [
            'invenio_stats = invenio_stats:InvenioStats',
        ],
        'invenio_celery.tasks': [
            'invenio_stats = invenio_stats.tasks',
        ],
        'invenio_base.api_blueprints': [
            'invenio_files_rest = invenio_stats.views:blueprint',
        ],
        'invenio_search.templates': [
            'invenio_stats = invenio_stats.templates:register_templates',
        ],
        'invenio_queues.queues': [
            'invenio_stats = invenio_stats.queues:declare_queues',
        ],
        'invenio_stats.events': [
            'invenio_stats = '
            'invenio_stats.contrib.registrations:register_events'
        ],
        'invenio_stats.aggregations': [
            'invenio_stats = '
            'invenio_stats.contrib.registrations:register_aggregations'
        ],
        'invenio_stats.queries': [
            'invenio_stats = '
            'invenio_stats.contrib.registrations:register_queries'
        ],
        'invenio_access.actions': [
            'stats_api_access = invenio_stats.permissions:stats_api_access',
        ],
        'invenio_db.models': [
            'invenio_stats = invenio_stats.models',
        ],
        'invenio_db.alembic': [
            'invenio_stats = invenio_stats:alembic',
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha',
    ],
)
