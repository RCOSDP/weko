# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
# Copyright (C) 2021-2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Implement funtions for managing OAI-PMH resumption token."""

import random

from flask import current_app
from invenio_rest.serializer import BaseSchema
from itsdangerous import URLSafeTimedSerializer
from marshmallow import fields


def _schema_from_verb(verb, partial=False):
    """Return an instance of schema for given verb."""
    from .verbs import Verbs

    return getattr(Verbs, verb)(partial=partial)


def serialize(pagination, **kwargs):
    """Return resumption token serializer."""
    if not pagination.has_next:
        return

    token_builder = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt=kwargs["verb"],
    )
    schema = _schema_from_verb(kwargs["verb"], partial=False)
    schema_kwargs = kwargs.copy()
    schema_kwargs.update(schema_kwargs.get("resumptionToken", {}))

    data = dict(
        seed=random.random(),
        page=pagination.next_num,
        kwargs=schema.dump(schema_kwargs).data,
    )
    scroll_id = getattr(pagination, "_scroll_id", None)
    if scroll_id:
        data["scroll_id"] = scroll_id

    return token_builder.dumps(data)


class ResumptionToken(fields.Field):
    """Resumption token validator."""

    def _deserialize(self, value, attr, data, **kwargs):
        """Serialize resumption token."""
        token_builder = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"],
            salt=data["verb"],
        )
        result = token_builder.loads(
            value, max_age=current_app.config["OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME"]
        )
        result["token"] = value

        schema_kwargs = result["kwargs"].copy()
        schema_kwargs["verb"] = data["verb"]

        result["kwargs"] = _schema_from_verb(data["verb"]).load(schema_kwargs).data
        return result


class ResumptionTokenSchema(BaseSchema):
    """Schema with resumption token."""

    resumptionToken = ResumptionToken(required=True, load_only=True)

    def load(self, data, many=None, partial=None):
        """Deserialize a data structure to an object."""
        result = super(ResumptionTokenSchema, self).load(
            data, many=many, partial=partial
        )
        result.data.get("resumptionToken", {}).update(
            result.data.get("resumptionToken", {}).get("kwargs", {})
        )
        return result
