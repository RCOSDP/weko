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
import json
import traceback
from functools import wraps

from flask import current_app
from flask_babelex import gettext as _
from lxml import etree
from jsonschema import validate, ValidationError

from invenio_cache import current_cache
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier

from weko_admin.utils import get_current_api_certification
from weko_records.api import ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping
from weko_workflow.api import WorkActivity
from weko_workflow.models import ActionJournal
from weko_workflow.utils import MappingData

from . import config
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
            key = key_prefix
            for value in args:
                key += str(value)
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


def get_item_id(item_type_id):
    """Get dictionary contain item id.

    Get from mapping between item type and jpcoar
    :param item_type_id: The item type id
    :return: dictionary
    """
    def _get_jpcoar_mapping(rtn_results, jpcoar_data):
        for u, s in jpcoar_data.items():
            if rtn_results.get(u) is not None:
                data = list()
                if isinstance(rtn_results.get(u), list):
                    data = rtn_results.get(u)
                    data.append({u: {**s, "model_id": k}})
                else:
                    rtn_results.get(u)
                    data.append({u: rtn_results.get(u)})
                    data.append({u: {**s, "model_id": k}})
                rtn_results[u] = data
            else:
                rtn_results[u] = s
                rtn_results[u]['model_id'] = k

    results = dict()
    item_type_mapping = Mapping.get_record(item_type_id)
    try:
        for k, v in item_type_mapping.items():
            if isinstance(v, dict):
                jpcoar = v.get("jpcoar_mapping")
                if isinstance(jpcoar, dict):
                    _get_jpcoar_mapping(results, jpcoar)
    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
        results['error'] = str(e)

    return results


def _get_title_data(jpcoar_data, key, rtn_title):
    """Get title data.

    @param jpcoar_data: JPCOAR data
    @param key: index key
    @param rtn_title: title list
    """
    try:
        if str(key).find('item') != -1:
            rtn_title['title_parent_key'] = key
            title_value = jpcoar_data['title']
            if '@value' in title_value.keys():
                rtn_title['title_value_lst_key'] = title_value[
                    '@value'].split('.')
            if '@attributes' in title_value.keys():
                title_lang = title_value['@attributes']
                if 'xml:lang' in title_lang.keys():
                    rtn_title['title_lang_lst_key'] = title_lang[
                        'xml:lang'].split('.')
        else:
            #current_app.logger.debug("not contain 'item' in key:{}".format(key))
            return
    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()


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
    title = dict()
    for k, v in sorted(item_type_mapping.items()):
        if isinstance(v, dict):
            jpcoar = v.get("jpcoar_mapping")
            if isinstance(jpcoar, dict) and 'title' in jpcoar.keys():
                _get_title_data(jpcoar, k, title)
                if title:
                    break
    result['title'] = title
    return result


def remove_empty(data):
    """
    Recursively remove empty values from dictionaries and lists.

    This function traverses the input data structure 
    (which can be a dictionary, list, or other type)
    and removes any elements that are considered "empty". 
    Empty values include: None, empty strings,
    empty dictionaries, empty lists, and lists containing 
    only an empty dictionary ([{}]).

    Args:
        data (Any): The input data structure to be cleaned.

    Returns:
        Any: The cleaned data structure with all empty values removed.
    """
    if isinstance(data, dict):
        return {k: v for k, v in ((k, remove_empty(v)) for k, v in data.items())
                if v not in (None, '', {}, [], [{}])}
    elif isinstance(data, list):
        cleaned = [remove_empty(item) for item in data]
        cleaned = [
            item for item in cleaned if item not in (None, '', {}, [], [{}])
        ]
        return cleaned
    else:
        return data

def get_doi_record_data(doi, item_type_id, activity_id):
    """Get record data base on DOI API.

    Args:
        doi (str): DOI
        item_type_id (int): Item type ID
        activity_id (int): Activity ID

    Returns:
        list: List of record data
    """
    activity = WorkActivity()
    temp_data = activity.get_activity_metadata(activity_id)
    metadata = temp_data if isinstance(temp_data, dict) else json.loads(temp_data)
    metainfo = metadata.get("metainfo")
    metainfo_cleaned = remove_empty(metainfo)
    doi_with_original = fetch_metadata_by_doi(doi, item_type_id, metainfo)
    doi_response = [{k: v} for k, v in doi_with_original.items()]

    return doi_response


def fetch_metadata_by_doi(doi, item_type_id, original=None, **kwargs):
    """Get record data base on DOI API.

    Get metadata from APIs by supclied DOI ID and fill in the metadata
    in order of priority.

    Args:
        doi (str): DOI
        item_type_id (int): Item type ID
        original (dict): Original metadata
        kwargs (dict): optional arguments
            - meta_data_api (list): List of metadata APIs to use <br>
                (e.g., ["JaLC API", "医中誌 Web API", "CrossRef", "DataCite"])

    Returns:
        dict: Merged metadata from APIs and original metadata
    """
    from weko_workspace.utils import (
        get_jalc_record_data,
        get_jamas_record_data,
        get_datacite_record_data,
        get_cinii_record_data
    )
    api_funcs = {
        "JaLC API": get_jalc_record_data,
        "医中誌 Web API": get_jamas_record_data,
        "CrossRef": get_crossref_record_data_with_pid,
        "DataCite": get_datacite_record_data,
        "CiNii Research": get_cinii_record_data,
    }

    api_priority = kwargs.get("meta_data_api")

    # Check if api_priority is None.
    # api_priority is not None if it comes from SWORD API.
    if not isinstance(api_priority, list):
        api_priority = current_app.config["WEKO_ITEMS_AUTOFILL_TO_BE_USED"]
    # If api_priority is empty, apply original metadata.
    if not api_priority:
        api_priority = ["Original"]

    result = {}
    for key in reversed(api_priority):
        response_metadata = {}
        # case: Original.
        if key == "Original":
            if isinstance(original, dict):
                for k, v in original.items():
                    if isinstance(v, dict):
                        filtered = {kk: vv for kk, vv in v.items() if vv}
                        if filtered:
                            response_metadata[k] = filtered
                    elif isinstance(v, list):
                        filtered = [
                            item for item in v 
                                if item and 
                                    (not isinstance(item, dict) or any(item.values()))
                        ]
                        if filtered:
                            response_metadata[k] = filtered
                    elif v:
                        response_metadata[k] = v
            else:
                current_app.logger.info("original metadata is not found.")
                continue
        # case: APIs.
        # If some exception occurs, record_data_dict will be empty.
        # It means that skip this API.
        else:
            try:
                response_list = (
                    api_funcs[key](doi, item_type_id)
                    if key in api_funcs else []
                )
                response_metadata = {
                    k: v for item in response_list
                    if isinstance(item, dict) for k, v in item.items()
                }
                current_app.logger.info(
                    f"Successfully get metadata from {key} with DOI: {doi}."
                )
            except Exception as ex:
                current_app.logger.warning(
                    f"Failed to get metadata from {key}"
                )
                traceback.print_exc()
        result.update(response_metadata)
    return result


def get_crossref_record_data_with_pid(doi, item_type_id):
    """
    Get record data base on CrossRef default pid.

    Args:
        doi (str): DOI
        item_type_id (int): Item type ID

    Returns:
        list: List of record data
    """
    pid_response = get_current_api_certification("crf")
    pid = pid_response["cert_data"]
    return get_crossref_record_data(pid, doi, item_type_id)


@cached_api_json(timeout=50, key_prefix="crossref_data")
def get_crossref_record_data(pid, doi, item_type_id, exclude_duplicate_lang=True):
    """Get record data base on CrossRef API.

    Args:
        pid (str): PID
        doi (str): DOI
        item_type_id (int): Item type ID
        exclude_duplicate_lang (bool): Exclude duplicate language

    Returns:
        list: List of record data
    """
    result = list()
    api_response = CrossRefOpenURL(pid, doi).get_data()
    current_app.logger.debug("CrossRefOpenURL.get_data():{}".format(api_response))
    if api_response["error"]:
        return result
    api_response = convert_crossref_xml_data_to_dictionary(
        api_response['response'])
    current_app.logger.debug("convert_crossref_xml_data_to_dictionary():{}".format(api_response))
    if api_response["error"]:
        return result
    api_data = get_crossref_data_by_key(api_response, 'all')
    with db.session.no_autoflush:
        items = ItemTypes.get_by_id(item_type_id)
    if items is None:
        return result
    if items.form is not None:
        autofill_key_tree = sort_by_item_type_order(
            items.form,
            get_autofill_key_tree(
                items.form,
                get_crossref_autofill_item(item_type_id)))
        result = build_record_model(
            autofill_key_tree, api_data, items.schema,
            exclude_duplicate_lang=exclude_duplicate_lang
        )
    return result


@cached_api_json(timeout=50, key_prefix="cinii_data")
def get_cinii_record_data(naid, item_type_id):
    """Get record data base on CiNii API.

    :param naid: The CiNii ID
    :param item_type_id: The item type ID
    :return:
    """
    result = list()
    api_response = CiNiiURL(naid).get_data()
    if api_response["error"] \
            or not isinstance(api_response['response'], dict):
        return result
    api_data = get_cinii_data_by_key(api_response, 'all')
    items = ItemTypes.get_by_id(item_type_id)
    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = get_autofill_key_tree(
            items.form, get_cinii_autofill_item(item_type_id)
        )
        result = build_record_model(autofill_key_tree, api_data, items.schema)
    return result


def get_basic_cinii_data(data):
    """Get basic data template from CiNii.

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
        new_data['@language'] = item['@language'] if item.get('@language') else default_language
        result.append(new_data)
    return result


def pack_single_value_as_dict(data):
    """Pack value as dictionary.

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


def pack_data_with_multiple_type_cinii(data, type1, type2):
    """Map CiNii multi data with type.

    Arguments:
        data1
        type1
        data2
        type2

    Returns:
        packed data

    """
    result = list()
    _data = {item["@type"]:item["@value"] for item in data}
    if type1 in _data:
        new_data = dict()
        new_data['@value'] = _data[type1]
        new_data['@type'] = type1
        result.append(new_data)
    if type2 in _data:
        new_data = dict()
        new_data['@value'] = _data[type2]
        new_data['@type'] = type2
        result.append(new_data)
    return result


def get_cinii_creator_data(data):
    """Get creator data from CiNii.

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: creator data
    :return: list of creator name
    """
    result = list()
    for item in data:
        name_data = item.get('foaf:name')
        if name_data:
            result.append(get_basic_cinii_data(name_data))
    return result


def get_cinii_contributor_data(data):
    """Get contributor data from CiNii.

    Get contributor name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    for item in data:
        name_data = item.get("foaf:name")
        if name_data:
            result.append(get_basic_cinii_data(name_data))
    return result


def get_cinii_description_data(data):
    """Get description data from CiNii.

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
    default_type = 'Abstract'
    for item in data:
        notations = item.get("notation")
        if notations is None:
            continue
        for notation in notations:
            new_data = dict()
            new_data['@value'] = notation.get('@value')
            new_data['@type'] = item["type"] if item.get("type") else default_type
            new_data["@language"] = notation["@language"] if notation.get("@language") else default_language
            result.append(new_data)
    return result


def get_cinii_subject_data(data):
    """Get subject data from CiNii.

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
        new_data["@scheme"] = "Other"
        new_data["@URI"] = sub.get("@id")
        new_data["@value"] = sub.get("dc:title")
        new_data["@language"] = default_language
        result.append(new_data)
    return result


def get_cinii_page_data(data):
    """Get start page and end page data.

    Get page info and pack it:
    {
        '@value': number
    }

    :param: data: No of page
    :return: packed data
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(str(result))
    except Exception as e:
        current_app.logger.error(e)
        return pack_single_value_as_dict(None)


def get_cinii_numpage(data):
    """Get number of page.

    If CiNii have pageRange, get number of page
    If not, number of page equals distance between start and end page

    :param: data: CiNii data
    :return: number of page is packed
    """
    if data.get('jpcoar:numPages'):
        return get_cinii_page_data(data.get('jpcoar:numPages'))
    if data.get('prism:startingPage') and data.get('prism:endingPage'):
        try:
            end = int(data.get('prism:endingPage'))
            start = int(data.get('prism:startingPage'))
            num_pages = end - start + 1
            return pack_single_value_as_dict(str(num_pages))
        except Exception as e:
            current_app.logger.error(e)
            return pack_single_value_as_dict(None)
    return {"@value": None}


def get_cinii_date_data(data):
    """Get publication date.

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

def get_cinii_product_identifier(data, type1, type2):
    _data = [item.get('identifier') for item in data]
    result = pack_data_with_multiple_type_cinii(_data, type1, type2)
    return result

def get_cinii_data_by_key(api, keyword):
    """Get data from CiNii based on keyword.

    :param: api: CiNii data
    :param: keyword: keyword for search
    :return: data for keyword
    """
    data_response = api['response']
    result = dict()
    if data_response is None:
        return result
    data = data_response
    if keyword == 'title' and data.get('dc:title'):
        result[keyword] = get_basic_cinii_data(data.get('dc:title'))
    elif keyword == 'alternative' and data.get('dcterms:alternative'):
        result[keyword] = get_basic_cinii_data(data.get('dcterms:alternative'))
    elif keyword == 'creator' and data.get('creator'):
        result[keyword] = get_cinii_creator_data(data.get('creator'))
    elif keyword == 'contributor' and data.get('contributor'):
        result[keyword] = get_cinii_contributor_data(data.get('contributor'))
    elif keyword == 'description' and data.get('description'):
        result[keyword] = get_cinii_description_data(
            data.get('description')
        )
    elif keyword == 'subject' and data.get('foaf:topic'):
        result[keyword] = get_cinii_subject_data(data.get('foaf:topic'))
    elif keyword == 'sourceTitle' and data.get('publication') \
        and data.get('publication').get('prism:publicationName'):
        result[keyword] = get_basic_cinii_data(
            data.get('publication').get('prism:publicationName')
        )
    elif keyword == 'volume' and data.get('publication') \
        and data.get("publication").get('prism:volume'):
        result[keyword] = pack_single_value_as_dict(data.get("publication").get('prism:volume'))
    elif keyword == 'issue' and data.get('publication') \
        and data.get("publication").get('prism:number'):
        result[keyword] = pack_single_value_as_dict(data.get("publication").get('prism:number'))
    elif keyword == 'pageStart' and data.get('publication') \
        and data.get("publication").get('prism:startingPage'):
        result[keyword] = get_cinii_page_data(data.get("publication").get('prism:startingPage'))
    elif keyword == 'pageEnd' and data.get('publication') \
        and data.get('publication').get('prism:endingPage'):
        result[keyword] = get_cinii_page_data(data.get("publication").get('prism:endingPage'))
    elif keyword == 'numPages' and data.get('publication'):
        result[keyword] = get_cinii_numpage(data.get('publication'))
    elif keyword == 'date' and data.get('publication') \
        and data.get('publication').get('prism:publicationDate'):
        result[keyword] = get_cinii_date_data(
            data.get('publication').get('prism:publicationDate'))
    elif keyword == 'publisher' and data.get('publication') \
        and data.get('publication').get('dc:publisher'):
        result[keyword] = get_basic_cinii_data(data.get('publication').get('dc:publisher'))
    elif keyword == 'sourceIdentifier' and data.get('publication') \
        and data.get('publication').get('publicationIdentifier'):
        result[keyword] = pack_data_with_multiple_type_cinii(
            data.get('publication').get('publicationIdentifier'),
            'ISSN',
            'NCID'
        )
    elif keyword == "relation" and data.get('productIdentifier'):
        result[keyword] = get_cinii_product_identifier(
            data.get('productIdentifier'),
            'NAID',
            'DOI'
        )
    elif keyword == 'all':
        for key in current_app.config[
                'WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM']:
            result[key] = get_cinii_data_by_key(api, key).get(key)
    return result


def get_crossref_title_data(data):
    """Get title data from CrossRef.

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


def _build_name_data(data):
    """Build name data from CrossRef data.

    @param data: CrossRef data
    @return: Name list
    """
    result = list()
    default_language = 'en'
    for name_data in data:
        family_name = name_data.get('family')
        given_name = name_data.get('given')
        full_name = ''
        if given_name and family_name:
            full_name = family_name + " " + given_name
        elif given_name:
            full_name = given_name
        elif family_name:
            full_name = family_name
        new_data = dict()
        new_data['@value'] = full_name
        new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_crossref_creator_data(data):
    """Get creator name from CrossRef data.

    Arguments:
        data -- CrossRef data

    """
    return _build_name_data(data)


def get_crossref_contributor_data(data):
    """Get contributor name from CrossRef data.

    Arguments:
        data -- CrossRef data

    """
    return _build_name_data(data)


def get_start_and_end_page(data):
    """Get start page and end page data.

    Get page info and pack it:
    {
        '@value': number
    }

    :param: data: No of page
    :return: packed data
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(str(result))
    except ValueError as e:
        current_app.logger.error(e)
        return pack_single_value_as_dict(None)


def get_crossref_issue_date(data):
    """Get CrossRef issued date.

    Arguments:
        data -- issued data

    Returns:
        Issued date is packed

    """
    result = dict()
    if data:
        result['@value'] = data
        result['@type'] = 'Issued'
    else:
        result['@value'] = None
        result['@type'] = None
    return result


def get_crossref_source_title_data(data):
    """Get source title information.

    Arguments:
        data -- created data

    Returns:
        Source title  data

    """
    new_data = dict()
    default_language = 'en'
    new_data['@value'] = data
    new_data['@language'] = default_language
    return new_data


def get_crossref_publisher_data(data):
    """Get publisher information.

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


def get_crossref_relation_data(isbn, doi):
    """Get CrossRef relation data.

    :param isbn, doi:
    :return:
    """
    result = list()
    if doi:
        new_data = dict()
        new_data['@value'] = doi
        new_data['@type'] = "DOI"
        result.append(new_data)
    if isbn and len(result) == 0:
        for element in isbn:
            new_data = dict()
            new_data['@value'] = element
            new_data['@type'] = "ISBN"
            result.append(new_data)
    if len(result) == 0:
        return pack_single_value_as_dict(None)
    return result


def get_crossref_source_data(data):
    """Get CrossRef source data.

    :param data:
    :return:
    """
    result = list()
    if data:
        new_data = dict()
        new_data['@value'] = data
        new_data['@type'] = 'ISSN'
        result.append(new_data)
    return result


def get_crossref_data_by_key(api, keyword):
    """Get CrossRef data based on keyword.

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
    if keyword == 'title' and data.get('article_title'):
        result[keyword] = get_crossref_title_data(data.get('article_title'))
    elif keyword == 'creator' and data.get('author'):
        result[keyword] = get_crossref_creator_data(data.get('author'))
    elif keyword == 'contributor' and data.get('contributor'):
        result[keyword] = get_crossref_contributor_data(data.get('contributor'))
    elif keyword == 'sourceTitle' and data.get('journal_title'):
        result[keyword] = get_crossref_source_title_data(
            data.get('journal_title')
        )
    elif keyword == 'volume' and data.get('volume'):
        result[keyword] = pack_single_value_as_dict(data.get('volume'))
    elif keyword == 'issue' and data.get('issue'):
        result[keyword] = pack_single_value_as_dict(data.get('issue'))
    elif keyword == 'pageStart' and data.get('first_page'):
        result[keyword] = get_start_and_end_page(data.get('first_page'))
    elif keyword == 'pageEnd' and data.get('last_page'):
        result[keyword] = get_start_and_end_page(data.get('last_page'))
    elif keyword == 'date' and data.get('year'):
        result[keyword] = get_crossref_issue_date(data.get('year'))
    elif keyword == 'relation':
        result[keyword] = get_crossref_relation_data(
            data.get('isbn'),
            data.get('doi')
        )
    elif keyword == 'sourceIdentifier':
        result[keyword] = get_crossref_source_data(data.get('issn'))
    elif keyword == 'all':
        for key in current_app.config[
                'WEKO_ITEMS_AUTOFILL_CROSSREF_REQUIRED_ITEM']:
            result[key] = get_crossref_data_by_key(api, key).get(key)
    return result


def get_cinii_autofill_item(item_id):
    """Get CiNii autofill item.

    :param item_id: Item ID.
    :return:
    """
    jpcoar_item = get_item_id(item_id)
    cinii_req_item = dict()
    for key in current_app.config['WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM']:
        if jpcoar_item.get(key) is not None:
            cinii_req_item[key] = jpcoar_item.get(key)
    return cinii_req_item


def get_crossref_autofill_item(item_id):
    """Get CrossRef autofill item.

    :param item_id: Item ID
    :return:
    """
    jpcoar_item = get_item_id(item_id)
    crossref_req_item = dict()
    for key in current_app.config[
            'WEKO_ITEMS_AUTOFILL_CROSSREF_REQUIRED_ITEM']:
        if jpcoar_item.get(key) is not None:
            crossref_req_item[key] = jpcoar_item.get(key)
    return crossref_req_item


def get_autofill_key_tree(schema_form, item, result=None):
    """Get auto fill key tree.

    :param schema_form: schema form
    :param item: The mapping items
    :param result: The key result
    :return: Autofill key tree
    """
    if result is None:
        result = dict()
    if not isinstance(item, dict):
        return None

    for key, val in item.items():
        if isinstance(val, dict) and 'model_id' in val.keys():
            parent_key = val['model_id']
            key_data = dict()
            if parent_key == "pubdate":
                continue
            if key == "creator":
                creator_name_object = val.get("creatorName")
                if creator_name_object:
                    key_data = get_key_value(schema_form,
                                             creator_name_object, parent_key)
            elif key == "contributor":
                contributor_name = val.get("contributorName")
                if contributor_name:
                    key_data = get_key_value(schema_form,
                                             contributor_name, parent_key)
            elif key == "relation":
                related_identifier = val.get("relatedIdentifier")
                if related_identifier:
                    key_data = get_key_value(schema_form,
                                             related_identifier, parent_key)
            else:
                key_data = get_key_value(schema_form, val, parent_key)
            if key_data:
                if isinstance(result.get(key), list):
                    result[key].append({key: key_data})
                elif result.get(key):
                    result[key] = [{key: result.get(key)}, {key: key_data}]
                else:
                    result[key] = key_data
        elif isinstance(val, list):
            for mapping_data in val:
                get_autofill_key_tree(schema_form, mapping_data, result)

    return result


def sort_by_item_type_order(item_forms, autofill_key_tree):
    """Sort autofill_key_tree by order of item type.

    :param item_forms: List forms in order to get item order
    :param autofill_key_tree: autofill key tree
    :return: Sorted autofill_key_tree
    """
    def get_parent_key(_item):
        """Get parent key of item in sub autofill_key_tree.

        :param _item: Mapping objet
        :return: Parent key
        """
        if isinstance(_item, str):
            parent_key = _item.split('.')[0]
            return parent_key.replace('[]', '')
        if isinstance(_item, dict):
            if _item.get('@value'):
                parent_key = _item.get('@value').split('.')[0]
                return parent_key.replace('[]', '')
            values = _item.values()
            values_list = list(values)
            first_value = values_list[0]
            return get_parent_key(first_value)

    # Get all parent key of items in item type.
    item_form_key_list = [i.get('key') for i in item_forms]
    # Sort index autofill key tree by order of item type.
    for k, v in autofill_key_tree.items():
        if isinstance(v, list):
            temp = []
            for item_form_key in item_form_key_list:
                for item in v:
                    str_value = get_parent_key(item)
                    if item_form_key == str_value:
                        temp.append(item)
                        break
                if len(temp) > 0:
                    break
            # Reset sorted value.
            autofill_key_tree[k] = temp
    return autofill_key_tree


def get_key_value(schema_form, val, parent_key):
    """Get key value.

    :param schema_form: Schema form
    :param val: Schema form value
    :param parent_key: The parent key
    :return: The key value
    """
    key_data = dict()
    if val.get("@value") is not None:
        value_key = val.get('@value')
        key_data['@value'] = get_autofill_key_path(
            schema_form,
            parent_key,
            value_key
        ).get('key')

    if val.get("@attributes") is not None:
        value_key = val.get('@attributes')
        if value_key.get("xml:lang") is not None:
            key_data['@language'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("xml:lang")
            ).get('key')
        if value_key.get("identifierType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("identifierType")
            ).get('key')
        if value_key.get("descriptionType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("descriptionType")
            ).get('key')
        if value_key.get("subjectScheme") is not None:
            key_data['@scheme'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("subjectScheme")
            ).get('key')
        if value_key.get("subjectURI") is not None:
            key_data['@URI'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("subjectURI")
            ).get('key')
        if value_key.get("dateType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("dateType")
            ).get('key')

    return key_data


def get_autofill_key_path(schema_form, parent_key, child_key):
    """Get auto fill key path.

    :param schema_form: Schema form
    :param parent_key: Parent key
    :param child_key: Child key
    :return: The key path
    """
    result = dict()
    key_result = ''
    existed = False
    try:
        for item in schema_form:
            if item.get("key") == parent_key:
                items_list = item.get("items")
                for item_data in items_list:
                    if existed:
                        break
                    existed, key_result = get_specific_key_path(
                        child_key.split('.'), item_data)
        result['key'] = key_result
    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
        result['key'] = None
        result['error'] = str(e)

    return result


def get_specific_key_path(des_key, form):
    """Get specific path of des_key on form.

    @param des_key: Destination key
    @param form: The form key list
    @return: Existed flag and path result
    """
    existed = False
    path_result = None
    if isinstance(form, dict):
        list_keys = form.get("key", None)
        if list_keys:
            list_keys = list_keys.replace('[]', '').split('.')
            # Always remove the first element because it is parents key
            list_keys.pop(0)
            if set(list_keys) == set(des_key):
                existed = True
        if existed:
            return existed, form.get("key")
        elif not existed and form.get("items"):
            return get_specific_key_path(des_key, form.get("items"))
    elif isinstance(form, list):
        for child_form in form:
            if existed:
                break
            existed, path_result = get_specific_key_path(des_key, child_form)
    return existed, path_result


def build_record_model(
    item_autofill_key, api_data, schema=None, exclude_duplicate_lang=False
):
    """Build record record_model.

    Args:
        item_autofill_key (dict): Item auto-fill key
        api_data (dict): Api data
        schema (dict): Schema
        exclude_duplicate_lang (bool): Exclude duplicate language

    Returns:
        list: Record model list
    """
    def _build_record_model(
        _api_data, _item_autofill_key, _record_model_lst,
        _filled_key, _schema, _exclude_duplicate_lang
    ):
        """Build record model.

        Args:
            _api_data (dict): Api data
            _item_autofill_key (dict): Item auto-fill key
            _record_model_lst (list): Record model list
            _filled_key (list): Filled key list
            _schema (dict): Schema
            _exclude_duplicate_lang (bool): Exclude duplicate language
        """
        for k, v in _item_autofill_key.items():
            data_model = {}
            api_autofill_data = _api_data.get(k)
            if not api_autofill_data or k in _filled_key:
                continue
            if isinstance(v, dict):
                build_form_model(data_model, v)
            elif isinstance(v, list):
                for mapping_data in v:
                    _build_record_model(
                        _api_data, mapping_data, _record_model_lst,
                        _filled_key, _schema, _exclude_duplicate_lang
                    )
            record_model = {}
            for key, value in data_model.items():
                merge_dict(record_model, value)
            new_record_model = fill_data(
                record_model, api_autofill_data, _schema, _exclude_duplicate_lang
            )
            if new_record_model:
                _record_model_lst.append(new_record_model)
                _filled_key.append(k)

    record_model_lst = list()
    filled_key = list()
    if not api_data or not item_autofill_key:
        return record_model_lst
    _build_record_model(
        api_data, item_autofill_key, record_model_lst,
        filled_key, schema, exclude_duplicate_lang
    )

    return record_model_lst


def build_model(form_model, form_key):
    """Build model.

    @param form_model:
    @param form_key:
    """
    child_model = {}
    if '[]' in form_key:
        form_key = form_key.replace("[]", "")
        child_model = []
    if isinstance(form_model, dict):
        form_model[form_key] = child_model
    else:
        form_model.append({form_key: child_model})


def build_form_model(form_model, form_key, autofill_key=None):
    """Build form model.

    @param form_model:
    @param form_key:
    @param autofill_key:
    """
    if isinstance(form_key, dict):
        for k, v in form_key.items():
            if isinstance(v, str) and v:
                arr = v.split('.')
                form_model[k] = {}
                build_form_model(form_model[k], arr, k)
    elif isinstance(form_key, list):
        if len(form_key) > 1:
            key = form_key.pop(0)
            build_model(form_model, key)
            key = key.replace("[]", "")
            if isinstance(form_model, dict):
                build_form_model(form_model[key], form_key,
                                 autofill_key)
            else:
                build_form_model(form_model[0].get(key), form_key,
                                 autofill_key)
        elif len(form_key) == 1:
            key = form_key.pop(0)
            if isinstance(form_model, list):
                form_model.append({key: autofill_key})
            elif isinstance(form_model, dict):
                form_model[key] = autofill_key


def merge_dict(original_dict, merged_dict, over_write=True):
    """Merge dictionary.

    @param original_dict: the original dictionary.
    @param merged_dict: the merged dictionary.
    @param over_write: the over write flag.
    """
    if isinstance(original_dict, list) and isinstance(merged_dict, list):
        for data in merged_dict:
            for data_1 in original_dict:
                merge_dict(data_1, data)
    elif isinstance(original_dict, dict) and isinstance(merged_dict, dict):
        for key in merged_dict:
            if key in original_dict:
                if isinstance(original_dict[key], (dict, list)) and isinstance(
                        merged_dict[key], (dict, list)):
                    merge_dict(original_dict[key], merged_dict[key])
                elif original_dict[key] == merged_dict[key]:
                    continue
                else:
                    if over_write:
                        merged_dict[key] = original_dict[key]
                    else:
                        current_app.logger.error('Conflict at "{}"'.format(key))
            else:
                original_dict[key] = merged_dict[key]


def deepcopy(original_object, new_object):
    """Copy dictionary object.

    @param original_object: the original object.
    @param new_object: the new object.
    @return:
    """
    import copy
    if isinstance(original_object, dict):
        for k, v in original_object.items():
            new_object[k] = copy.deepcopy(v)
    elif isinstance(original_object, list):
        for original_data in original_object:
            if isinstance(original_data, (dict, list)):
                deepcopy(copy.deepcopy(original_data), new_object)
    else:
        return


def fill_data(form_model, autofill_data, schema=None, exclude_duplicate_lang=False):
    """Fill data to form model.

    @param form_model: the form model.
    @param autofill_data: the autofill data
    @param is_multiple_data: multiple flag.
    """
    result = {} if isinstance(form_model, dict) else []
    is_multiple_data = is_multiple(form_model, autofill_data)

    def validate_data(data, sub_schema):
        if sub_schema is None:
            current_app.logger.debug("=== Validation skipped ===")
            return True
        try:
            validate(instance=data, schema=sub_schema)
            current_app.logger.debug(f"Validation passed: {data} matches schema {sub_schema}")
            return True
        except ValidationError as e:
            current_app.logger.debug(f"Validation failed: {e.message}")
            return False

    if isinstance(autofill_data, list):
        key = list(form_model.keys())[0] if len(form_model) != 0 else None
        sub_schema = None
        if schema:
            sub_schema = get_subschema(schema, key)
            if sub_schema and sub_schema.get("type") == "array":
                sub_schema = sub_schema.get("items")

        if is_multiple_data or (not is_multiple_data and isinstance(form_model.get(key),list)):
            model_clone = {}
            deepcopy(form_model[key][0], model_clone)
            result[key]=[]
            used_lang_set = set()
            for data in autofill_data:
                if exclude_duplicate_lang and isinstance(data, dict) and data.get('@language'):
                    if data.get('@language') in used_lang_set:
                        continue
                    used_lang_set.add(data.get('@language'))
                model = {}
                deepcopy(model_clone, model)
                new_model = fill_data(model, data, sub_schema, exclude_duplicate_lang)
                result[key].append(new_model.copy())
        else:
            result = fill_data(form_model, autofill_data[0], schema, exclude_duplicate_lang)
    elif isinstance(autofill_data, dict):
        if isinstance(form_model, dict):
            for k, v in form_model.items():
                subschema = get_subschema(schema, k)
                if isinstance(v, str):
                    value = autofill_data.get(v, '')
                    if not validate_data(value, subschema):
                        continue
                    result[k] = value
                else:
                    new_v = fill_data(v, autofill_data, subschema, exclude_duplicate_lang)
                    result[k] = new_v
        elif isinstance(form_model, list):
            for v in form_model:
                new_v = fill_data(v, autofill_data, schema, exclude_duplicate_lang)
                result.append(new_v)
    else:
        return
    return result


def get_subschema(schema, key):
    """Get sub schema.

    Args:
        schema (dict): The schema to search in.
        key (str): The key to search for.
    Returns:
        dict: The sub schema if found, otherwise None.
    """
    if not schema:
        return None

    if schema.get("type") == "object" and "properties" in schema:
        return schema["properties"].get(key)

    if schema.get("type") == "array" and "items" in schema:
        return get_subschema(schema["items"], key)

    return None


def is_multiple(form_model, autofill_data):
    """Check form model.

    @param form_model: Form model data.
    @param autofill_data: Autofill data.
    @return: True if form model can auto-fill with multiple data.
    """
    if isinstance(autofill_data, list) and len(autofill_data) > 1:
        for key in form_model:
            return isinstance(form_model[key], list)
    else:
        return False


def get_workflow_journal(activity_id):
    """Get workflow journal data.

    :param activity_id: The identify of Activity.
    :return: Workflow journal data
    """
    journal_data = None
    with db.session.no_autoflush:
        journal = ActionJournal.query.filter_by(
            activity_id=activity_id).one_or_none()
        if journal:
            journal_data = journal.action_journal
    return journal_data


def convert_crossref_xml_data_to_dictionary(api_data, encoding='utf-8'):
    """Convert CrossRef XML data to dictionary.

    :param api_data: CrossRef xml data
    :param encoding: Encoding type
    :return: CrossRef data is converted to dictionary.
    """
    result = {}
    rtn_data = {
        'response': {},
        'error': ''
    }
    try:
        root = etree.XML(api_data.encode(encoding))
        crossref_xml_data_keys = config.WEKO_ITEMS_AUTOFILL_CROSSREF_XML_DATA_KEYS
        contributor_roles = config.WEKO_ITEMS_AUTOFILL_CROSSREF_CONTRIBUTOR
        for elem in root.getiterator():
            if etree.QName(elem).localname in crossref_xml_data_keys:
                if etree.QName(elem).localname == "contributor" or etree.QName(
                        elem).localname == "organization":
                    _get_contributor_and_author_names(elem, contributor_roles,
                                                      result)
                elif etree.QName(elem).localname == "year":
                    if 'media_type' in elem.attrib \
                            and elem.attrib['media_type'] == "print":
                        result.update({etree.QName(elem).localname: elem.text})
                elif etree.QName(elem).localname in ["issn", "isbn"]:
                    if 'type' in elem.attrib \
                            and elem.attrib['type'] == "print":
                        result.update({etree.QName(elem).localname: elem.text})
                else:
                    result.update({etree.QName(elem).localname: elem.text})
        rtn_data['response'] = result
    except Exception as e:
        rtn_data['error'] = str(e)
        traceback.print_exc()
    return rtn_data


def _get_contributor_and_author_names(elem, contributor_roles, rtn_data):
    """Get contributor and author name from API response data.

    @param elem: API data
    @param contributor_roles: Contributor roles
    @param rtn_data: Return data
    """
    temp = {}
    for element in elem.getiterator():
        if etree.QName(element).localname == 'given_name':
            temp.update({"given": element.text})
        if etree.QName(element).localname == 'surname':
            temp.update({"family": element.text})
    if elem.attrib['contributor_role'] in contributor_roles:
        if "contributor" in rtn_data:
            rtn_data["contributor"].append(temp)
        else:
            rtn_data.update({"contributor": [temp]})
    else:
        if "author" in rtn_data:
            rtn_data["author"].append(temp)
        else:
            rtn_data.update({"author": [temp]})


def get_wekoid_record_data(recid, item_type_id):
    """Get data from this system by recid.

    @param search_data: recid
    """
    from weko_items_ui.utils import get_hide_parent_and_sub_keys, \
        has_permission_edit_item
    ignore_mapping = current_app.config['WEKO_ITEMS_AUTOFILL_IGNORE_MAPPING']
    # Get item id.
    pid = PersistentIdentifier.get('recid', recid)
    # Get source mapping info.
    mapping_src = MappingData(pid.object_uuid)
    record_src = mapping_src.record
    # Check permission.
    permission = has_permission_edit_item(record_src, recid)
    if not permission:
        raise ValueError(_("The item cannot be copied because "
                           "you do not have permission to view it."))
    # Get keys of 'Hide' items.
    item_type = mapping_src.get_data_item_type()
    hide_parent_key, hide_sub_keys = get_hide_parent_and_sub_keys(item_type)
    # Get data source and remove value of hide item.
    item_map_src = mapping_src.item_map
    item_map_data_src = {}
    for mapping_key, item_key in item_map_src.items():
        data = mapping_src.get_data_by_mapping(mapping_key, False,
                                               hide_sub_keys, hide_parent_key)
        values = [value for key, value in data.items() if value]
        if values and values[0] and mapping_key not in ignore_mapping:
            item_map_data_src[mapping_key] = values[0]
    # Get destination mapping info.
    item_map_des = get_mapping(item_type_id, "jpcoar_mapping")
    item_map_data_des = {}
    for mapping_key, item_key_str in item_map_des.items():
        for item_key in item_key_str.split(','):
            if mapping_key in item_map_data_src.keys():
                value = item_map_data_src.get(mapping_key)
                if not all(x is None for x in value):
                    item_map_data_des[item_key] = value
                    break
    # Convert structure of schema to record model.
    record_model = build_record_model_for_wekoid(
        item_type_id, item_map_data_des)
    # Set value for record model.
    result = set_val_for_record_model(record_model, item_map_data_des)
    return result


def build_record_model_for_wekoid(item_type_id, item_map_data):
    """Build record model map with structure of metadata.

    @param item_type_id: id of item type.
    @param item_map_data: is dict, key is mapping,
        value are values of item on this mapping key.
    """
    from weko_records.api import ItemTypes

    # Get parent key of item has value to improve performence.
    item_has_val = set()
    for k, v in item_map_data.items():
        item_has_val.add(k.split('.')[0])
    # Convert structure of schema to record model.
    # Default value is [] or {}.
    item_type = ItemTypes.get_by_id(item_type_id)
    properties = item_type.schema.get('properties')
    result = []
    for k, v in properties.items():
        if k not in item_has_val:
            continue
        res_temp = {k: [] if is_multiple_item(v) else {}}
        props = v.get('properties') or v.get('items', {}).get(
            'properties') or None
        if props:
            get_record_model(res_temp, k, props)
        result.append(res_temp)
    return result


def is_multiple_item(val):
    """Check current item is multiple.

    @param val:
    """
    if isinstance(val, dict):
        if val.get('items', {}).get('properties'):
            return True
    return False


def get_record_model(res_temp, key, properties):
    """Build sub record model.

    @param res_temp:
    @param key:
    @param properties:
    """
    if isinstance(res_temp, list):
        item_temp = {}
        for item in res_temp:
            if item.get(key) in [[], {}]:
                item_temp = item
                break
        index = res_temp.index(item_temp)
        temp = res_temp[index]
    else:
        temp = res_temp[key]

    if isinstance(temp, list):
        temp_1 = {}
        for k, v in properties.items():
            if isinstance(v, dict):
                temp_1[k] = [] if is_multiple_item(v) else {}
                props = v.get('properties') or v.get('items', {}).get(
                    'properties') or None
                if props:
                    get_record_model(temp_1, k, props)
        temp.append(temp_1)
    if isinstance(temp, dict):
        for k, v in properties.items():
            if isinstance(v, dict):
                temp[k] = [] if is_multiple_item(v) else {}
                props = v.get('properties') or v.get('items', {}).get(
                    'properties') or None
                if props:
                    get_record_model(temp, k, props)


def set_val_for_record_model(record_model, item_map_data):
    """Set value for record model by item_map_data.

    @param record_model:
    @param item_map_data:
    """
    the_most_levels = 0
    for k, v in item_map_data.items():
        keys = k.split('.')
        if len(keys) > the_most_levels:
            the_most_levels = len(keys)
        set_val_for_all_child(keys, record_model, v)
    # Remove item if value is empty.
    # values map with this condition => remove.
    condition = [[], {}, [{}], '']
    for item in record_model:
        for i in range(0, the_most_levels):
            remove_sub_record_model_no_value(item, condition)
    return record_model


def set_val_for_all_child(keys, models, values):
    """Set value for sub record model.

    @param keys:
    @param models:
    @param values:
    """
    import copy
    model_temp = None
    for key in keys:
        for model in models:
            if model.get(key):
                model_temp = model[key]
    if isinstance(model_temp, dict):
        for val in values:
            for k, v in model_temp.items():
                if k == keys[-1]:
                    model_temp[k] = val if val else ''
    if isinstance(model_temp, list):
        organization_item = copy.deepcopy(model_temp[0])
        for i, val in enumerate(values):
            if i < len(model_temp):
                # Set value for case multiple data.
                if not model_temp[i].get(keys[-1]) is None and model_temp[i][
                        keys[-1]].get(keys[-1]) is None:
                    model_temp[i][keys[-1]] = val if val else ''
                else:
                    for k, v in model_temp[i].items():
                        if isinstance(v, dict) and not v.get(keys[-1]) is None:
                            model_temp[i][k] = v
                            model_temp[i][k][keys[-1]] = val if val else ''
                        if isinstance(v, list) and not v[0].get(
                                keys[-1]) is None:
                            model_temp[i][k] = v
                            model_temp[i][k][0][keys[-1]] = val if val else ''
            else:
                # The first time set value for this item.
                temp = copy.deepcopy(organization_item)
                if not temp.get(keys[-1]) is None and temp[keys[-1]].get(
                        keys[-1]) is None:
                    temp[keys[-1]] = val if val else ''
                else:
                    for k, v in temp.items():
                        if isinstance(v, dict) and not v.get(keys[-1]) is None:
                            temp[k] = v
                            temp[k][keys[-1]] = val if val else ''
                        if isinstance(v, list) and not v[0].get(
                                keys[-1]) is None:
                            temp[k] = v
                            temp[k][0][keys[-1]] = val if val else ''
                model_temp.append(temp)


def remove_sub_record_model_no_value(item, condition):
    """Remove sub record model no value.

    @param keys:
    @param models:
    @param values:
    """
    if isinstance(item, dict):
        temp = copy.deepcopy(item)
        for k, v in temp.items():
            if v in condition:
                del item[k]
            else:
                remove_sub_record_model_no_value(item[k], condition)
    if isinstance(item, list):
        item = [] if item in condition else item
        for sub_item in item:
            remove_sub_record_model_no_value(sub_item, condition)

