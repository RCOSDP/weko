# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent Identifier field."""

from marshmallow import missing

from invenio_records_rest.schemas.fields.generated import GenFunction


def pid_from_context(_, context):
    """Get PID from marshmallow context."""
    pid = (context or {}).get('pid')
    return pid.pid_value if pid else missing


class PersistentIdentifier(GenFunction):
    """Field to handle PersistentIdentifiers in records.

    .. versionadded:: 1.2.0
    """

    def __init__(self, *args, **kwargs):
        """Initialize field."""
        super(PersistentIdentifier, self).__init__(
            serialize=pid_from_context, deserialize=pid_from_context,
            *args, **kwargs)
