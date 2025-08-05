# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signposting is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import pytest
from unittest.mock import patch
from flask import url_for
from sqlalchemy.exc import SQLAlchemyError

from weko_signposting.api import get_record_doi

from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_signposting tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-signposting/.tox/c1/tmp

# def requested_signposting(pid, record, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_signposting tests/test_api.py::test_requested_signposting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-signposting/.tox/c1/tmp
def test_requested_signposting(app, client, db_records, mocker):
    depid, recid, parent, doi, record, item = db_records[0]
    expected = json_data("data/link_str.json")

    mock_permalink = mocker.patch("weko_signposting.api.get_record_doi")
    mock_permalink.return_value = None

    url = url_for("invenio_records_ui.recid_signposting", pid_value=recid.pid_value)
    res = client.head(url)

    expected_link = expected["links"][0]
    result = res.headers["Link"]
    assert result == expected_link
    assert res.status_code == 200

    mock_permalink.return_value="https://doi.org/10.xyz/0000000001"

    res = client.head(url)

    expected_link = expected["links"][1]
    result = res.headers["Link"]
    assert result == expected_link
    assert res.status_code == 200


# def get_record_doi(recid):
# .tox/c1/bin/pytest --cov=weko_signposting tests/test_api.py::test_get_record_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-signposting/.tox/c1/tmp
def test_get_record_doi(app, client, db, db_records, mocker):
    depid, recid, parent, doi, record, item = db_records[0]

    assert get_record_doi(recid.pid_value) == doi.pid_value

    doi.delete()
    db.session.commit()
    assert get_record_doi(recid.pid_value) is None

    assert get_record_doi("invalid:recid") is None

    with patch("weko_signposting.api.PersistentIdentifier.get") as mock_get:
        mock_get.side_effect = SQLAlchemyError("Database error")

        assert get_record_doi(recid.pid_value) is None

