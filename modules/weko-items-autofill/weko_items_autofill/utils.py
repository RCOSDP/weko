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
from weko_records.api import Mapping, ItemTypes

from .api import CiNiiURL, CrossRefOpenURL


def is_update_cache():
    """Return True if Autofill Api has been updated."""
    return current_app.config['WEKO_ITEMS_AUTOFILL_API_UPDATED']


def cached_api_json(timeout=50, key_prefix="cached_api_json"):
    """Cache Api response data.

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
    """Convert datetime from response to the format of GUI.

    @param list_date: list include the value of day, month,
    year of the publication date
    @return:
    if the response has full of 3 index(yyyy-mm-dd).
    Convert it to datetime format and return true string format
    else return none
    """
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
    """Try to assign value into dictionary data.

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
    """Reset diction data.

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
    """Assign data from Crossref created field to data container.

    @parameter: Crossref created field, data container
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
        if type(data.get('title')) is list:
            list_title = data.get('title')
            for title in list_title:
                if title.get('title'):
                    try_assign_data(title, field.get('title'), 'title',
                                    ['@value'])
                    try_assign_data(title,
                                    current_app.config
                                    ['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'],
                                    'title', ['@attributes', 'xml:lang'])
                    break
        else:
            try_assign_data(data, field.get('title'), 'title',
                            ['@value'])
            try_assign_data(data, current_app.config
                            ['WEKO_ITEMS_AUTOFILL_DEFAULT_LANGUAGE'], 'title',
                            ['@attributes', 'xml:lang'])
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
    """Assign data from Crossref page field to data container.

    @parameter: Crossref page field, data container
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
    """Assign data from Crossref author field to data container.

    @parameter: Crossref author field, data container
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
    """Assign data from Crossref issued field to data container.

    @parameter: Crossref issued field, data container
    """
    try:
        if type(data.get('date')) is list:
            list_date = data.get('date')
            for date in list_date:
                if date.get('date'):
                    if('@value' not in date['date'].keys()):
                        continue
                    try_assign_data(date,
                                    convert_datetime_format(field.get
                                                            ('date-parts')),
                                    'date',
                                    ['@value'])
                    try_assign_data(date, 'Issued', 'date',
                                    ['@attributes', 'dateType'])
                    break
        else:
            try_assign_data(data,
                            convert_datetime_format(field.get('date-parts')),
                            'date',
                            ['@value'])
            try_assign_data(data, 'Issued', 'date',
                            ['@attributes', 'dateType'])
    except Exception:
        pass


def asssign_data_crossref_default_field(field, data):
    """Assign data from default value to data container.

    Set default language to English(en or eng) because API does not return
        the current language
    @parameter: Default value, data container
    """
    if type(data.get('language')) is list:
        list_language = data.get('language')
        for language in list_language:
            if language.get('language'):
                try_assign_data(language, 'eng', 'language', ['@value'])
                break
    else:
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
    """Convert response data from Crossref API to auto fill data.

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
    """Assign data from CiNii dc_title field to data container.

    @parameter: CiNii dc_title field, data container
    """
    try:
        item = field[0]
        lang = item.get('@language')
        if lang is None:
            lang = 'ja'

        # Set dcterms:alternative
        try_assign_data(data, item.get('@value'),
                        'alternative', ['@value'])
        try_assign_data(data, lang, 'alternative',
                        ['@attributes', 'xml:lang'])

        # Set dc:title
        if type(data.get('title')) is list:
            list_title = data.get('title')
            for title in list_title:
                if title.get('title'):
                    try_assign_data(data, item.get('@value'),
                                    'title', ['title', '@value'])
                    try_assign_data(data, lang, 'title',
                                    ['title', '@attributes', 'xml:lang'])
                    break
        else:
            try_assign_data(data, item.get('@value'), 'title',
                            ['@value'])
            try_assign_data(data, lang, 'title',
                            ['@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_dc_creator_field(field, data):
    """Assign data from CiNii dc_creator field to data container.

    @parameter: CiNii dc_creator field, data container
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
    """Assign data from CiNii page field to data container.

    @parameter: CiNii page field, data container
    """
    try:
        try_assign_data(data, page_start, 'pageStart', ['@value'])
        try_assign_data(data, page_end, 'pageEnd', ['@value'])
        try_assign_data(data, str(int(page_end) - int(page_start) + 1),
                        'numPages', ['@value'])
    except Exception:
        pass


def assign_data_cinii_prism_publication_date_field(field, data):
    """Assign data from CiNii prism_publication_date field to data container.

    @parameter: CiNii prism_publication_date field, data container
    """
    try:
        date_list = field.split('-')
        if type(data.get('date')) is list:
            list_date = data.get('date')
            for date in list_date:
                if date.get('date'):
                    try_assign_data(date, convert_datetime_format(date_list),
                                    'date', ['@value'])
                    try_assign_data(date, 'Issued', 'date',
                                    ['@attributes', 'dateType'])
                    break
        else:
            try_assign_data(data, convert_datetime_format(date_list), 'date',
                            ['@value'])
            try_assign_data(data, 'Issued', 'date',
                            ['@attributes', 'dateType'])
    except Exception:
        pass


def assign_data_cinii_dc_publisher_field(field, data):
    """Assign data from CiNii dc_publisher field to data container.

    @parameter: CiNii dc_publisher field, data container
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
    """Assign data from CiNii foaf_maker field to data container.

    @parameter: CiNii foaf_maker field, data container
    """
    try:
        con_organization = field[0].get('con:organization')
        foaf_name = con_organization[0].get('foaf:name')
        for item in foaf_name:
            lang = item.get('@language')
            if lang is None and item.get('@value'):
                try_assign_data(data, item.get('@value'), 'contributor',
                                ['contributorName', '@value'])
                try_assign_data(data, 'ja', 'contributor',
                                ['contributorName', '@attributes', 'xml:lang'])
    except Exception:
        pass


def assign_data_cinii_dc_description_field(field, data):
    """Assign data from CiNii dc_description field to data container.

    @parameter: CiNii dc_description field, data container
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
    """Assign data from CiNii foaf_topic field to data container.

    @parameter: CiNii foaf_topic field, data container
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
    """Assign data from CiNii prism_publicationName field to data container.

    @parameter: CiNii prism_publicationName field, data container
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


def assign_data_cinii_prism_issn(field, data):
    """Assign data from CiNii prism issn field information to data container.

    :type field: object
    :type data: object
    """
    try:
        try_assign_data(data, field, 'sourceIdentifier', ['@value'])
        if field:
            try_assign_data(data, 'ISSN', 'sourceIdentifier',
                            ['@attributes', 'identifierType'])
    except Exception:
        pass


def assign_data_cinii_cinii_ncid(field, data):
    """Assign data from CiNii prism ncid field information to data container.

    :type field: object
    :type data: object
    """
    try:
        try_assign_data(data, field, 'sourceIdentifier', ['@value'])
        if field:
            try_assign_data(data, 'NCID', 'sourceIdentifier',
                            ['@attributes', 'identifierType'])
    except Exception:
        pass


def assign_data_cinii_cinii_naid(field, data):
    """Assign data from CiNii cinii naid field information to data container.

    :type field: object
    :type data: object
    """
    try:
        try_assign_data(data, field, 'relation',
                        ['relatedIdentifier', '@value'])
        if field:
            try_assign_data(data, 'NAID', 'relation',
                            ['relatedIdentifier', '@attributes',
                             'identifierType'])
    except Exception:
        pass


def assign_data_cinii_prism_doi(field, data):
    """Assign data from CiNii prism doi field information to data container.

    :type field: object
    :type data: object
    """
    try:
        try_assign_data(data, field, 'relation',
                        ['relatedIdentifier', '@value'])
        if field:
            try_assign_data(data, 'DOI', 'relation',
                            ['relatedIdentifier', '@attributes',
                             'identifierType'])
    except Exception:
        pass


def assign_data_cinii_other_information_field(prism_volume,
                                              prism_number, data):
    """Assign data from CiNii other field information to data container.

    @parameter: CiNii other field information, data container
    """
    try:
        try_assign_data(data, prism_volume, 'volume', ['@value'])
        try_assign_data(data, prism_number, 'issue', ['@value'])
    except Exception:
        pass


def parse_cinii_json_response(response, response_data_template):
    """Convert response data from CiNii API to auto fill data.

    response: data from CiNii API
    response_data_template: template of autofill data
    """
    response_data_convert = copy.deepcopy(response_data_template)
    reset_dict_final_value(response_data_convert)
    if response['response'] == '':
        return None
    try:
        graph = response['response'].get('@graph')

        if not graph:
            return response_data_convert

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

        if graph[0].get('prism:issn'):
            assign_data_cinii_prism_issn(graph[0].get('prism:issn'),
                                         response_data_convert)
        elif graph[0].get('cinii:ncid'):
            assign_data_cinii_prism_issn(graph[0].get('cinii:ncid'),
                                         response_data_convert)

        if graph[0].get('cinii:naid'):
            assign_data_cinii_cinii_naid(graph[0].get('cinii:naid'),
                                         response_data_convert)
        elif graph[0].get('prism:doi'):
            assign_data_cinii_cinii_naid(graph[0].get('prism:doi'),
                                         response_data_convert)

        assign_data_cinii_other_information_field(graph[0].get('prism:volume'),
                                                  graph[0].get('prism:number'),
                                                  response_data_convert)
    except Exception:
        pass

    return response_data_convert


def get_item_id(item_type_id):
    """Get dictionary contain item id.

    Get from mapping between item type and jpcoar
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


@cached_api_json(timeout=50, key_prefix="crossref_data")
def get_crossref_data(pid, doi):
    """Get autofill data from Crossref API.

    pid: pid
    search_data: DOI
    """
    api = CrossRefOpenURL(pid, doi)
    return api.get_data()


@cached_api_json(timeout=50, key_prefix="cinii_data")
def get_cinii_data(naid):
    """Get autofill data from CiNii API.

    naid : naid
    """
    api = CiNiiURL(naid)
    return api.get_data()


def convert_html_escape(text):
    """Convert escape HTML to character.

    :type text: String
    """
    if not isinstance(text, str):
        return
    html_escape = {
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
        "&gt;": ">",
        "&lt;": "<",
    }
    try:
        for key, value in html_escape.items():
            text = text.replace(key, value)
    except Exception:
        pass

    return text


def get_title_pubdate_path(item_type_id):
    """Get title and pubdate path.

    :param item_type_id:
    :return: result json.
    """
    result = {
        'title': '',
        'pubDate': ''
    }
    item_type_mapping = Mapping.get_record(item_type_id)
    title = list()
    pub_date = list()
    for k, v in item_type_mapping.items():
        jpcoar = v.get("jpcoar_mapping")
        if isinstance(jpcoar, dict):
            if 'title' in jpcoar.keys():
                try:
                    if str(k).index('item') is not None:
                        title.append(k)
                        title_value = jpcoar['title']
                        if '@value' in title_value.keys():
                            title.append(title_value['@value'])
                        if '@attributes' in title_value.keys():
                            title_lang = title_value['@attributes']
                            if 'xml:lang' in title_lang.keys():
                                title.append(title_lang['xml:lang'])
                except Exception:
                    pass
            elif 'date' in jpcoar.keys():
                try:
                    if str(k).index('item') is not None:
                        pub_date.append(k)
                        title_value = jpcoar['date']
                        if '@value' in title_value.keys():
                            pub_date.append(title_value['@value'])
                except Exception:
                    pass
    result['title'] = title
    result['pubDate'] = pub_date
    return result


# @cached_api_json(timeout=50, key_prefix="crossref_data")
def get_crossref_record_data(pid, doi, id, items):
    """
        TODO: Implement for API
    """
    api = CrossRefOpenURL(pid, doi).get_data()
    result = get_crossref_data_by_key(api, 'all')
    return result


# @cached_api_json(timeout=50, key_prefix="cinii_data")
def get_cinii_record_data(naid, id, items):
    """
        TODO: Impelement for API
    """
    api = CiNiiURL(naid).get_data()
    result = get_cinii_data_by_key(api, 'all')
    return result


def get_basic_cinii_data(data):
    """ Get basic data template from CiNii

        Basic value format:
        {
            '@value': value,
            '@language': language
        }

        :param: data: CiNii data
        :return: list converted data
    """
    result = list()
    default_language = 'ja'
    for item in data:
        new_data = dict()
        new_data['@value'] = item.get('@value')
        if item.get('@language'):
            new_data['@language'] = item.get('@language')
        else:
            new_data['@language'] = default_language
        result.append(new_data)
    return result


def pack_single_value_as_dict(data):
    """ Pack value as dictionary

    Based on return format
    {
        '@value': value
    }

    :param: data: data need to pack
    :return: dictionary contain packed data
    """
    new_data = dict()
    new_data['@value'] = data
    return new_data


def pack_data_with_multiple_type_cinii(data1, type1, data2, type2):
    """ Map CiNii multi data with type
    
    Arguments:
        data1
        type1
        data2
        type2
    
    Returns:
        packed data
    """
    result = list()
    if data1:
        new_data = dict()
        new_data['@value'] = data1
        new_data['@type'] = type1
        result.append(new_data)
    if data2:
        new_data = dict()
        new_data['@value'] = data2
        new_data['@type'] = type2
        result.append(new_data)
    return result


def get_cinii_creator_data(data):
    """ Get creator data from CiNii

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: creator data
    :return: list of creator name
    """
    result = list()
    default_language = 'ja'
    for item in data:
        new_data = dict()
        new_data['@value'] = item[0].get('@value')
        if item[0].get('@language'):
            new_data['@language'] = item[0].get('@language')
        else:
            new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_cinii_contributor_data(data):
    """ Get contributor data from CiNii

    Get contributor name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'ja'
    for item in data:
        new_data = dict()
        organization = item['con:organization'][0]
        new_data['@value'] = organization['foaf:name'][0].get('@value')
        if organization['foaf:name'][0].get('@language'):
            language = organization['foaf:name'][0].get('@language')
            new_data['@language'] = language
        else:
            new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_cinii_description_data(data):
    """ Get description data from CiNii

    Get description and form it as format:
    {
        '@value': description,
        '@language': language,
        '@type': type of description
    }

    :param: description data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    for item in data:
        new_data = dict()
        new_data['@value'] = item.get('@value')
        new_data['@type'] = 'Abstract'
        if item.get('@language'):
            new_data['@language'] = item.get('@language')
        else:
            new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_cinii_subject_data(data):
    """ Get subject data from CiNii

    Get subject and form it as format:
    {
        '@value': title,
        '2language': language,
        '@scheme': scheme of subject
        '@URI': source of subject
    }

    :param: data: subject data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    for sub in data:
        new_data = dict()
        new_data['@scheme'] = 'Other'
        new_data['@URI'] = sub.get('@id')
        title = sub.get('dc:title')
        if title[0] is not None:
            new_data['@value'] = title[0].get('@value')
            if title[0].get('@language'):
                new_data['@language'] = title[0].get('@language')
            else:
                new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_cinii_page_data(data):
    """ Get start page and end page data

    Get page info and pack it:
    {
        '@value': number
    }

    :param: data: No of page
    :return: packed data
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(result)
    except Exception:
        return pack_single_value_as_dict(None)


def get_cinii_numpage(data):
    """ Get number of page

    If CiNii have pageRange, get number of page
    If not, number of page equals distance between start and end page

    :param: data: CiNii data
    :return: number of page is packed
    """
    if data.get('prism:pageRange'):
        return get_cinii_page_data(data.get('prism:pageRange'))
    else:
        try:
            end = int(data.get('prism:endingPage'))
            start = int(data.get('prism:startingPage'))
            numPages = end - start + 1
            return pack_single_value_as_dict(numPages)
        except Exception:
            return pack_single_value_as_dict(None)


def get_cinii_date_data(data):
    """ Get publication date

    Get publication date from CiNii data
    format:
    {
        '@value': date
        '@type': type of date
    }

    :param: data: date
    :return: date and date type is packed
    """
    result = dict()
    if len(data.split('-')) != 3:
        result['@value'] = None
        result['@type'] = None
    else:
        result['@value'] = data
        result['@type'] = 'Issued'
    return result


def get_cinii_data_by_key(api, keyword):
    """ Get data from CiNii based on keyword

    :param: api: CiNii data
    :param: keyword: keyword for search
    :return: data for keyword
    """
    data = api['response'].get('@graph')
    data = data[0]
    result = dict()
    if keyword == 'title':
        result[keyword] = get_basic_cinii_data(data.get('dc:title'))
    elif keyword == 'alternative':
        result[keyword] = get_basic_cinii_data(data.get('dc:title'))
    elif keyword == 'creator':
        result[keyword] = get_cinii_creator_data(data.get('dc:creator'))
    elif keyword == 'contributor':
        result[keyword] = get_cinii_contributor_data(data.get('foaf:maker'))
    elif keyword == 'description':
        result[keyword] = get_cinii_description_data(
            data.get('dc:description')
            )
    elif keyword == 'subject':
        result[keyword] = get_cinii_subject_data(data.get('foaf:topic'))
    elif keyword == 'sourceTitle':
        result[keyword] = get_basic_cinii_data(
            data.get('prism:publicationName')
            )
    elif keyword == 'volume':
        result[keyword] = pack_single_value_as_dict(data.get('prism:volume'))
    elif keyword == 'issue':
        result[keyword] = pack_single_value_as_dict(data.get('prism:number'))
    elif keyword == 'pageStart':
        result[keyword] = get_cinii_page_data(data.get('prism:startingPage'))
    elif keyword == 'pageEnd':
        result[keyword] = get_cinii_page_data(data.get('prism:endingPage'))
    elif keyword == 'numPages':
        result[keyword] = get_cinii_numpage(data)
    elif keyword == 'date':
        result[keyword] = get_cinii_date_data(data.get('prism:publicationDate'))
    elif keyword == 'publisher':
        result[keyword] = get_basic_cinii_data(data.get('dc:publisher'))
    elif keyword == 'sourceIdentifier':
        result[keyword] = pack_data_with_multiple_type_cinii(
            data.get('prism:issn'),
            'ISSN（非推奨）',
            data.get('cinii:ncid'),
            'NCID'
        )
    elif keyword == 'relation':
        result[keyword] = pack_data_with_multiple_type_cinii(
            data.get('cinii:naid'),
            'NAID',
            data.get('prism:doi'),
            'DOI'
        )
    elif keyword == 'all':
        CINII_REQUIRED_ITEM = [
            "title",
            "alternative",
            "creator",
            "contributor",
            "description",
            "subject",
            "sourceTitle",
            "volume",
            "issue",
            "pageStart",
            "pageEnd",
            "numPages",
            "date",
            "publisher",
            "sourceIdentifier",
            "relation"
        ]
        for key in CINII_REQUIRED_ITEM:
            result[key] = get_cinii_data_by_key(api, key).get(key)
    return result


def get_crossref_title_data(data):
    """ Get title data from CrossRef

    Arguments:
        data -- title data

    Returns:
        Packed title data
    """
    result = list()
    default_language = 'en'
    if isinstance(data, list):
        for title in data:
            new_data = dict()
            new_data['@value'] = title
            new_data['@language'] = default_language
            result.append(new_data)
    else:
        new_data = dict()
        new_data['@value'] = data
        new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_crossref_creator_data(data):
    """ Get creator name from CrossRef data

    Arguments:
        data -- CrossRef data
    """
    result = list()
    default_language = 'en'
    for creator in data:
        family_name = creator.get('family')
        given_name = creator.get('given')
        full_name = ''
        if given_name and family_name:
            full_name = family_name + given_name
        elif given_name:
            full_name = given_name
        elif family_name:
            full_name = family_name
        new_data = dict()
        new_data['@value'] = full_name
        new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_crossref_numpage_data(data):
    """ Get number of page from CrossRef data

    Arguments:
        data -- page data

    Returns:
        Number of page is calculated and packed
    """
    numpages = data.split('-')
    if len(numpages) == 1:
        DEFAULT_PAGE_NUMBER = 1
        return pack_single_value_as_dict(DEFAULT_PAGE_NUMBER)
    else:
        try:
            num_page = int(numpages[1]) - int(numpages[0])
            return pack_single_value_as_dict(num_page)
        except Exception:
            return pack_single_value_as_dict(None)


def get_start_and_end_page(data, index):
    """ Get start data and end date from CrossRef data

    Arguments:
        data -- page data
        index -- Index in page array. 0 for start and 1 for end

    Returns:
        Start/End date is packed
    """
    numpages = data.split('-')
    if len(numpages) == 1:
        try:
            start_page = int(data)
            new_data = dict()
            new_data['@value'] = start_page
            return new_data
        except Exception:
            new_data = dict()
            new_data['@value'] = None
            return new_data
    else:
        try:
            new_data = dict()
            new_data['@value'] = int(numpages[index])
            return new_data
        except Exception:
            new_data = dict()
            new_data['@value'] = None
            return new_data


def get_crossref_issue_date(data):
    """ Get crossref issued date

    Arguments:
        data -- issued data

    Returns:
        Issued date is packed
    """
    date = data.get('date-parts')
    if isinstance(date, list) and len(date) == 3:
        datetime = '-'.join(date)
        return pack_single_value_as_dict(datetime)
    else:
        return pack_single_value_as_dict(None)


def get_crossref_publisher_data(data):
    """ Get publisher information

    Arguments:
        data -- created data

    Returns:
        Publisher packed data
    """
    new_data = dict()
    default_language = 'en'
    new_data['@value'] = data
    new_data['@language'] = default_language
    return new_data


def get_crossref_relation_data(data):
    result = list()
    if data is None:
        return pack_single_value_as_dict(None)
    for isbn in data:
        new_data = dict()
        new_data['@value'] = isbn
        new_data['@type'] = 'ISBN'
        result.append(new_data)
    return result


def get_crossref_data_by_key(api, keyword):
    """ Get CrossRef data based on keyword

    Arguments:
        api: CrossRef data
        keyword: search keyword

    Returns:
        CrossRef data for keyword
    """
    if api['error'] or api['response'] is None:
        return None

    data = api['response']
    result = dict()

    created = data.get('created')
    if created is None:
        return None
    page = data.get('page')

    if keyword == 'title':
        result[keyword] = get_crossref_title_data(created.get('title'))
    elif keyword == 'language':
        result[keyword] = pack_single_value_as_dict('eng')
    elif keyword == 'creator':
        result[keyword] = get_crossref_creator_data(data.get('author'))
    elif keyword == 'numPages':
        result[keyword] = get_crossref_numpage_data(page)
    elif keyword == 'pageStart':
        result[keyword] = get_start_and_end_page(page, 0)
    elif keyword == 'pageEnd':
        result[keyword] = get_start_and_end_page(page, 1)
    elif keyword == 'date':
        result[keyword] = get_crossref_issue_date(data.get('issued'))
    elif keyword == 'publisher':
        result[keyword] = get_crossref_publisher_data(created.get('publisher'))
    elif keyword == 'relation':
        result[keyword] = get_crossref_relation_data(created.get('ISBN'))
    elif keyword == 'all':
        CROSSREF_REQUIRE_ITEM = ["title", "language", "creator", "numPages",
                                 "pageStart", "pageEnd", "date",
                                 "publisher", "relation"]
        for key in CROSSREF_REQUIRE_ITEM:
            result[key] = get_crossref_data_by_key(api, key).get(key)
    return result
