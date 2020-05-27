# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask-Admin filter utilities."""

from __future__ import absolute_import, print_function

import uuid

from flask_admin.contrib.sqla import filters
from flask_admin.model.filters import convert


class UUIDEqualFilter(filters.FilterEqual):
    """UUID aware filter."""

    def apply(self, query, value, alias):
        """Convert UUID.

        :param query: SQLAlchemy query object.
        :param value: UUID value.
        :param alias: Alias of the column.
        :returns: Filtered query matching the UUID value.
        """
        try:
            value = uuid.UUID(value)
            return query.filter(self.column == value)
        except ValueError:
            return query


class FilterConverter(filters.FilterConverter):
    """Filter converter for dealing with UUIDs and variants."""

    uuid_filters = (UUIDEqualFilter, )

    @convert('uuidtype')
    def conv_uuid(self, column, name, **kwargs):
        """Convert UUID filter."""
        return [f(column, name, **kwargs) for f in self.uuid_filters]

    @convert('variant')
    def conv_variant(self, column, name, **kwargs):
        """Convert variants."""
        return self.convert(str(column.type), column, name, **kwargs)
