# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Base class for Marshmallow based serializers."""

from ..schemas import RecordSchemaJSONV1
from .base import PreprocessorMixin, TransformerMixinInterface


class MarshmallowMixin(PreprocessorMixin):
    """Base class for marshmallow serializers."""

    def __init__(self, schema_class=RecordSchemaJSONV1, **kwargs):
        """Initialize record."""
        self.schema_class = schema_class
        super().__init__(**kwargs)

    def dump(self, obj, context=None):
        """Serialize object with schema."""
        return self.schema_class(context=context).dump(obj).data

    def transform_record(self, pid, record, links_factory=None, **kwargs):
        """Transform record into an intermediate representation."""
        context = kwargs.get("marshmallow_context", {})
        context.setdefault("pid", pid)
        context.setdefault("record", record)
        return self.dump(
            self.preprocess_record(pid, record, links_factory=links_factory, **kwargs),
            context,
        )

    def transform_search_hit(self, pid, record_hit, links_factory=None, **kwargs):
        """Transform search result hit into an intermediate representation."""
        context = kwargs.get("marshmallow_context", {})
        context.setdefault("pid", pid)
        context.setdefault("record", record_hit["_source"])
        return self.dump(
            self.preprocess_search_hit(
                pid, record_hit, links_factory=links_factory, **kwargs
            ),
            context,
        )


MarshmallowSerializer = MarshmallowMixin
"""Marshmallow Serializer, only for backward compatibility."""
