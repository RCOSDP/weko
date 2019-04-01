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

from .api import CiNiiURL, CrossRefOpenURL


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
            key = key_prefix + args[len(args) - 1]
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
        if type(data.get(key_first)) is list:
            for item in data.get(key_first):
                if type(item) is dict:
                    if item.get(key_first) is not None:
                        data_temp.append(item)
        else:
            data_temp.append(data.get(key_first))
        idx = 0
    if list_key is None:
        data_temp[0] = convert_html_escape(value)
    else:
        for key in list_key:
            if type(data_temp[idx]) is dict:
                if key in data_temp[idx]:
                    if data_temp[idx].get(key):
                        data_temp.append(data_temp[idx].get(key))
                        idx += 1
                    else:
                        temp = data_temp[idx]
                        temp[key] = convert_html_escape(value)
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
        elif isinstance(data[k], list):
            for key in data[k]:
                reset_dict_final_value(key)
        else:
            data[k] = None


def asssign_data_crossref_created_field(field, data):
    """
        Assign data from crossref created field to data container
        @parameter: crossref created field, data container
        @return:
    """
    try:
        try_assign_data(data, field.get('affiliationName'),
                        'creator',
                        ['affiliation', 'affiliationName', '@value'])
        try_assign_data(data,
                        current_app.config[
                            'WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'], 'creator',
                        ['affiliation', 'affiliationName', '@attributes',
                         'xml:lang'])
        try_assign_data(data, field.get('nameIdentifier'),
                        'creator', ['affiliation', 'nameIdentifier', '@value'])
        try_assign_data(data,
                        field.get('nameIdentifierScheme'),
                        'creator',
                        ['affiliation', 'nameIdentifier', '@attributes',
                         'nameIdentifierScheme'])
        try_assign_data(data, field.get('nameIdentifierURI'),
                        'creator',
                        ['affiliation', 'nameIdentifier', '@attributes',
                         'nameIdentifierURI'])
        try_assign_data(data,
                        field.get('creatorAlternative'),
                        'creator', ['creatorAlternative', '@value'])
        try_assign_data(data, field.get('title'), 'title',
                        ['@value'])
        try_assign_data(data, field.get('nameIdentifier'),
                        'creator', ['nameIdentifier', '@value'])
        try_assign_data(data,
                        field.get('nameIdentifierScheme'),
                        'creator',
                        ['nameIdentifier', '@attributes',
                         'nameIdentifierScheme'])
        try_assign_data(data, field.get('nameIdentifierURI'),
                        'creator',
                        ['nameIdentifier', '@attributes', 'nameIdentifierURI'])
        try_assign_data(data, field.get('publisher'),
                        'publisher', ['@value'])
        try_assign_data(data, field.get('relationType'),
                        'relation', ['@attributes', 'relationType'])
        try_assign_data(data, '', 'relation',
                        ['relatedTitle', '@value'])
        isbn_item = field.get('ISBN')
        try_assign_data(data, isbn_item[0], 'relation',
                        ['relatedIdentifier', '@value'])
        try_assign_data(data, 'ISBN', 'relation',
                        ['relatedIdentifier', '@attributes', 'identifierType'])
    except Exception:
        pass


def asssign_data_crossref_page_field(field, data):
    """
        Assign data from crossref page field to data container
        @parameter: crossref page field, data container
        @return:
    """
    try:
        split_page = field.split('-')
        try_assign_data(data, str(int(split_page[1]) - int(split_page[0]) + 1),
                        'numPages', ['@value'])
        try_assign_data(data, split_page[1], 'pageEnd', ['@value'])
        try_assign_data(data, split_page[0], 'pageStart', ['@value'])
    except Exception:
        pass


def asssign_data_crossref_author_field(field, data):
    """
        Assign data from crossref author field to data container
        @parameter: crossref author field, data container
        @return:
    """
    try:
        given_name = field[0].get('given') or ''
        family_name = field[0].get('family') or ''
        creator_name = given_name + " " + family_name
        try_assign_data(data, creator_name.strip(),
                        'creator', ['creatorName', '@value'])
        try_assign_data(data, family_name,
                        'creator',
                        ['familyName', '@value'])
        try_assign_data(data, given_name,
                        'creator',
                        ['givenName', '@value'])
    except Exception:
        pass


def asssign_data_crossref_issued_field(field, data):
    """
        Assign data from crossref issued field to data container
        @parameter: crossref issued field, data container
        @return:
    """
    try:
        try_assign_data(data,
                        convert_datetime_format(field.get('date-parts')),
                        'date',
                        ['@value'])
        try_assign_data(data, 'Issued', 'date',
                        ['@attributes', 'dateType'])
    except Exception:
        pass


def asssign_data_crossref_default_field(field, data):
    """
        Assign data from default value to data container
        Set default language to English(en or eng) because API does not return
        the current language
        @parameter: Default value, data container
        @return:
    """
    try_assign_data(data, 'eng', 'language', ['@value'])
    try_assign_data(data,
                    field,
                    'publisher',
                    ['@attributes', 'xml:lang'])
    try_assign_data(data,
                    field,
                    'relation',
                    ['relatedTitle', '@attributes', 'xml:lang'])
    try_assign_data(data,
                    field,
                    'title',
                    ['@attributes', 'xml:lang'])
    try_assign_data(data,
                    field,
                    'creator',
                    ['creatorAlternative', '@attributes', 'xml:lang'])
    try_assign_data(data,
                    field,
                    'creator',
                    ['creatorName', '@attributes', 'xml:lang'])
    try_assign_data(data,
                    field,
                    'creator',
                    ['familyName', '@attributes', 'xml:lang'])
    try_assign_data(data,
                    field,
                    'creator',
                    ['givenName', '@attributes', 'xml:lang'])


def parse_crossref_json_response(response, response_data_template):
    """ Convert response data from crossref API to auto fill data
        response: data from crossref API
        response_data_template: template of autofill data
    """
    response_data_convert = copy.deepcopy(response_data_template)
    if response['response'] == '':
        return None
    reset_dict_final_value(response_data_convert)
    try:
        created = response['response'].get('created')
        issued = response['response'].get('issued')
        author = response['response'].get('author')
        page = response['response'].get('page')

        asssign_data_crossref_created_field(created, response_data_convert)
        asssign_data_crossref_page_field(page, response_data_convert)
        asssign_data_crossref_author_field(author, response_data_convert)
        asssign_data_crossref_issued_field(issued, response_data_convert)
        asssign_data_crossref_default_field(
            current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
            response_data_convert)
    except Exception:
        pass

    return response_data_convert


def assign_data_cinii_dc_title_field(field, data):
    """
        Assign data from cinii dc_title field to data container
        @parameter: cinii dc_title field, data container
        @return:
    """
    try:
        for item in field:
            lang = item.get('@language')
            if lang is None and item.get('@value'):
                try_assign_data(data, item.get('@value'),
                                'title', ['title', '@value'])
                try_assign_data(data, 'ja', 'title',
                                ['title', '@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_dc_creator_field(field, data):
    """
        Assign data from cinii dc_creator field to data container
        @parameter: cinii dc_creator field, data container
        @return:
    """
    try:
        for item in field[0]:
            lang = item.get('@language')
            if lang is None and item.get('@value'):
                try_assign_data(data, item.get('@value'),
                                'creator', ['creatorName', '@value'])
                try_assign_data(data, 'ja', 'creator',
                                ['creatorName', '@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_page_field(page_start, page_end, data):
    """
        Assign data from cinii page field to data container
        @parameter: cinii page field, data container
        @return:
    """
    try:
        try_assign_data(data, page_start, 'pageStart', ['@value'])
        try_assign_data(data, page_end, 'pageEnd', ['@value'])
        try_assign_data(data, str(int(page_end) - int(page_start) + 1),
                        'numPages', ['@value'])
    except Exception:
        pass


def assign_data_cinii_prism_publication_date_field(field, data):
    """
        Assign data from cinii prism_publication_date field to data container
        @parameter: cinii prism_publication_date field, data container
        @return:
    """
    try:
        date_list = field.split('-')
        try_assign_data(data, convert_datetime_format(date_list), 'date',
                        ['date', '@value'])
        try_assign_data(data, 'Issued', 'date',
                        ['date', '@attributes', 'dateType'])
    except Exception:
        pass


def assign_data_cinii_dc_publisher_field(field, data):
    """
        Assign data from cinii dc_publisher field to data container
        @parameter: cinii dc_publisher field, data container
        @return:
    """
    try:
        for item in field:
            lang = item.get('@language')
            if lang is None and item.get('@value'):
                try_assign_data(data, item.get('@value'), 'publisher',
                                ['@value'])
                try_assign_data(data, 'ja', 'publisher',
                                ['@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_foaf_maker_field(field, data):
    """
        Assign data from cinii foaf_maker field to data container
        @parameter: cinii foaf_maker field, data container
        @return:
    """
    try:
        con_organization = field[0].get('con:organization')
        floaf_name = con_organization[0].get('foaf:name')
        for item in floaf_name:
            lang = item.get('@language')
            if lang is None and item.get('@value'):
                try_assign_data(data, item.get('@value'), 'contributor',
                                ['contributorName', '@value'])
                try_assign_data(data, 'ja', 'contributor',
                                ['contributorName', '@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_dc_description_field(field, data):
    """
        Assign data from cinii dc_description field to data container
        @parameter: cinii dc_description field, data container
        @return:
    """
    try:
        for item in field:
            lang = item.get('@language')
            if lang is None and item.get('@value'):
                try_assign_data(data, item.get('@value'), 'description',
                                ['@value'])
                try_assign_data(data, 'ja', 'description',
                                ['@attributes', 'xml:lang'])
                try_assign_data(data, 'Abstract', 'description',
                                ['@attributes', 'descriptionType'])
    except Exception:
        pass


def assign_data_cinii_foaf_topic_field(field, data):
    """
        Assign data from cinii foaf_topic field to data container
        @parameter: cinii foaf_topic field, data container
        @return:
    """
    try:
        dc_title_topic = field[0].get('dc:title')
        try_assign_data(data, dc_title_topic[0].get('@value'), 'subject',
                        ['@value'])
        try_assign_data(data, field[0].get('@id'), 'subject',
                        ['@attributes', 'subjectURI'])
        try_assign_data(data, 'Other', 'subject',
                        ['@attributes', 'subjectScheme'])
        try_assign_data(data, 'ja', 'subject',
                        ['@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_prism_publication_name_field(field, data):
    """
        Assign data from cinii prism_publicationName field to data container
        @parameter: cinii prism_publicationName field, data container
        @return:
    """
    try:
        for item in field:
            lang = item.get('@language')
            if lang is None and item.get('@value'):
                try_assign_data(data, item.get('@value'), 'sourceTitle',
                                ['@value'])
                try_assign_data(data, 'ja', 'sourceTitle',
                                ['@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_other_information_field(prism_volume,
                                              prism_number, prism_issn, data):
    """
        Assign data from cinii other field information to data container
        @parameter: cinii other field information, data container
        @return:
    """
    try:
        try_assign_data(data, prism_volume, 'volume', ['@value'])
        try_assign_data(data, prism_number, 'issue', ['@value'])
        try_assign_data(data, prism_issn, 'sourceIdentifier', ['@value'])
        if prism_issn:
            try_assign_data(data, 'ISSN', 'sourceIdentifier',
                            ['@attributes', 'identifierType'])
    except Exception:
        pass


def parse_cinii_json_response(response, response_data_template):
    """ Convert response data from cinii API to auto fill data
        response: data from cinii API
        response_data_template: template of autofill data
    """
    response_data_convert = copy.deepcopy(response_data_template)
    reset_dict_final_value(response_data_convert)
    if response['response'] == '':
        return None
    try:
        graph = response['response'].get('@graph')

        assign_data_cinii_dc_title_field(graph[0].get('dc:title'),
                                         response_data_convert)
        assign_data_cinii_dc_creator_field(graph[0].get('dc:creator'),
                                           response_data_convert)
        assign_data_cinii_page_field(graph[0].get('prism:startingPage'),
                                     graph[0].get('prism:endingPage'),
                                     response_data_convert)
        assign_data_cinii_prism_publication_date_field(
            graph[0].get('prism:publicationDate'), response_data_convert)
        assign_data_cinii_dc_publisher_field(graph[0].get('dc:publisher'),
                                             response_data_convert)
        assign_data_cinii_foaf_maker_field(graph[0].get('foaf:maker'),
                                           response_data_convert)
        assign_data_cinii_dc_description_field(graph[0].get('dc:description'),
                                               response_data_convert)
        assign_data_cinii_foaf_topic_field(graph[0].get('foaf:topic'),
                                           response_data_convert)
        assign_data_cinii_prism_publication_name_field(graph[0].get(
            'prism:publicationName'), response_data_convert)
        assign_data_cinii_other_information_field(graph[0].get('prism:volume'),
                                                  graph[0].get('prism:number'),
                                                  graph[0].get('prism:issn'),
                                                  response_data_convert)

    except Exception:
        pass

    return response_data_convert


def get_item_id(item_type_id):
    """
    return dictionary contain item id
    get from mapping between item type and jpcoar
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
                    if results.get(u) is not None:
                        data = list()
                        if isinstance(results.get(u), list):
                            data = results.get(u)
                            data.append({u: s})
                        else:
                            data.append({u: results.get(u)})
                            data.append({u: s})
                        results[u] = data
                    else:
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


@cached_api_json(timeout=50,)
def get_cinii_data(naid):
    """Return cache-able data
    naid : naid
    """
    api = CiNiiURL(naid)
    return api.get_data()


def convert_html_escape(text):
    """
    Convert escape HTML to character
    :type text: String
    """
    html_escape = {
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
        "&gt;": ">",
        "&lt;": "<",
    }

    for key, value in html_escape:
        text.replace(key, value)

    return text
