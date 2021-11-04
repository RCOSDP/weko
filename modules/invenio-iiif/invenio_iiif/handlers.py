# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Handler functions for Flask-IIIF to open image and protect API."""

import tempfile

import pkg_resources
from flask import g
from invenio_files_rest.views import ObjectResource

try:
    pkg_resources.get_distribution('wand')
    from wand.image import Image
    HAS_IMAGEMAGICK = True
except pkg_resources.DistributionNotFound:
    # Python module not installed
    HAS_IMAGEMAGICK = False
except ImportError:
    # ImageMagick notinstalled
    HAS_IMAGEMAGICK = False


def protect_api(uuid=None, **kwargs):
    """Retrieve object and check permissions.

    Retrieve ObjectVersion of image being requested and check permission
    using the Invenio-Files-REST permission factory.
    """
    bucket, version_id, key = uuid.split(':', 2)
    g.obj = ObjectResource.get_object(bucket, key, version_id)
    return g.obj


def image_opener(key):
    """Handler to locate file based on key.

    .. note::
        If the file is a PDF then only the first page will be
        returned as an image.

    :param key: A key encoded in the format "<bucket>:<version>:<object_key>".
    :returns: A file-like object.
    """
    if hasattr(g, 'obj'):
        obj = g.obj
    else:
        obj = protect_api(key)

    fp = obj.file.storage().open('rb')

    # If ImageMagick with Wand is installed, extract first page
    # for PDF/text.
    if HAS_IMAGEMAGICK and obj.mimetype in ['application/pdf', 'text/plain']:
        first_page = Image(Image(fp).sequence[0])
        tempfile_ = tempfile.TemporaryFile()
        with first_page.convert(format='png') as converted:
            converted.save(file=tempfile_)
        return tempfile_
    return fp
