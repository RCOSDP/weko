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
from flask import g
from flask_iiif.restful import IIIFImageAPI
from invenio_files_rest.models import ObjectVersion


@shared_task(ignore_result=True)
def create_thumbnail(uuid, thumbnail_width):
    """Create the thumbnail for an image."""
    # 利用者のリクエストではない内部処理なので、利用者の権限は確かめずに
    # 対象を解決しておく(image_opener は g.obj があればそれを使う)。
    bucket, version_id, key = uuid.split(':', 2)
    g.obj = ObjectVersion.get(bucket, key, version_id=version_id)
    # size = '!' + thumbnail_width + ','
    size = thumbnail_width + ','  # flask_iiif doesn't support ! at the moment
    region = "full"
    thumbnail = IIIFImageAPI().get("v2", uuid, region, size, "0", "default", "jpg")
