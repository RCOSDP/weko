# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow based JSON serializer for records."""

from __future__ import absolute_import, print_function

from flask import json, request

from .base import PreprocessorMixin, SerializerMixinInterface
from .marshmallow import MarshmallowMixin



class JSONSerializerMixin(SerializerMixinInterface):
    """Mixin serializing records as JSON."""

    @staticmethod
    def _format_args():
        """Get JSON dump indentation and separates."""
        if request and request.args.get('prettyprint'):
            return dict(
                indent=2,
                separators=(', ', ': '),
            )
        else:
            return dict(
                indent=None,
                separators=(',', ':'),
            )

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        from weko_records_ui.utils import hide_by_email,hide_by_itemtype

        record = hide_by_email(record, True)
        from weko_items_ui.utils import get_ignore_item
        list_hidden = get_ignore_item(record['item_type_id'])
        record = hide_by_itemtype(record, list_hidden)
        return json.dumps(
            self.transform_record(pid, record, links_factory, **kwargs),
            **self._format_args())

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        from weko_records_ui.utils import hide_by_email,hide_by_itemtype
        from weko_items_ui.utils import get_ignore_item                     
        from weko_deposit.api import WekoRecord
        from weko_records_ui.permissions import check_publish_status,check_created_id
        from weko_index_tree.utils import get_user_roles

        for hit in search_result['hits']['hits']:
            if '_source' in hit and '_item_metadata' in hit['_source']:
                hit['_source']['_item_metadata'] = hide_by_email(hit['_source']['_item_metadata'], True)
                list_hidden = get_ignore_item(hit['_source']['_item_metadata']['item_type_id'])
                hit['_source']['_item_metadata'] = hide_by_itemtype(hit['_source']['_item_metadata'], list_hidden)
            if '_source' in hit and len(hit['_source'].get('feedback_mail_list', [])) > 0:
                hit['_source']['feedback_mail_list'] = []
            if '_source' in hit and '_item_metadata' in hit['_source'] and hit['_source']['_item_metadata']:
                if 'control_number' in hit['_source']['_item_metadata']:
                    control_number=hit['_source']['_item_metadata']['control_number']
                    record = WekoRecord.get_record_by_pid(control_number)
                    is_admin = False
                    is_owner = False
                    roles = get_user_roles()
                    if roles[0]:
                        is_admin = True
                    if check_created_id(record):
                        is_owner = True
                    is_public = check_publish_status(record)
                    if check_created_id(record):
                        is_owner = True
                    is_public = check_publish_status(record)
                    if not is_public and not is_admin and not is_owner:
                        hit['_source']['_item_metadata']={}

        return json.dumps(dict(
            hits=dict(
                hits=[self.transform_search_hit(
                    pid_fetcher(hit['_id'], hit['_source']),
                    hit,
                    links_factory=item_links_factory,
                    **kwargs
                ) for hit in search_result['hits']['hits']],
                total=search_result['hits']['total'],
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        ), **self._format_args())


class JSONSerializer(JSONSerializerMixin, MarshmallowMixin, PreprocessorMixin):
    """Marshmallow based JSON serializer for records."""
