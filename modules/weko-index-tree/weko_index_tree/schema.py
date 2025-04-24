# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Index-Tree is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-index-tree."""


from datetime import datetime
from marshmallow import Schema, ValidationError, fields


def validate_role_or_group(value):
    """Validate the role or group."""
    if not value:
        return

    list_value = value.split(',')
    for item in list_value:
        if not item.replace("-", "").isdecimal():
            raise ValidationError("Not a valid role or group format.")


def validate_public_date(value):
    """Validate the public date."""
    if not value:
        return

    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError:
        raise ValidationError("Not a valid date format. Use YYYYMMDD.")


class IndexesSchemaBase(Schema):
    """"Indexes schema.

    Indexes schema for the index tree.
    This is based on weko_index_tree.models.Index.

    """
    index_name = fields.String()
    """Name of the index."""

    index_name_english = fields.String(validate=lambda x: len(x) > 0)
    """English Name of the index."""

    index_link_name = fields.String()
    """Name of the index link."""

    index_link_name_english = fields.String(validate=lambda x: len(x) > 0)
    """English Name of the index link."""

    index_link_enabled = fields.Boolean()
    """Index link enable flag."""

    comment = fields.String()
    """Comment of the index."""

    more_check = fields.Boolean()
    """More Status of the index."""

    display_no = fields.Integer()
    """Display number of the index."""

    harvest_public_state = fields.Boolean()
    """Harvest public State of the index."""

    display_format = fields.String()
    """The Format of Search Resault."""

    public_state = fields.Boolean()
    """Public State of the index."""

    public_date = fields.String(validate=validate_public_date)
    """Public Date of the index."""

    rss_status = fields.Boolean()
    """RSS Icon Status of the index."""

    coverpage_state = fields.Boolean()
    """PDF Cover Page State of the index."""

    browsing_role = fields.String(validate=validate_role_or_group)
    """Browsing role of the index."""

    contribute_role = fields.String(validate=validate_role_or_group)
    """Contribute Role of the index."""

    browsing_group = fields.String(validate=validate_role_or_group)
    """Browsing Group of the index."""

    contribute_group = fields.String(validate=validate_role_or_group)
    """Contribute Group of the index."""

    online_issn = fields.String()
    """Online ISSN of the index."""

    class Meta:
        strict = True

class IndexCreateSchema(IndexesSchemaBase):
    """Index create schema."""

    parent = fields.Integer(required=True)
    """Parent Information of the index. Required for creation."""

    class Meta:
        strict = True


class IndexUpdateSchema(IndexesSchemaBase):
    """Index update schema."""

    parent = fields.Integer()
    """Parent Information of the index."""

    class Meta:
        strict = True


class IndexCreateRequestSchema(Schema):
    """Index management request schema.

    Schema for weko_index_tree.rest.IndexManagementAPI.
    """

    index = fields.Nested(IndexCreateSchema, required=True)
    """Index field."""

    class Meta:
        strict = True

class IndexUpdateRequestSchema(Schema):
    """Index management request schema.

    Schema for weko_index_tree.rest.IndexManagementAPI.
    """

    index = fields.Nested(IndexUpdateSchema, required=True)
    """Index field."""

    class Meta:
        strict = True
