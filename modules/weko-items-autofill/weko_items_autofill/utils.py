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
import copy
import datetime
from functools import wraps

from flask import current_app
from invenio_cache import current_cache
from weko_records.api import Mapping

from .crossref_api import CrossRefOpenURL


def is_update_cache():
    """Return True if Autofill Api has been updated."""
    return current_app.config['WEKO_ITEMS_AUTOFILL_API_UPDATED']


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


def convert_datetime_format(list_date):
    """Convert datetime from response to the format of GUI
    @param list_date: list include the value of day, month,
    year of the publication date
    @return:
    if the response has full of 3 index(yyyy-mm-dd).
    Convert it to datetime format and return true string format
    else return none"""
    if type(list_date) is list:
        if len(list_date) == 3:
            date = datetime.datetime.strptime(
                str(list_date[0]) + '-' + str(list_date[1]) + '-' + str(
                    list_date[2]), '%Y-%m-%d')
            return date.strftime('%Y-%m-%d')
        else:
            return None
    else:
        return


def try_assign_data(data, value, key_first, list_key=None):
    """Try to assign value into dictionary data
            Basic flow: If dictionary path is exist,
                value will be assigned to dictionary data
            Alternative flow: If dictionary path is not exist,
                no change could be saved
        Parameter:
            data: dictionary data
            value: value have to be assigned
            default_key: first/default dictionary path
            list_key: child of dictionary path
        Return:
            Dictionary with validated values
    """
    data_temp = list()
    if data.get(key_first) is None:
        return
    else:
        data_temp.append(data.get(key_first))
        idx = 0
    if list_key is None:
        data_temp[0] = value
    else:
        for key in list_key:
                if key in data_temp[idx]:
                    if data_temp[idx].get(key):
                        data_temp.append(data_temp[idx].get(key))
                        idx += 1
                    else:
                        temp = data_temp[idx]
                        temp[key] = value
                        return
                else:
                    return


def reset_dict_final_value(data):
    """
        Set template dictionary data to empty
            Basic flow: Remove all final value of dictionary
        Parameter:
            data: dictionary data
        Return:
            Dictionary with all final value is empty.
    """
    temp_data = copy.deepcopy(data)
    for k, v in temp_data.items():
        if isinstance(data[k], dict):
            reset_dict_final_value(data[k])
        else:
            data[k] = None


def parse_crossref_json_response(response, response_data_template):
    """ Convert response data from crossref API to auto fill data
        response: data from crossref API
        response_data_template: template of autofill data
    """
    response_data_convert = copy.deepcopy(response_data_template)
    reset_dict_final_value(response_data_convert)
    if response['response'] == '':
        return None

    created = response['response'].get("created")
    issued = response['response'].get('issued')
    author = response['response'].get('author')
    page = response['response'].get('page')
    if type(page) is str:
        split_page = page.split('-')
        if len(split_page) == 2:
            try:
                try_assign_data(response_data_convert,
                                str(int(split_page[1]) - int(
                                    split_page[0]) + 1),
                                'numPages', ['@value'])
                try_assign_data(response_data_convert, split_page[1], 'pageEnd',
                                ['@value'])
                try_assign_data(response_data_convert, split_page[0],
                                'pageStart',
                                ['@value'])
            except ValueError:
                pass

    if type(created) is dict:
        try_assign_data(response_data_convert, created.get('affiliationName'),
                        'creator', ['affiliation', 'affiliationName', '@value'])
        try_assign_data(response_data_convert,
                        current_app.config[
                            'WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'], 'creator',
                        ['affiliation', 'affiliationName', '@attributes',
                         'xml:lang'])
        try_assign_data(response_data_convert, created.get('nameIdentifier'),
                        'creator', ['affiliation', 'nameIdentifier', '@value'])
        try_assign_data(response_data_convert,
                        created.get('nameIdentifierScheme'),
                        'creator',
                        ['affiliation', 'nameIdentifier', '@attributes',
                         'nameIdentifierScheme'])
        try_assign_data(response_data_convert, created.get('nameIdentifierURI'),
                        'creator',
                        ['affiliation', 'nameIdentifier', '@attributes',
                         'nameIdentifierURI'])
        try_assign_data(response_data_convert,
                        created.get('creatorAlternative'),
                        'creator', ['creatorAlternative', '@value'])
        try_assign_data(response_data_convert, created.get('title'), 'title',
                        ['@value'])
        try_assign_data(response_data_convert, created.get('nameIdentifier'),
                        'creator', ['nameIdentifier', '@value'])
        try_assign_data(response_data_convert,
                        created.get('nameIdentifierScheme'),
                        'creator',
                        ['nameIdentifier', '@attributes',
                         'nameIdentifierScheme'])
        try_assign_data(response_data_convert, created.get('nameIdentifierURI'),
                        'creator',
                        ['nameIdentifier', '@attributes', 'nameIdentifierURI'])
        try_assign_data(response_data_convert, created.get('publisher'),
                        'publisher', ['@value'])
        try_assign_data(response_data_convert, created.get('relationType'),
                        'relation', ['@attributes', 'relationType'])
        try_assign_data(response_data_convert, None, 'relation',
                        ['relatedTitle', '@value'])
        isbn_item = created.get('ISBN')
        if type(isbn_item) is list:
            try_assign_data(response_data_convert, isbn_item[0], 'relation',
                            ['relatedIdentifier', '@value'])
            try_assign_data(response_data_convert, 'ISBN', 'relation',
                            ['relatedIdentifier', '@attributes',
                             'identifierType'])

    if type(author) is list:
        if type(author[0]) is dict:
            given_name = author[0].get('given') or ''
            family_name = author[0].get('family') or ''
            creator_name = given_name + " " + family_name
            try_assign_data(response_data_convert, creator_name.strip(),
                            'creator', ['creatorName', '@value'])
            try_assign_data(response_data_convert, family_name,
                            'creator',
                            ['familyName', '@value'])
            try_assign_data(response_data_convert, given_name,
                            'creator',
                            ['givenName', '@value'])

    if type(issued) is dict:
        try_assign_data(response_data_convert,
                        convert_datetime_format(issued.get('date-parts')),
                        'date',
                        ['@value'])
        try_assign_data(response_data_convert, "Issued", 'date',
                        ['@attributes', 'dateType'])

    """Set default language to English(en or eng) because API does not return 
    the current language"""
    try_assign_data(response_data_convert, 'eng', 'language', ['@value'])
    try_assign_data(response_data_convert,
                    current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                    'publisher',
                    ['@attributes', 'xml:lang'])
    try_assign_data(response_data_convert,
                    current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                    'relation',
                    ['relatedTitle', '@attributes', 'xml:lang'])
    try_assign_data(response_data_convert,
                    current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                    'title',
                    ['@attributes', 'xml:lang'])
    try_assign_data(response_data_convert,
                    current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                    'creator',
                    ['creatorAlternative', '@attributes', 'xml:lang'])
    try_assign_data(response_data_convert,
                    current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                    'creator',
                    ['creatorName', '@attributes', 'xml:lang'])
    try_assign_data(response_data_convert,
                    current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                    'creator',
                    ['familyName', '@attributes', 'xml:lang'])
    try_assign_data(response_data_convert,
                    current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                    'creator',
                    ['givenName', '@attributes', 'xml:lang'])

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
