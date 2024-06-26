# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""File storage interface."""

from .base import FileStorage
from .pyfs import PyFSFileStorage, pyfs_storage_factory

__all__ = (
    "FileStorage",
    "pyfs_storage_factory",
    "PyFSFileStorage",
)
