# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Implement funtions for managing OAI-PMH resumption token."""

import random

from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from marshmallow import Schema, fields


def _schema_from_verb(verb, partial=False):
    """Return an instance of schema for given verb."""
    from .verbs import Verbs
    return getattr(Verbs, verb)(partial=partial)


def serialize_file_response(data_index, data_count, **param):
    """ resumption token serializer when creating a response from a file.

        Args:
            data_index: Current INDEX.
            data_count: Overall number of data returned
            param: Parameters to be embedded in Token
        Returns:
            resumption token serializer
    """
    if data_index == data_count:
        return None

    token_builder = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY'],
        salt=param['verb'],
    )

    schema = _schema_from_verb(param['verb'], partial=False)
    data = dict(seed=random.random(), index=data_index,
                kwargs=schema.dump(param).data,
                metadataPrefix=param['metadataPrefix'],
                data_id=param['data_id'],
                until=param.get('until_time_str'),
                expirationDate=param['expirationDate'])
    data['from'] = param.get('from_time_str')
    data['set'] = param.get('set_spec')

    return token_builder.dumps(data)


def serialize(pagination, **kwargs):
    """Return resumption token serializer."""
    if not pagination.has_next:
        return

    token_builder = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY'],
        salt=kwargs['verb'],
    )
    schema = _schema_from_verb(kwargs['verb'], partial=False)
    data = dict(seed=random.random(), page=pagination.next_num,
                kwargs=schema.dump(kwargs).data)
    scroll_id = getattr(pagination, '_scroll_id', None)
    if scroll_id:
        data['scroll_id'] = scroll_id

    return token_builder.dumps(data)


class ResumptionToken(fields.Field):
    """Resumption token validator."""

    def _deserialize(self, value, attr, data):
        """Serialize resumption token."""
        token_builder = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY'],
            salt=data['verb'],
        )
        result = token_builder.loads(value, max_age=current_app.config[
            'OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME'])
        result['token'] = value
        result['kwargs'] = self.root.load(result['kwargs'], partial=True).data
        return result


class ResumptionTokenSchema(Schema):
    """Schema with resumption token."""

    resumptionToken = ResumptionToken(required=True, load_only=True)

    def load(self, data, many=None, partial=None):
        """Deserialize a data structure to an object."""
        result = super(ResumptionTokenSchema, self).load(
            data, many=many, partial=partial
        )
        result.data.update(
            result.data.get('resumptionToken', {}).get('kwargs', {})
        )
        return result
