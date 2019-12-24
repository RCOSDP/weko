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

from __future__ import absolute_import, print_function

import json

from flask import request
from invenio_rest.errors import RESTValidationError


def _flatten_marshmallow_errors(errors):
    """Flatten marshmallow errors."""
    res = []
    for field, error in errors.items():
        if isinstance(error, list):
            res.append(
                dict(field=field, message=' '.join([str(x) for x in error])))
        elif isinstance(error, dict):
            res.extend(_flatten_marshmallow_errors(error))
    return res


class MarshmallowErrors(RESTValidationError):
    """Marshmallow validation errors.

    Responsible for formatting a JSON response to a user when a validation
    error happens.
    """

    def __init__(self, errors):
        """Store marshmallow errors."""
        self._it = None
        self.errors = _flatten_marshmallow_errors(errors)
        super(MarshmallowErrors, self).__init__()

    def __str__(self):
        """Print exception with errors."""
        return "{base}. Encountered errors: {errors}".format(
            base=super(RESTValidationError, self).__str__(),
            errors=self.errors)

    def __iter__(self):
        """Get iterator."""
        self._it = iter(self.errors)
        return self

    def next(self):
        """Python 2.7 compatibility."""
        return self.__next__()  # pragma: no cover

    def __next__(self):
        """Get next file item."""
        return next(self._it)

    def get_body(self, environ=None):
        """Get the request body."""
        body = dict(
            status=self.code,
            message=self.get_description(environ),
        )

        if self.errors:
            body['errors'] = self.errors

        return json.dumps(body)


def marshmallow_loader(schema_class):
    """Marshmallow loader for JSON requests."""
    def json_loader():
        request_json = request.get_json()

        context = {}
        pid_data = request.view_args.get('pid_value')
        if pid_data:
            pid, _ = pid_data.data
            context['pid'] = pid

        result = schema_class(context=context).load(request_json)

        if result.errors:
            raise MarshmallowErrors(result.errors)
        return result.data
    return json_loader


def json_patch_loader():
    """Dummy loader for json-patch requests."""
    return request.get_json(force=True)
