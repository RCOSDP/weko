# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow based JSON-LD serializer for records."""

from __future__ import absolute_import, print_function

import copy

from flask import request
from pyld import jsonld

from .base import TransformerMixinInterface
from .json import JSONSerializer


class JSONLDTransformerMixin(TransformerMixinInterface):
    """JSON-LD serializer for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    def __init__(self, context, expanded=True, **kwargs):
        """Initialize record.

        :param context: JSON-LD context.
        :param schema_class: Marshmallow schema.
        :param expanded: expanded form, compacted else.
        :param replace_refs: replace the ``$ref`` keys within the JSON.
        """
        self.context = context
        self._expanded = expanded
        super(JSONLDTransformerMixin, self).__init__(**kwargs)

    @property
    def expanded(self):
        """Get JSON-LD expanded state."""
        # Ensure we can run outside a application/request context.
        if request:
            if 'expanded' in request.args:
                return True
            elif 'compacted' in request.args:
                return False
        return self._expanded

    def transform_jsonld(self, obj):
        """Compact JSON according to context."""
        rec = copy.deepcopy(obj)
        rec.update(self.context)
        compacted = jsonld.compact(rec, self.context)
        if not self.expanded:
            return compacted
        else:
            return jsonld.expand(compacted)[0]

    def transform_record(self, pid, record, links_factory=None, **kwargs):
        """Transform record into an intermediate representation."""
        result = super(JSONLDTransformerMixin, self).transform_record(
            pid, record, links_factory, **kwargs
        )
        return self.transform_jsonld(result)

    def transform_search_hit(self, pid, record_hit, links_factory=None,
                             **kwargs):
        """Transform search result hit into an intermediate representation."""
        result = super(JSONLDTransformerMixin, self).transform_search_hit(
            pid, record_hit, links_factory, **kwargs
        )
        return self.transform_jsonld(result)


class JSONLDSerializer(JSONLDTransformerMixin, JSONSerializer):
    """JSON-LD serializer for records supporting Marshmallow schemas."""
