# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test permission helpers."""

import uuid
from unittest.mock import MagicMock, patch

from invenio_files_rest.permissions import get_guest_activity_bucket_ids


def _first(value):
    query = MagicMock()
    query.first.return_value = value
    return query


# def get_guest_activity_bucket_ids(token):
# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_permissions.py::test_get_guest_activity_bucket_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_get_guest_activity_bucket_ids(app):
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_records_files.models import RecordsBuckets
    from weko_workflow.models import GuestActivity

    item_id = uuid.uuid4()
    root_id = uuid.uuid4()
    bucket_ids = [uuid.uuid4(), uuid.uuid4()]

    guest_query = MagicMock()
    pid_query = MagicMock()
    rb_query = MagicMock()
    get_activity = 'weko_workflow.api.WorkActivity.get_activity_by_id'

    with patch.object(GuestActivity, 'query', guest_query), \
            patch.object(PersistentIdentifier, 'query', pid_query), \
            patch.object(RecordsBuckets, 'query', rb_query), \
            patch(get_activity) as mock_activity:
        # No token
        assert get_guest_activity_bucket_ids(None) == set()
        guest_query.filter_by.assert_not_called()

        # Unknown token
        guest_query.filter_by.return_value = _first(None)
        assert get_guest_activity_bucket_ids('token') == set()
        guest_query.filter_by.assert_called_with(token='token')

        # Activity without item
        guest_query.filter_by.return_value = _first(
            MagicMock(activity_id='A-00000000-00001'))
        mock_activity.return_value = MagicMock(item_id=None)
        assert get_guest_activity_bucket_ids('token') == set()
        mock_activity.assert_called_with('A-00000000-00001')

        mock_activity.return_value = None
        assert get_guest_activity_bucket_ids('token') == set()

        # Activity with item
        mock_activity.return_value = MagicMock(item_id=item_id)
        pid_query.filter_by.side_effect = [
            _first(MagicMock(pid_value='1.1')),
            _first(MagicMock(object_uuid=root_id)),
        ]
        rb_query.filter.return_value.all.return_value = [
            MagicMock(bucket_id=bucket_ids[0]),
            MagicMock(bucket_id=bucket_ids[1]),
        ]
        result = get_guest_activity_bucket_ids('token')
        assert result == {str(b) for b in bucket_ids}
        assert pid_query.filter_by.call_args_list[1][1] == dict(
            pid_type='recid', pid_value='1')

        # Item without PID
        pid_query.filter_by.side_effect = [_first(None)]
        rb_query.filter.return_value.all.return_value = [
            MagicMock(bucket_id=bucket_ids[0])]
        result = get_guest_activity_bucket_ids('token')
        assert result == {str(bucket_ids[0])}
