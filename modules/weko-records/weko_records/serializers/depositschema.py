# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO Deposit Schema V1."""
from functools import partial

from flask import url_for
from marshmallow import Schema, fields, post_load

external_url_for = partial(url_for, _external=True)
"""Helper for external url_for link generation."""


class DepositSchemaV1(Schema):
    """"""

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
