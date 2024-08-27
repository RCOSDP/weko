# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Trimmed string field."""

from marshmallow import fields


class TrimmedString(fields.String):
    """String field which strips whitespace the ends of the string."""

    def _deserialize(self, value, attr, data, **kwargs):
        """Deserialize string value."""
        value = super()._deserialize(value, attr, data, **kwargs)
        return value.strip()
