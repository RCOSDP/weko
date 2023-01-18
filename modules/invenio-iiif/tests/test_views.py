# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of image opener."""

from __future__ import absolute_import, print_function

import pytest
from mock import patch
from werkzeug.exceptions import HTTPException
from flask import url_for,make_response
from flask_iiif.utils import iiif_image_url

from invenio_pidstore.errors import (
    PIDDeletedError,
    PIDDoesNotExistError,
    PIDMissingObjectError,
    PIDRedirectedError,
)
from werkzeug.routing import BuildError
from invenio_iiif.views import create_blueprint_from_app,create_blueprint,create_url_rule,manifest_view

# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp

def test_get_image(client, image_object, image_uuid):
    """Test retrieval of image."""
    print(iiif_image_url(uuid=image_uuid, size='200,200'))
    #with pytest.raises(AttributeError):
    res = client.get(iiif_image_url(uuid=image_uuid, size='200,200'))
    assert res.status_code == 200
    assert res.content_type == 'image/png'


def test_image_info(client, image_object, image_uuid):
    """Test retrieval of image info."""
    res = client.get(
        url_for('iiifimageinfo', version='v2', uuid=image_uuid))
    assert res.status_code == 200
    assert res.content_type == 'application/json'


def test_get_restricted_image(client, image_object, image_uuid):
    """Test retrieval of image."""
    image_url = iiif_image_url(uuid=image_uuid, size='200,200')
    # First request with deny (cache miss) fails
    client.get(
        image_url,
        headers={'Authorization': 'deny'}
    )
    # First request with allow (cache miss) succeeds
    client.get(image_url)
    # Second request with deny (cache hit) also fails
    client.get(
        image_url,
        headers={'Authorization': 'deny'}
    )


def test_get_restricted_image_info(client, image_object, image_uuid):
    """Test retrieval of image info."""
    info_url = url_for('iiifimageinfo', version='v2', uuid=image_uuid)
    # First request with deny (cache miss) fails
    client.get(
        info_url,
        headers={'Authorization': 'deny'}
    )
    # First request with allow (cache miss) pass
    client.get(info_url)
    # Second request with deny (cache hit) fails
    client.get(
        info_url,
        headers={'Authorization': 'deny'}
    )


#def create_blueprint_from_app(app):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_views.py::test_create_blueprint_from_app -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_create_blueprint_from_app(app, mocker):
    app.config.update(
        IIIF_MANIFEST_ENDPOINTS = {
            "recid": {
                "pid_type": "recid",
                "route": "/records/<pid_value>",
            },
            "pid": {
                "pid_type":"recid"
            }
        }
    )
    mock_create = mocker.patch("invenio_iiif.views.create_blueprint")
    create_blueprint_from_app(app)
    test = {
        "recid": {
            "pid_type": "recid",
            "route": "iiif/v2/records/<pid_value>/manifest.json",
        },
        "pid":{"pid_type":"recid"}
    }
    mock_create.assert_called_with(test)


#def create_blueprint(endpoints):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_views.py::test_create_blueprint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_create_blueprint():
    end_points = {
        "recid": {
            "pid_type": "recid",
            "route": "iiif/v2/records/<pid_value>/manifest.json",
        },
    }
    result = create_blueprint(end_points)
    
    
#def create_url_rule(
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_views.py::test_create_url_rule -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_create_url_rule():
    from invenio_iiif.manifest import IIIFManifest
    endpoint = "recid"
    route="/test1/test2"
    pid_type="recid"
    
    result = create_url_rule(endpoint,route=route,pid_type=pid_type)
    assert result["endpoint"] == "recid"
    assert result["rule"] == "/test1/test2"
    assert result["methods"] == ["GET"]
    
#def manifest_view(
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_views.py::test_manifest_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
def test_manifest_view(app,records,mocker):
    from invenio_pidstore.resolver import Resolver
    from invenio_iiif.manifest import IIIFManifest
    from invenio_records.api import Record
    pid_value=records[0][0].pid_value
    resolver=Resolver(pid_type="recid",object_type="rec",getter=Record.get_record)
    permission_factory=None
    manifest_class=IIIFManifest
    mocker.patch("invenio_iiif.views.url_for",side_effect=lambda x,pid_value:x+pid_value)
    with app.test_request_context("/test"):
        with patch("invenio_iiif.views.Resolver.resolve",side_effect=PIDDoesNotExistError(records[0][0].pid_type,records[0][0].pid_value)):
            with pytest.raises(HTTPException) as httperror:
                result = manifest_view(pid_value,resolver,permission_factory,manifest_class)
            assert httperror.value.code == 404
        with patch("invenio_iiif.views.Resolver.resolve",side_effect=PIDMissingObjectError("error_pid")):
            with pytest.raises(HTTPException) as httperror:
                result = manifest_view(pid_value,resolver,permission_factory,manifest_class)
            assert httperror.value.code == 500
        
        with patch("invenio_iiif.views.Resolver.resolve",side_effect=PIDRedirectedError("error_pid",records[0][0])):
            mock_redirect = mocker.patch("invenio_iiif.views.redirect",return_value=make_response())
            result = manifest_view(pid_value,resolver,permission_factory,manifest_class)
            mock_redirect.assert_called_with(".recid1")
            with patch("invenio_iiif.views.redirect",side_effect=BuildError("endpoint","value","method")):
                with pytest.raises(HTTPException) as httperror:
                    result = manifest_view(pid_value,resolver,permission_factory,manifest_class)
                assert httperror.value.code == 500

        result = manifest_view(pid_value,resolver,permission_factory,manifest_class)
        assert result.status_code == 204
        
    