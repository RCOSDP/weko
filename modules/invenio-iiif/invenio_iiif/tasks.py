# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Background tasks to prepare cache with thumbnails."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask_iiif.restful import IIIFImageAPI


@shared_task(ignore_result=True)
def create_thumbnail(uuid, thumbnail_width):
    """Create the thumbnail for an image."""
    # size = '!' + thumbnail_width + ','
    size = thumbnail_width + ','  # flask_iiif doesn't support ! at the moment
    region = "full"
    thumbnail = IIIFImageAPI().get("v2", uuid, region, size, "0", "default", "jpg")
