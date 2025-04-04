# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2019, 2020 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""S3 file storage support for Invenio. """

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=5.0',
    'invenio-base>=1.2.2',
    'invenio-app>=1.2.3',
    'invenio-db[all]>=1.0.4',
    'isort>=4.3.3',
    'moto>=1.3.7',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-invenio>=1.3.0',
    'pytest-pep8>=1.0.6',
    'pytest>=4.6.4,<5.0.0',
    'redis>=2.10.5',
]

extras_require = {
    'docs': [
        'Sphinx>=1.5.1,<3.0.2',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

setup_requires = [
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'boto3>=1.9.83',
    'invenio-files-rest>=1.0.0',
    's3fs>=0.1.5,<0.3.0', # Newer versions only allow python >= 3.5
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_s3', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-s3',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio s3',
    license='MIT',
    author='Esteban J. G. Gabancho',
    author_email='egabancho@gmail.com',
    url='https://github.com/inveniosoftware/invenio-s3',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.api_apps': [
            'invenio_s3 = invenio_s3:InvenioS3',
        ],
        'invenio_base.apps': [
            'invenio_s3 = invenio_s3:InvenioS3',
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
        'Development Status :: 4 - Beta',
    ],
)
