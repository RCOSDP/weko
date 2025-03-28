# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Serialization response factories.

Responsible for creating a HTTP response given the output of a serializer.
"""

from __future__ import absolute_import, print_function

import asyncio
from concurrent.futures.thread import ThreadPoolExecutor

from flask import current_app, abort
from weko_admin.models import AdminSettings
from weko_records.api import ItemTypes, Mapping
from weko_records.utils import sort_meta_data_by_options


def record_responsify(serializer, mimetype):
    """Create a Records-REST response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.
    """
    def view(pid, record, code=200, headers=None, links_factory=None):
        if pid and record:
            response = current_app.response_class(
                serializer.serialize(pid, record, links_factory=links_factory),
                mimetype=mimetype)
            response.set_etag(str(record.revision_id))
            response.last_modified = record.updated
        else:
            response = current_app.response_class(abort(500), mimetype=mimetype)
            response.status_code = code
        
        if headers is not None:
            response.headers.extend(headers)

        if links_factory is not None:
            add_link_header(response, links_factory(pid))

        return response

    return view


def search_responsify(serializer, mimetype):
    """Create a Records-REST search result response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.
    """
    async def __format_item_list(records: list):
        """Format item which is displayed in the item list.

        Args:
            records (list): Search results.
        """
        settings = AdminSettings.get('items_display_settings')
        item_type_id_lst = set()
        for record in records:
            item_type_id_lst.add(
                record['_source'].get('item_type_id')
                or record['_source']['_item_metadata'].get('item_type_id'))
        item_type_id_lst = list(item_type_id_lst)

        item_type_dict = __get_item_types(item_type_id_lst)
        tasks = []
        for record in records:
            task = asyncio.ensure_future(
                sort_meta_data_by_options(
                    record, settings,
                    item_type_dict.get(str(
                        record['_source'].get('item_type_id')
                        or record['_source']['_item_metadata'].get(
                            'item_type_id'))
                    )
                )
            )
            tasks.append(task)
        await asyncio.gather(*tasks)

    def __get_item_types(ids: list) -> dict:
        """Get item types base on list of item type id.

        Args:
            ids (list): Item Type identifier list.
        Returns:
            dict: Item types.

        """
        item_types = ItemTypes.get_records(ids)
        item_type_dict = {}
        for item_type in item_types:
            item_type_dict[str(item_type.model.id)] = item_type
        return item_type_dict

    def view(pid_fetcher, search_result, code=200, headers=None, links=None,
             item_links_factory=None):
        if search_result['hits']['hits'] and \
                len(search_result['hits']['hits']) > 0:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.SelectorEventLoop())
                loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=10):
                task = asyncio.gather(
                    __format_item_list(
                        search_result['hits']['hits']
                    )
                )
                loop.run_until_complete(task)
        response = current_app.response_class(
            serializer.serialize_search(pid_fetcher, search_result,
                                        links=links,
                                        item_links_factory=item_links_factory),
            mimetype=mimetype)
        response.status_code = code
        if headers is not None:
            response.headers.extend(headers)

        if links is not None:
            add_link_header(response, links)

        return response

    return view


def add_link_header(response, links):
    """Add a Link HTTP header to a REST response.

    :param response: REST response instance
    :param links: Dictionary of links
    """
    if links is not None:
        response.headers.extend({
            'Link': ', '.join([
                '<{0}>; rel="{1}"'.format(l, r) for r, l in links.items()])
        })
