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
from flask import current_app
from invenio_cache import current_cache
from invenio_i18n.ext import current_i18n

from weko_records.api import ItemTypeProps, ItemTypes, Mapping

def is_update_cache():
    """Return True if Amazon Api has been updated."""
    return current_app.config['WEKO_ITEMS_AUTOFIL_AMAZON_API_UPDATED']


def cached_api_json(timeout=50, key_prefix='amazon_json'):
    """Cache Api data
    :param timeout: Cache timeout
    :param key_prefix: prefix key
    :return:
    """

    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout, key_prefix=key_prefix + current_i18n.language,
                forced_update=is_update_cache)
            return cache_fun(f)(*args, **kwargs)

        return wrapper

    return caching


def get_items_autofill(item_type_id):
    """
    :param item_type_id:
    :return: items autofill
    """
    items = {
        'title': '',
        'sourceTitle': '',
        'language': '',
        'creator': '',
        'pageStart': '',
        'pageEnd': '',
        'date': '',
        'publisher': '',
        'relatedIdentifier': '',
    }
    item_type_json = ItemTypes.get_record(item_type_id)
    item_mapping_json = Mapping.get_record(item_type_id)
    if item_type_json and item_mapping_json:
        for value in item_type_json["properties"]:
            jpcoar_metadata = item_mapping_json[value]["jpcoar_mapping"]
            if isinstance(jpcoar_metadata, dict):
                for k in jpcoar_metadata.keys():
                    for key in items.keys():
                        if k == key:
                            items[key] = value

    return items
