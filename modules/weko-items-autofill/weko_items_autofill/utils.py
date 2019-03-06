# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module of weko-items-autofill utils.."""
from functools import wraps
from invenio_cache import current_cache
from invenio_i18n.ext import current_i18n

from weko_records.api import Mapping
from .crossref_api import Works
from . import config


def is_update_cache():
    """Return True if Amazon Api has been updated."""
    return config.WEKO_ITEMS_AUTOFILL_AMAZON_API_UPDATED


def cached_api_json(timeout=50, key_prefix="amazon_json"):
    """Cache Api data
    :param timeout: Cache timeout
    :param key_prefix: prefix key
    :return:
    """

    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout,
                key_prefix=key_prefix + current_i18n.language,
                forced_update=is_update_cache,
            )
            return cache_fun(f)(*args, **kwargs)

        return wrapper

    return caching


def get_items_autofill(item_type_id):
    """
    :param item_type_id:
    :return: items autofill
    """
    items = dict()
    item_mapping_json = Mapping.get_record(item_type_id)
    jpcoar_metadata = _get_jpcoar_metadata(item_mapping_json)
    for jpcoar_item_name in config.WEKO_ITEMS_AUTOFILL_ITEMS_AUTOFILL:
        items[jpcoar_item_name] = get_autofill_item_id(jpcoar_item_name,
                                                       jpcoar_metadata)
    return items


def get_autofill_item_id(jpcoar_item_name, jpcoar_data):
    item_id = ""
    for k in jpcoar_data.keys():
        jpcoar_data_type = jpcoar_data[k]
        if isinstance(jpcoar_data_type, dict):
            if jpcoar_item_name in jpcoar_data_type.keys():
                return k
            elif jpcoar_data_type.get('relation'):
                if jpcoar_item_name in jpcoar_data_type.get('relation').keys():
                    return k

    return item_id


def _get_jpcoar_metadata(jpcoar_mapping_json):
    jpcoar_metadata = dict()
    for k in jpcoar_mapping_json.keys():
        jpcoar_mapping = jpcoar_mapping_json.get(k)["jpcoar_mapping"]
        if jpcoar_mapping:
            jpcoar_metadata[k] = jpcoar_mapping

    return jpcoar_metadata


def parse_crossref_response(response):
    response_data = dict()
    if response is None or not isinstance(response, dict):
        return response_data

    if response.get('status') != Works.STATUS_OK:
        return response_data

    message = response.get('message')

    if message:
        response_key = config.WEKO_ITEMS_AUTOFILL_CROSSREF_RESPONSE_RESULT

        for key in response_key:
            if message.get(key):
                response_data[key] = message.get(key)

        return response_data
