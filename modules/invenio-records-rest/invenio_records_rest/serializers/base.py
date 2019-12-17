# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Mixin helper class for preprocessing records and search results."""

from __future__ import absolute_import, print_function

import copy

import pytz


class SerializerMixinInterface(object):
    """Mixin serializing records.

    A record serializer should inherit subclasses of
    - SerializerMixinInterface
    - TransformerMixinInterface
    - PreprocessorMixinInterface

    This class forwards its input to the transformer mixin and serializes its
    result.
    """

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record and persistent identifier.

        This method should delegate the record transformation to the
        transformer mixin's transform_record method.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        raise NotImplementedError()

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        This method should delegate each record search hit transformation
        to the transformer mixin's transform_search_hit method.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        raise NotImplementedError()

    def serialize_oaipmh(self, pid, record):
        """Serialize a single record for OAI-PMH.

        :param pid: The
            :py:class:`invenio_pidstore.models.PersistentIdentifier` instance.
        :param record: The :class:`invenio_records.api.Record` instance.
        :returns: The object serialized.
        """
        raise NotImplementedError()


class TransformerMixinInterface(object):
    """Mixin transforming records during serialization.

    This class should be mixed with a PreprocessorMixinInterface subclass and
    a SerializerMixinInterface subclass.

    This class transforms the dictionary returned by the preprocessor.
    """

    def transform_record(self, pid, record, links_factory=None, **kwargs):
        """Transform record into an intermediate representation.

        This method should delegate the record preprocessing to the
        preprocessor mixin's preprocess_record method.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        raise NotImplementedError()

    def transform_search_hit(self, pid, record_hit, links_factory=None,
                             **kwargs):
        """Transform search result hit into an intermediate representation.

        This method should delegate the record preprocessing to the
        preprocessor mixin's preprocess_search_hit method.

        :param pid: Persistent identifier instance.
        :param pid: Persistent identifier instance.
        :param record_hit: Record metadata retrieved via search.
        :param links_factory: Factory function for record links.
        """
        raise NotImplementedError()


class PreprocessorMixinInterface(object):
    """Mixin preprocessing records during serialization.

    This class should be mixed with a TransformerMixinInteface subclass and
    a SerializerMixinInterface subclass.

    This class builds a dictionary which is then transformed and serialized.
    """

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        raise NotImplementedError()

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None, **kwargs):
        """Prepare a record hit from Elasticsearch for serialization.

        :param pid: Persistent identifier instance.
        :param record_hit: Record metadata retrieved via search.
        :param links_factory: Factory function for record links.
        """
        raise NotImplementedError()


class PreprocessorMixin(PreprocessorMixinInterface):
    """Base class for serializers."""

    def __init__(self, replace_refs=False, **kwargs):
        """Constructor."""
        super(PreprocessorMixin, self).__init__(**kwargs)
        self.replace_refs = replace_refs

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        links_factory = links_factory or (lambda x, record=None, **k: dict())
        metadata = copy.deepcopy(record.replace_refs()) if self.replace_refs \
            else record.dumps()
        return dict(
            pid=pid,
            metadata=metadata,
            links=links_factory(pid, record=record, **kwargs),
            revision=record.revision_id,
            created=(pytz.utc.localize(record.created).isoformat()
                     if record.created else None),
            updated=(pytz.utc.localize(record.updated).isoformat()
                     if record.updated else None),
        )

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None, **kwargs):
        """Prepare a record hit from Elasticsearch for serialization."""
        links_factory = links_factory or (lambda x, **k: dict())
        record = dict(
            pid=pid,
            metadata=record_hit['_source'],
            links=links_factory(pid, record_hit=record_hit, **kwargs),
            revision=record_hit['_version'],
            created=None,
            updated=None,
        )
        # Move created/updated attrs from source to object.
        for key in ['_created', '_updated']:
            if key in record['metadata']:
                record[key[1:]] = record['metadata'][key]
                del record['metadata'][key]
        return record
