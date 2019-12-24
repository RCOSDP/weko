# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test event builders."""

import datetime

from mock import patch

from invenio_stats.contrib.event_builders import file_download_event_builder, \
    record_view_event_builder
from invenio_stats.utils import get_user


class NewDate(datetime.datetime):
    @classmethod
    def utcnow(cls):
        return cls(2017, 1, 1)


headers = {'USER_AGENT':
           'Mozilla/5.0 (Windows NT 6.1; WOW64) '
           'AppleWebKit/537.36 (KHTML, like Gecko)'
           'Chrome/45.0.2454.101 Safari/537.36'}


def test_file_download_event_builder(app, mock_user_ctx,
                                     sequential_ids, objects):
    """Test the file-download event builder."""
    file_obj = objects[0]
    file_obj.bucket_id = sequential_ids[0]

    with app.test_request_context(headers=headers):
        event = {}
        with patch('datetime.datetime', NewDate):
            file_download_event_builder(event, app, file_obj)
        assert event == dict(
            # When:
            timestamp=NewDate.utcnow().isoformat(),
            # What:
            bucket_id=str(file_obj.bucket_id),
            file_id=str(file_obj.file_id),
            file_key=file_obj.key,
            size=file_obj.file.size,
            referrer=None,
            # Who:
            **get_user()
        )


def test_record_view_event_builder(app, mock_user_ctx, record, pid):
    """Test the record view event builder."""
    with app.test_request_context(headers=headers):
        event = {}
        with patch('datetime.datetime', NewDate):
            record_view_event_builder(event, app, pid, record)
        assert event == dict(
            # When:
            timestamp=NewDate.utcnow().isoformat(),
            # What:
            record_id=str(record.id),
            pid_type=pid.pid_type,
            pid_value=str(pid.pid_value),
            referrer=None,
            # Who:
            **get_user()
        )
