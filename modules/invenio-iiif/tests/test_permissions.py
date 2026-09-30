# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of IIIF permissions."""

from mock import MagicMock
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_records.api import Record
from invenio_records_files.models import RecordsBuckets

from invenio_iiif.permissions import (
    _get_file_metadata,
    _get_record_of_bucket,
    iiif_object_permission_factory,
)

# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_permissions.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp


def _record_json(version_id):
    return {
        "recid": "1",
        "item_1": {
            "attribute_name": "Title",
            "attribute_value_mlt": [{"subitem_title": "title"}],
        },
        "item_2": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {"filename": "other.png", "version_id": "other"},
                {
                    "filename": "image.png",
                    "version_id": str(version_id),
                    "accessrole": "open_access",
                },
            ],
        },
    }


def _patch_record_permissions(mocker, page=True, file=True):
    page_factory = mocker.patch(
        "weko_records_ui.permissions.page_permission_factory",
        return_value=MagicMock(can=MagicMock(return_value=page)),
    )
    file_check = mocker.patch(
        "weko_records_ui.permissions.check_file_download_permission",
        return_value=file,
    )
    return page_factory, file_check


def _patch_files_rest_permission(mocker, can):
    return mocker.patch(
        "invenio_files_rest.proxies.current_permission_factory",
        MagicMock(return_value=MagicMock(can=MagicMock(return_value=can))),
    )


def _create_object(db):
    bucket = Bucket.create()
    obj = ObjectVersion.create(bucket, "image.png")
    db.session.commit()
    return bucket, obj


# def _get_file_metadata(record, version_id):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_permissions.py::test_get_file_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_get_file_metadata():
    record = _record_json("v1")
    assert _get_file_metadata(record, "v1")["filename"] == "image.png"
    assert _get_file_metadata(record, "v2") is None
    assert _get_file_metadata({"item_1": "value"}, "v1") is None


# def _get_record_of_bucket(bucket_id):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_permissions.py::test_get_record_of_bucket -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_get_record_of_bucket(app, db, location):
    bucket, obj = _create_object(db)
    assert _get_record_of_bucket(bucket.id) is None

    record = Record.create(_record_json(obj.version_id))
    RecordsBuckets.create(record=record.model, bucket=bucket)
    db.session.commit()
    result = _get_record_of_bucket(bucket.id)
    assert result["recid"] == "1"


# def iiif_object_permission_factory(obj, record=None):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_permissions.py::test_iiif_object_permission_factory_record_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_iiif_object_permission_factory_record_file(app, db, location, mocker):
    bucket, obj = _create_object(db)
    record = Record.create(_record_json(obj.version_id))
    RecordsBuckets.create(record=record.model, bucket=bucket)
    db.session.commit()
    # The files-rest permission is not used for a file of a record.
    _patch_files_rest_permission(mocker, True)

    page_factory, file_check = _patch_record_permissions(mocker, True, True)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj).can() is True
    assert page_factory.call_args[0][0]["recid"] == "1"
    assert file_check.call_args[0][1]["filename"] == "image.png"

    _patch_record_permissions(mocker, page=False, file=True)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj).can() is False

    _patch_record_permissions(mocker, page=True, file=False)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj).can() is False


# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_permissions.py::test_iiif_object_permission_factory_given_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_iiif_object_permission_factory_given_record(app, db, location, mocker):
    bucket, obj = _create_object(db)
    record = _record_json(obj.version_id)
    _patch_files_rest_permission(mocker, True)

    _patch_record_permissions(mocker, True, True)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj, record=record).can() is True

    _patch_record_permissions(mocker, True, False)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj, record=record).can() is False


# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_permissions.py::test_iiif_object_permission_factory_not_record_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_iiif_object_permission_factory_not_record_file(app, db, location, mocker):
    bucket, obj = _create_object(db)
    page_factory, file_check = _patch_record_permissions(mocker, True, True)

    # No record is linked to the bucket.
    files_rest = _patch_files_rest_permission(mocker, False)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj).can() is False
    files_rest.assert_called_with(obj, "object-read")

    files_rest = _patch_files_rest_permission(mocker, True)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj).can() is True

    # The object is not a file of the record.
    record = Record.create(_record_json("other-version"))
    RecordsBuckets.create(record=record.model, bucket=bucket)
    db.session.commit()
    files_rest = _patch_files_rest_permission(mocker, False)
    with app.test_request_context():
        assert iiif_object_permission_factory(obj).can() is False
    page_factory.assert_not_called()
    file_check.assert_not_called()
