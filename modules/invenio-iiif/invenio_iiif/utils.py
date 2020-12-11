# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utilities for IIIF."""

from __future__ import absolute_import, print_function

from flask import current_app
from invenio_files_rest.models import ObjectVersion
from six.moves.urllib_parse import quote


def iiif_image_key(obj):
    """Generate a unique IIIF image key, using the images DB location.

    :param obj: File object instance.
    :returns: Image key 'u'(str)
    """
    if isinstance(obj, ObjectVersion):
        bucket_id = obj.bucket_id
        version_id = obj.version_id
        key = obj.key
    else:
        bucket_id = obj.get('bucket')
        version_id = obj.get('version_id')
        key = obj.get('key')
    return u'{}:{}:{}'.format(
        bucket_id,
        version_id,
        key,
    )


def ui_iiif_image_url(obj, version='v2', region='full', size='full',
                      rotation=0, quality='default', image_format='png'):
    """Generate IIIF image URL from the UI application.

    :param obj: File object instance.
    :returns: URL to retrieve the processed image from.
    """
    return u'{prefix}{version}/{identifier}/{region}/{size}/{rotation}/' \
        u'{quality}.{image_format}'.format(
            prefix=current_app.config['IIIF_UI_URL'],
            version=version,
            identifier=quote(
                iiif_image_key(obj).encode('utf8'), safe=':'),
            region=region,
            size=size,
            rotation=rotation,
            quality=quality,
            image_format=image_format,
        )
