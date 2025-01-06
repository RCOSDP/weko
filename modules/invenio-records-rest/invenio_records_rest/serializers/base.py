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
import pickle

import pytz
import traceback

from flask import current_app
from weko_records.api import Mapping

from invenio_records_rest.config import RECORDS_REST_DEFAULT_MAPPING_DICT


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
        def get_keys(arr):
            """Get keys."""
            result = []
            for i in arr:
                result.append(i)
                if i != arr[-1]:
                    result.append(0)
            return result

        def get_mapping(item_type_id):
            """Get keys of metadata record by mapping."""
            # Get default mapping key and lang from config (defaults are None).
            from weko_items_ui.utils import get_options_and_order_list, get_hide_list_by_schema_form
            from weko_records.api import ItemTypes

            mapping_dict = RECORDS_REST_DEFAULT_MAPPING_DICT
            # Get mapping of this record.
            item_type = ItemTypes.get_by_id(item_type_id)
            item_type_list = None
            hide_list = []
            if item_type:
                item_type_list = item_type.render.get('table_row')
                hide_list = get_hide_list_by_schema_form(item_type)
                meta_option, item_type_mapping = get_options_and_order_list(
                    item_type_id, item_type_data=ItemTypes(item_type.schema, model=item_type))
            else:
                meta_option, item_type_mapping = get_options_and_order_list(item_type_id)
            if not item_type_mapping or not item_type_list:
                return mapping_dict
            # Update default mapping key and lang by mapping of this record.
            identifier = 'system_identifier'
            for k in item_type_list:
                if k in item_type_mapping:
                    v = item_type_mapping.get(k)
                    prop_hidden = meta_option.get(k, {}).get('option', {}).get('hidden', False)
                    if not v or not isinstance(v.get('jpcoar_mapping'), dict) \
                            or prop_hidden:
                        continue
                    for k1, v1 in v.get('jpcoar_mapping').items():
                        skip_flag = False
                        for h in hide_list:
                            if h.startswith(k) and \
                                    (('@value' in v1.keys() and 
                                    h.endswith(v1.get('@value').split('.')[-1])) or \
                                    ('creatorName' in v1.keys() and 
                                    h.endswith(v1.get('creatorName', {}).get('@value').split('.')[-1]))):
                                skip_flag = True
                        if skip_flag:
                            continue
                        for k2, v2 in mapping_dict.items():
                            if k1 != k2.split(':')[1] or \
                                    not isinstance(v1, dict) or \
                                    mapping_dict[k2]:
                                continue
                            key = identifier if identifier in k else k
                            key_arr = ['metadata', key, 'attribute_value_mlt', 0]
                            lang_arr = key_arr.copy()
                            if k1 == 'creator':
                                name = v1.get('creatorName', {})
                                # Set all key for __lang
                                attr = name.get('@attributes', {})
                                xml_lang = attr.get('xml:lang', '').split('.')
                                lang_arr.extend(get_keys(xml_lang))
                                # Set all key for key
                                name_arr = name.get('@value', '').split('.')
                                key_arr.extend(get_keys(name_arr))
                            elif '.' in v1.get('@value', ''):
                                # Set key for __lang
                                attr = v1.get('@attributes', {})
                                xml_lang = attr.get('xml:lang', '').split('.')
                                lang_arr.extend(get_keys(xml_lang))
                                # Set all key for key
                                name_arr = v1.get('@value', '').split('.')
                                key_arr.extend(get_keys(name_arr))
                            else:
                                # Set key for __lang
                                attr = v1.get('@attributes', {})
                                lang_arr.append(attr.get('xml:lang', ''))
                                # Set all key for key
                                key_arr.append(v1.get('@value', ''))
                            mapping_dict[k2] = key_arr
                            mapping_dict['{}__lang'.format(k2)] = lang_arr
            return mapping_dict

        links_factory = links_factory or (lambda x, record=None, **k: dict())
        
        metadata = pickle.loads(pickle.dumps(record.replace_refs(), -1)) if self.replace_refs \
            else record.dumps()
        # Get keys of metadata record by mapping.
        mapping_key_lang = get_mapping(metadata.get('item_type_id'))
        return dict(
            pid=pid,
            metadata=metadata,
            links=links_factory(pid, record=record, **kwargs),
            revision=record.revision_id,
            created=(pytz.utc.localize(record.created).isoformat()
                     if record.created else None),
            updated=(pytz.utc.localize(record.updated).isoformat()
                     if record.updated else None),
            mapping_dict=mapping_key_lang,
            record=record
        )

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None, **kwargs):
        """Prepare a record hit from Elasticsearch for serialization."""
        links_factory = links_factory or (lambda x, **k: dict())
        record = dict(
            pid=pid,
            metadata=record_hit.get('_source', {}),
            links=links_factory(pid, record_hit=record_hit, **kwargs),
            revision=record_hit.get('_version', 0),
            created=None,
            updated=None,
        )
        # Move created/updated attrs from source to object.
        for key in ['_created', '_updated']:
            if key in record['metadata']:
                record[key[1:]] = record['metadata'][key]
                del record['metadata'][key]
        return record
