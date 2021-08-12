# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
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
"""Module for depositing record metadata and uploading files."""
import os
from typing import Any
from typing import Dict

from setuptools import find_packages
from setuptools import setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

install_requires = [
    "bagit",
    "marshmallow",
    "rdflib",
    "rdflib-jsonld",
    "invenio-celery",
    "invenio-db[versioning]",
    "invenio-deposit",
    "invenio-files-rest",
    "invenio-jsonschemas",
    "invenio-records-files",
    "invenio-records-rest",
    "rfc6266-parser",
    "sword3common",
    # We use typing.Protocol, which is Py3.8+, but is available in typing-extensions for backwards compatibility
    'typing-extensions;python_version<"3.8"',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g: Dict[str, Any] = {}
with open(os.path.join("invenio_sword", "version.py"), "rt") as fp:
    exec(fp.read(), g)
    version = g["__version__"]

setup(
    name="invenio-sword",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    keywords="invenio sword deposit upload",
    license="GPLv2",
    author="Cottage Labs LLP",
    author_email="us@cottagelabs.com",
    url="https://github.com/swordapp/invenio-sword",
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    entry_points={
        "invenio_base.apps": ["invenio_sword = invenio_sword:InvenioSword",],
        "invenio_base.api_apps": ["invenio_sword = invenio_sword:InvenioSword",],
        "invenio_sword.packaging": [
            "http://purl.org/net/sword/3.0/package/Binary = invenio_sword.packaging:BinaryPackaging",
            "http://purl.org/net/sword/3.0/package/SimpleZip = invenio_sword.packaging:SimpleZipPackaging",
            "http://purl.org/net/sword/3.0/package/SWORDBagIt = invenio_sword.packaging:SWORDBagItPackaging",
        ],
        "invenio_sword.metadata": [
            "http://purl.org/net/sword/3.0/types/Metadata = invenio_sword.metadata:SWORDMetadata",
        ],
        "invenio_celery.tasks": ["invenio_sword = invenio_sword.tasks",],
    },
    install_requires=install_requires,
    extras_require={"test": ["pytest", "pytest-httpserver",]},
    python_requires=">=3.7",
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
        "Development Status :: 1 - Planning",
    ],
)
