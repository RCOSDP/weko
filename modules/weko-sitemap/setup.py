# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

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
    'Flask-Babel>=3.0.0',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('weko_sitemap', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='weko-sitemap',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio TODO',
    license='MIT',
    author='National Institute of Informatics',
    author_email='wekosoftware@nii.ac.jp',
    url='https://github.com/RCOSDP/weko-sitemap',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'weko_sitemap = weko_sitemap:WekoSitemap',
        ],
        'invenio_base.blueprints': [
            'weko_sitemap = weko_sitemap.views:blueprint',
        ],
        'invenio_i18n.translations': [
            'messages = weko_sitemap',
        ],
        'invenio_admin.views': [
            'weko_sitemap_sitemap = weko_sitemap.admin:sitemap_adminview',
        ],
        # TODO: Edit these entry points to fit your needs.
        # 'invenio_access.actions': [],
        # 'invenio_admin.actions': [],
        'invenio_assets.webpack': [
            'weko_sitemap = weko_sitemap.webpack:weko_sitemap',
        ],
        # 'invenio_base.api_apps': [],
        # 'invenio_base.api_blueprints': [],
        # 'invenio_base.blueprints': [],
        'invenio_celery.tasks': [
            'weko_sitemap = weko_sitemap.tasks',
        ],
        # 'invenio_db.models': [],
        # 'invenio_pidstore.minters': [],
        # 'invenio_records.jsonresolver': [],
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
