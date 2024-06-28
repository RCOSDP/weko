# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Signal receivers for certain events."""

import datetime

from flask import request

from ..utils import get_user


def file_download_event_builder(event, sender_app, obj=None, **kwargs):
    """Build a file-download event."""
    event.update(
        {
            # When:
            "timestamp": datetime.datetime.utcnow().isoformat(),
            # What:
            "bucket_id": str(obj.bucket_id),
            "file_id": str(obj.file_id),
            "file_key": obj.key,
            "size": obj.file.size,
            "referrer": request.referrer,
            # Who:
            **get_user(),
        }
    )
    return event


def build_file_unique_id(doc):
    """Build file unique identifier."""
    doc["unique_id"] = "{0}_{1}".format(doc["bucket_id"], doc["file_id"])
    return doc


def build_record_unique_id(doc):
    """Build record unique identifier."""
    doc["unique_id"] = "{0}_{1}".format(doc["pid_type"], doc["pid_value"])
    return doc


def record_view_event_builder(event, sender_app, pid=None, record=None, **kwargs):
    """Build a record-view event."""
    event.update(
        {
            # When:
            "timestamp": datetime.datetime.utcnow().isoformat(),
            # What:
            "record_id": str(record.id),
            "pid_type": pid.pid_type,
            "pid_value": str(pid.pid_value),
            "referrer": request.referrer,
            # Who:
            **get_user(),
        }
    )
    return event
