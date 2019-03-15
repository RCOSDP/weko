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

from weko_records.api import Mapping

from . import config
from .crossref_api import CrossRefOpenURL
import copy


def is_update_cache():
    """Return True if Autofill Api has been updated."""
    return config.WEKO_ITEMS_AUTOFILL_API_UPDATED


def cached_api_json(timeout=50, key_prefix="cached_api_json"):
    """Cache Api data
    :param timeout: Cache timeout
    :param key_prefix: prefix key
    :return:
    """

    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = key_prefix + args[1]
            cache_fun = current_cache.cached(
                timeout=timeout,
                key_prefix=key,
                forced_update=is_update_cache,
            )
            if current_cache.get(key) is None:
                data = cache_fun(f)(*args, **kwargs)
                current_cache.set(key, data)
                return data
            else:
                return current_cache.get(key)

        return wrapper

    return caching


def parse_crossref_json_response(response, response_data_template):
    """ Convert response data from crossref API to auto fill data
        response: data from crossref API
        response_data_template: template of autofill data
    """
    response_data_convert = copy.deepcopy(response_data_template)
    if (response['response'] == ''):
        return None
    created = response['response'].get("created")
    issued = response['response'].get('issued')
    author = response['response'].get('author')
    page = response['response'].get('page')
    split_page = []
    if page:
        split_page = page.split('-')

    response_data_convert['creator']['affiliation']['affiliationName'][
        '@value'] = created.get('affiliationName')
    response_data_convert['creator']['affiliation']['affiliationName'][
        '@attributes']['xml:lang'] = \
        config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE
    response_data_convert['creator']['affiliation']['nameIdentifier'][
        '@value'] = created.get('nameIdentifier')
    response_data_convert['creator']['affiliation']['nameIdentifier'][
        '@attributes']['nameIdentifierScheme'] = \
        created.get('nameIdentifierScheme')
    response_data_convert['creator']['affiliation']['nameIdentifier'][
        '@attributes']['nameIdentifierURI'] = \
        created.get('nameIdentifierURI')
    response_data_convert['creator']['creatorAlternative'][
        '@value'] = created.get('creatorAlternative')
    response_data_convert['creator']['creatorAlternative']['@attributes'][
        'xml:lang'] = \
        config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE

    response_data_convert['creator']['creatorName']['@value'] = author[0].get(
        'given') + " " + author[0].get('family')

    response_data_convert['creator']['creatorName']['@attributes']['xml:lang'] = \
        config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE
    response_data_convert['creator']['familyName']['@value'] = author[0].get(
        'family')
    response_data_convert['creator']['familyName']['@attributes']['xml:lang'] = \
        config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE
    response_data_convert['creator']['givenName']['@value'] = author[0].get(
        'given')
    response_data_convert['creator']['givenName']['@attributes']['xml:lang'] = \
        config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE
    response_data_convert['creator']['nameIdentifier']['@value'] = created.get(
        'nameIdentifier')
    response_data_convert['creator']['nameIdentifier']['@attributes'][
        'nameIdentifierScheme'] = \
        created.get('nameIdentifierScheme')
    response_data_convert['creator']['nameIdentifier']['@attributes'][
        'nameIdentifierURI'] = \
        created.get('nameIdentifierURI')

    response_data_convert['date']['@value'] = issued.get('date-parts')

    response_data_convert['date']['@attributes']['dateType'] = created.get(
        'date')

    response_data_convert['language']['@value'] = 'eng'

    if len(split_page) == 2:
        response_data_convert['numPages']['@value'] = str(
            int(split_page[1]) - int(split_page[0]))
        response_data_convert['pageEnd']['@value'] = split_page[1]
        response_data_convert['pageStart']['@value'] = split_page[0]
    else:
        response_data_convert['numPages']['@value'] = ''
        response_data_convert['pageEnd']['@value'] = ''
        response_data_convert['pageStart']['@value'] = ''

    response_data_convert['publisher']['@value'] = created.get('publisher')
    response_data_convert['publisher']['@attributes'][
        'xml:lang'] = config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE

    response_data_convert['relation']['@attributes'][
        'relationType'] = created.get('relationType')
    response_data_convert['relation']['relatedIdentifier'][
        '@value'] = created.get('ISBN')
    isbn_item = created.get('ISBN')
    if isbn_item is not None:
        response_data_convert['relation']['relatedTitle']['@value'] = isbn_item[
            0]
    else:
        response_data_convert['relation']['relatedTitle']['@value'] = None

    response_data_convert['relation']['relatedTitle']['@attributes'][
        'xml:lang'] = \
        config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE

    response_data_convert['title']['@value'] = created.get('title')
    response_data_convert['title']['@attributes'][
        'xml:lang'] = config.WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE

    return response_data_convert


def get_item_id(item_type_id):
    """
    return dictionary contain item id
    get from mapping between itemtype and jpcoar
    :param item_type_id: The item type id
    :return: dictionary
    """
    results = dict()
    item_type_mapping = Mapping.get_record(item_type_id)
    try:
        for k, v in item_type_mapping.items():
            jpcoar = v.get("jpcoar_mapping")
            if isinstance(jpcoar, dict):
                for u, s in jpcoar.items():
                    results[u] = s
    except Exception as e:
        results['error'] = str(e)

    return results


@cached_api_json(timeout=50,)
def get_crossref_data(pid, doi):
    """Return cache-able data
    pid: pid
    search_data: DOI
    """
    api = CrossRefOpenURL(pid, doi)
    return api.get_data()
