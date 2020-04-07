# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO Deposit Schema V1."""
from functools import partial

from flask import url_for
from marshmallow import Schema, fields, post_load

external_url_for = partial(url_for, _external=True)
"""Helper for external url_for link generation."""


class DepositSchemaV1(Schema):
    """TODO:DepositSchemaV1."""

    id = fields.Integer(attribute='pid.pid_value', dump_only=True)
    links = fields.Method('dump_links', dump_only=True)
    created = fields.Str(dump_only=True)

    def dump_links(self, obj):
        """Dump links."""
        links = obj.get('links', {})
        m = obj.get('metadata')
        bucket_id = m.get('_buckets', {}).get('deposit')

        if bucket_id:
            links['bucket'] = external_url_for(
                'invenio_files_rest.bucket_api', bucket_id=bucket_id)
        return links

    @post_load(pass_many=False)
    def remove_envelope(self, data):
        """Post process data."""
        # Remove envelope
        if 'metadata' in data:
            data = data['metadata']

        return data
