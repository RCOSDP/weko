# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test serializer."""

from marshmallow import fields

from invenio_files_rest.serializer import (
    BaseSchema,
    json_serializer,
    serializer_mapping,
)


def test_serialize_pretty(app):
    """Test pretty JSON."""

    class TestSchema(BaseSchema):
        title = fields.Str(attribute="title")

    data = {"title": "test"}
    context = {
        "bucket": "11111111-1111-1111-1111-111111111111",
        "class": "TestSchema",
        "many": False,
    }

    serializer_mapping["TestSchema"] = TestSchema

    # TODO This test should be checked if it shouldn't have
    #  BaseSchema instead of Schema
    with app.test_request_context():
        assert json_serializer(data=data, context=context).data == b'{"title":"test"}'

    with app.test_request_context("/?prettyprint=1"):
        assert (
            json_serializer(data=data, context=context).data
            == b'{\n  "title": "test"\n}'
        )
