# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow loader for record deserialization.

Use marshmallow schema to transform a JSON sent via the REST API from an
external to an internal JSON presentation. The marshmallow schema further
allows for advanced data validation.
"""

import json

from flask import request
from invenio_rest.errors import RESTValidationError
from marshmallow import ValidationError

from ..utils import marshmallow_major_version


def _flatten_marshmallow_errors(errors, parents=()):
    """Flatten marshmallow errors."""
    res = []
    for field, error in errors.items():
        if isinstance(error, list):
            res.append(
                dict(
                    parents=parents,
                    field=field,
                    message=" ".join(str(x) for x in error),
                )
            )
        elif isinstance(error, dict):
            res.extend(_flatten_marshmallow_errors(error, parents=parents + (field,)))
    return res


class MarshmallowErrors(RESTValidationError):
    """Marshmallow validation errors.

    Responsible for formatting a JSON response to a user when a validation
    error happens.
    """

    def __init__(self, errors):
        """Store marshmallow errors."""
        self.errors = _flatten_marshmallow_errors(errors)
        super().__init__()

    def __str__(self):
        """Print exception with errors."""
        return "{base}. Encountered errors: {errors}".format(
            base=super().__str__(), errors=self.errors
        )

    def get_body(self, environ=None, scope=None):
        """Get the request body."""
        body = dict(
            status=self.code,
            message=self.get_description(environ),
        )

        if self.errors:
            body["errors"] = self.errors

        return json.dumps(body)


def marshmallow_loader(schema_class):
    """Marshmallow loader for JSON requests."""

    def json_loader():
        request_json = request.get_json()

        context = {}
        pid_data = request.view_args.get("pid_value")
        if pid_data:
            pid, record = pid_data.data
            context["pid"] = pid
            context["record"] = record
        if marshmallow_major_version < 3:
            result = schema_class(context=context).load(request_json)
            if result.errors:
                raise MarshmallowErrors(result.errors)
        else:
            # From Marshmallow 3 the errors on .load() are being raised rather
            # than returned. To adjust this change to our flow we catch these
            # errors and reraise them instead.
            try:
                result = schema_class(context=context).load(request_json)
            except ValidationError as error:
                raise MarshmallowErrors(error.messages)

        return result.data

    return json_loader


def json_patch_loader():
    """Dummy loader for json-patch requests."""
    return request.get_json(force=True)
