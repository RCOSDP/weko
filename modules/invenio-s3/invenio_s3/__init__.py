# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""S3 file storage support for Invenio.

To use this module together with Invenio-Files-Rest there are a few things you
need to keep in mind.

The storage factory configuration variable, ``FILES_REST_STORAGE_FACTORY``
needs to be set to ``'invenio_s3.s3fs_storage_factory'`` importable string.

We think the best way to use this module is to have one `Localtion
<https://invenio-files-rest.readthedocs.io/en/latest/api.html#module-invenio_files_rest.models>`_
for each S3 bucket. This is just for simplicity, it can used however needed.

This module doesn't create S3 buckets automatically, so before starting they
need to be created.
"""

from __future__ import absolute_import, print_function

from .ext import InvenioS3
from .storage import S3FSFileStorage, s3fs_storage_factory
from .version import __version__

__all__ = (
    '__version__',
    'InvenioS3',
    'S3FSFileStorage',
    's3fs_storage_factory',
)
