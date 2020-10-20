# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Implementation of various utility functions."""

import mimetypes

import six
from flask import current_app
from invenio_db import db
from sqlalchemy import MetaData, Table
from werkzeug.utils import import_string

ENCODING_MIMETYPES = {
    'gzip': 'application/gzip',
    'compress': 'application/gzip',
    'bzip2': 'application/x-bzip2',
    'xz': 'application/x-xz',
}
"""Mapping encoding to MIME types which are not in mimetypes.types_map."""


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, six.string_types):
        return import_string(value)
    elif value:
        return value
    return default


def load_or_import_from_config(key, app=None, default=None):
    """Load or import value from config.

    :returns: The loaded value.
    """
    app = app or current_app
    imp = app.config.get(key)
    return obj_or_import_string(imp, default=default)


def guess_mimetype(filename):
    """Map extra mimetype with the encoding provided.

    :returns: The extra mimetype.
    """
    m, encoding = mimetypes.guess_type(filename)
    if encoding:
        m = ENCODING_MIMETYPES.get(encoding, None)
    return m or 'application/octet-stream'


def get_record_bucket_by_bucket_id(bucket_id):
    """Get record bucket from table records_buckets.

    :params bucket_id: id of bucket.
    :returns: a record bucket.
    """
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table = Table('records_buckets', metadata)
    result = db.session.query(table).filter(
        table.c.bucket_id == bucket_id).one()
    return result


def get_record_metadata_by_record_id(record_id):
    """Get record metadata from table records_metadata.

    :params record_id: id of record metadata.
    :returns: a record metadata.
    """
    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table = Table('records_metadata', metadata)
    result = db.session.query(table).filter(table.c.id == record_id).one()
    return result
