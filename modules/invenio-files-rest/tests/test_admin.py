# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin tests."""

from __future__ import absolute_import, print_function

import pytest
from invenio_admin import InvenioAdmin
from wtforms.validators import ValidationError
from unittest.mock import patch, MagicMock
from flask import get_flashed_messages
from sqlalchemy.exc import SQLAlchemyError

from invenio_files_rest.admin import require_slug, validate_uri, LocationModelView
from invenio_files_rest.models import Bucket, ObjectVersion, Location

def test_require_slug():
    """Test admin views."""
    class TestField(object):
        def __init__(self, data):
            self.data = data

    assert require_slug(None, TestField('aslug')) is None
    pytest.raises(ValidationError, require_slug, None, TestField('Not A Slug'))


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_admin.py::test_validate_uri -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_validate_uri(app):
    class TestField(object):
        def __init__(self, data):
            self.data = data
    class TestType(object):
            def __init__(self, type):
                self.data = type
    class TestForm(object):
        def __init__(self, type):
            self.type = TestType(type)

    # type is s3, uri is wrong uri -> not raise error
    assert validate_uri(TestForm("s3"),TestField('wrong_uri')) is None
    # type is s3_vh, uri is correct uri -> not raise error
    assert validate_uri(TestForm("s3_vh"),TestField('https://correct_uri')) is None
    # type is s3_vh, uri is wrong uri -> raise error
    pytest.raises(ValidationError, validate_uri, TestForm("s3_vh"), TestField("wrong_uri"))


def test_admin_views(app, db, dummy_location):
    """Test admin views."""
    app.config['SECRET_KEY'] = 'CHANGEME'
    InvenioAdmin(app, permission_factory=None, view_class_factory=lambda x: x)

    b1 = Bucket.create(location=dummy_location)
    obj = ObjectVersion.create(b1, 'test').set_location('placeuri', 1, 'chk')
    db.session.commit()

    with app.test_client() as client:
        res = client.get('/admin/bucket/')
        assert res.status_code == 200
        assert str(b1.id) in res.get_data(as_text=True)

        res = client.get('/admin/fileinstance/')
        assert res.status_code == 200
        assert str(obj.file_id) in res.get_data(as_text=True)

        res = client.get('/admin/location/')
        assert res.status_code == 200
        assert str(b1.location.name) in res.get_data(as_text=True)

        res = client.get('/admin/objectversion/')
        assert res.status_code == 200
        assert str(obj.version_id) in res.get_data(as_text=True)


def make_location(**overrides):
    defaults = dict(
        id=None,
        name="test",
        uri="s3://my-bucket/",
        default=False,
        s3_endpoint_url=None,
        s3_region_name=None,
        s3_signature_version="s3",
        s3_default_block_size=1,
        s3_maximum_number_of_parts=2,
        s3_url_expiration=10,
        s3_send_file_directly=False,
    )
    defaults.update(overrides)
    return Location(**defaults)


class TestLocationModelView():
    @pytest.mark.parametrize(
        "count, expected_cat, expected_msg",
        [
            (0, "warning", "No default location is set. Please configure one location as default."),
            (1, None, None),
            (2, "warning", "Multiple locations are set as default. Only one default location can be configured. Please correct the settings.")
        ],
        ids=["no_default", "ok", "multiple_defaults"])
    def test_index_view(self, app, db, mocker, count, expected_cat, expected_msg):
        view = LocationModelView(Location, db.session)

        with app.test_request_context("/admin/location/"):
            with patch("invenio_files_rest.admin.Location.query") as mock_query:
                mock_query.filter_by.return_value.count.return_value = count
                with mocker.patch("flask_admin.contrib.sqla.ModelView.index_view", return_value="OK") as _:
                    result = view.index_view()
                    assert result == "OK"
            messages = get_flashed_messages(with_categories=True)
            if expected_msg:
                assert (expected_cat, expected_msg) in messages
            else:
                assert messages == []

    def test_index_view_error(self, app, db, mocker):
        view = LocationModelView(Location, db.session)

        with app.test_request_context("/admin/location/"):
            with mocker.patch("flask_admin.contrib.sqla.ModelView.index_view", return_value="OK"):
                with patch("flask.current_app.logger") as mock_logger:
                    # case: sqlalchemy error
                    with patch("invenio_files_rest.admin.Location.query") as mock_query:
                        mock_query.filter_by.return_value.count.side_effect = SQLAlchemyError("test error")
                        result = view.index_view()

                        assert result == "OK"
                        messages = get_flashed_messages(with_categories=True)
                        assert messages == []
                        mock_logger.error.assert_called_with("Error while checking default locations: test error")

                    # case: unexpected error
                    with patch("invenio_files_rest.admin.Location", side_effect=Exception("test error")):
                        result = view.index_view()

                        assert result == "OK"
                        messages = get_flashed_messages(with_categories=True)
                        assert messages == []
                        mock_logger.exception.assert_called_with("unexpected error in index_view")

    def test_on_model_change_default_conflict(self, app, db):
        model = make_location(default=True)
        view = LocationModelView(Location, db.session)
        with patch("invenio_files_rest.admin.Location.query") as mock_query:
            mock_query.filter_by.return_value.first.return_value = object()
            with pytest.raises(ValidationError):
                view.on_model_change(None, model, True)

    def test_on_model_change_location_ok(self, app, db):
        model = make_location(id=1, default=True)
        view = LocationModelView(Location, db.session)
        with patch("invenio_files_rest.admin.Location.query") as mock_query:
            mock_query.filter_by.return_value.filter.return_value.first.return_value = None
            view.on_model_change(None, model, True)

    def test_on_model_change_default_false(self, app, db):
        model = make_location(default=False)
        view = LocationModelView(Location, db.session)
        with patch("invenio_files_rest.admin.Location.query") as mock_query:
            view.on_model_change(None, model, True)
            mock_query.assert_not_called()

    class DummyForm:
        def __init__(self, data=False, render_kw=None):
            self.default = MagicMock()
            self.default.data = data
            self.default.render_kw = render_kw

    @pytest.mark.parametrize(
        "obj, form_default, render_kw, query_result, expected",
        [
            (MagicMock(default=True), False, None, None, None),
            (MagicMock(default=False, id=1), False, None, None, None),
            (MagicMock(default=False, id=1), False, None, MagicMock(), {"disabled": True}),
            (MagicMock(default=False, id=1), False, {"class": "foo"}, MagicMock(), {"class": "foo", "disabled": True}),
            (MagicMock(default=False, id=1), True, None, MagicMock(), None),
            (None, False, None, None, None),
        ]
    )
    def test_handle_default_checkbox(self, app, db, obj, form_default, render_kw, query_result, expected):
        view = LocationModelView(Location, db.session)
        form = self.DummyForm(data=form_default, render_kw=render_kw)
        with patch("invenio_files_rest.admin.Location.query") as mock_query:
            mock_query.filter_by.return_value.first.return_value = query_result
            mock_query.filter_by.return_value.filter.return_value.first.return_value = query_result
            view._handle_default_checkbox(form, obj)
            assert form.default.render_kw == expected

    def test_handle_default_checkbox_error(self, app, db, mocker):
        view = LocationModelView(Location, db.session)
        form = self.DummyForm(data=False, render_kw=None)
        with patch("invenio_files_rest.admin.Location.query") as mock_query:
            mock_query.filter_by.side_effect = Exception("test error")
            with patch("flask.current_app.logger") as mock_logger:
                view._handle_default_checkbox(form, None)
                mock_logger.exception.assert_called_with("Error in _handle_default_checkbox")

    def test_create_form(self, app, db, mocker):
        view = LocationModelView(Location, db.session)
        dummy_form = MagicMock()
        mock_super = mocker.patch("flask_admin.contrib.sqla.ModelView.create_form")
        mock_super.return_value = dummy_form
        mock_handle = mocker.patch.object(view, "_handle_default_checkbox")

        result = view.create_form(obj="dummy_obj")

        assert result == dummy_form
        mock_super.assert_called_once_with("dummy_obj")
        mock_handle.assert_called_once_with(dummy_form, "dummy_obj")

    def test_edit_form(self, app, db, mocker):
        view = LocationModelView(Location, db.session)
        dummy_form = MagicMock()
        mock_super = mocker.patch("flask_admin.contrib.sqla.ModelView.edit_form")
        mock_super.return_value = dummy_form
        mock_handle = mocker.patch.object(view, "_handle_default_checkbox")

        result = view.edit_form(obj="dummy_obj")

        assert result == dummy_form
        mock_super.assert_called_once_with("dummy_obj")
        mock_handle.assert_called_once_with(dummy_form, "dummy_obj")