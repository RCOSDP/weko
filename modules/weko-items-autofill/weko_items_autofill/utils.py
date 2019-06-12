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
from invenio_db import db
from weko_records.api import ItemTypes, Mapping
from weko_workflow.models import ActionJournal

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
    results = dict()
    item_type_mapping = Mapping.get_record(item_type_id)
    try:
        for k, v in item_type_mapping.items():
            jpcoar = v.get("jpcoar_mapping")
            first_index = True
            if isinstance(jpcoar, dict):
                for u, s in jpcoar.items():
                    if results.get(u) is not None:
                        data = list()
                        if isinstance(results.get(u), list):
                            data = results.get(u)
                            data.append({u: s, "model_id": k})
                        else:
                            data.append({u: results.get(u)})
                            data.append({u: s, "model_id": k})
                        results[u] = data
                    else:
                        results[u] = s
                        if first_index and isinstance(results[u], dict):
                            results[u]['model_id'] = k
                            first_index = False
    except Exception as e:
        results['error'] = str(e)

    return results


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


@cached_api_json(timeout=50, key_prefix="crossref_data")
def get_crossref_record_data(pid, doi, item_type_id):
    """Get record data base on CrossRef API.

    :param pid: The PID
    :param doi: The DOI ID
    :param item_type_id: The item type ID
    :return:
    """
    result = list()
    api_response = CrossRefOpenURL(pid, doi).get_data()
    if api_response["error"]:
        return result
    api_data = get_crossref_data_by_key(api_response, 'all')
    with db.session.no_autoflush:
        items = ItemTypes.get_by_id(item_type_id)
    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = get_autofill_key_tree(
            items.form, get_crossref_autofill_item(item_type_id))
        result = build_record_model(autofill_key_tree, api_data)
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
            items.form, get_cinii_autofill_item(item_type_id))
        result = build_record_model(autofill_key_tree, api_data)
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
        if item.get('@language'):
            new_data['@language'] = item.get('@language')
        else:
            new_data['@language'] = default_language
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


def pack_data_with_multiple_type_cinii(data1, type1, data2, type2):
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
    default_language = 'ja'
    for item in data:
        for i in range(0, len(item)):
            new_data = dict()
            new_data['@value'] = item[i].get('@value')
            if item[i].get('@language'):
                new_data['@language'] = item[i].get('@language')
            else:
                new_data['@language'] = default_language
            result.append(new_data)
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
    default_language = 'ja'
    for item in data:
        if item.get('con:organization') is None:
            continue
        organization = item['con:organization'][0]
        if organization.get('foaf:name') is None:
            continue
        for i in range(0, len(organization.get('foaf:name'))):
            new_data = dict()
            new_data['@value'] = organization['foaf:name'][i].get('@value')
            if organization['foaf:name'][i].get('@language'):
                language = organization['foaf:name'][i].get('@language')
                new_data['@language'] = language
            else:
                new_data['@language'] = default_language
            result.append(new_data)
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
    except Exception:
        return pack_single_value_as_dict(None)


def get_cinii_numpage(data):
    """Get number of page.

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
            num_pages = end - start + 1
            return pack_single_value_as_dict(str(num_pages))
        except Exception:
            return pack_single_value_as_dict(None)


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


def get_cinii_data_by_key(api, keyword):
    """Get data from CiNii based on keyword.

    :param: api: CiNii data
    :param: keyword: keyword for search
    :return: data for keyword
    """
    data_response = api['response'].get('@graph')
    result = dict()
    if data_response is None:
        return result
    data = data_response[0]
    if (keyword == 'title' or keyword == 'alternative') \
            and data.get('dc:title'):
        result[keyword] = get_basic_cinii_data(data.get('dc:title'))
    elif keyword == 'creator' and data.get('dc:creator'):
        result[keyword] = get_cinii_creator_data(data.get('dc:creator'))
    elif keyword == 'contributor' and data.get('foaf:maker'):
        result[keyword] = get_cinii_contributor_data(data.get('foaf:maker'))
    elif keyword == 'description' and data.get('dc:description'):
        result[keyword] = get_cinii_description_data(
            data.get('dc:description')
        )
    elif keyword == 'subject' and data.get('foaf:topic'):
        result[keyword] = get_cinii_subject_data(data.get('foaf:topic'))
    elif keyword == 'sourceTitle' and data.get('prism:publicationName'):
        result[keyword] = get_basic_cinii_data(
            data.get('prism:publicationName')
        )
    elif keyword == 'volume' and data.get('prism:volume'):
        result[keyword] = pack_single_value_as_dict(data.get('prism:volume'))
    elif keyword == 'issue' and data.get('prism:number'):
        result[keyword] = pack_single_value_as_dict(data.get('prism:number'))
    elif keyword == 'pageStart' and data.get('prism:startingPage'):
        result[keyword] = get_cinii_page_data(data.get('prism:startingPage'))
    elif keyword == 'pageEnd' and data.get('prism:endingPage'):
        result[keyword] = get_cinii_page_data(data.get('prism:endingPage'))
    elif keyword == 'numPages':
        result[keyword] = get_cinii_numpage(data)
    elif keyword == 'date' and data.get('prism:publicationDate'):
        result[keyword] = get_cinii_date_data(
            data.get('prism:publicationDate'))
    elif keyword == 'publisher' and data.get('dc:publisher'):
        result[keyword] = get_basic_cinii_data(data.get('dc:publisher'))
    elif keyword == 'sourceIdentifier':
        result[keyword] = pack_data_with_multiple_type_cinii(
            data.get('prism:issn'),
            'ISSN',
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


def get_crossref_creator_data(data):
    """Get creator name from CrossRef data.

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


def get_crossref_numpage_data(data):
    """Get number of page from CrossRef data.

    Arguments:
        data -- page data

    Returns:
        Number of page is calculated and packed

    """
    num_pages = data.split('-')
    if len(num_pages) == 1:
        return pack_single_value_as_dict(
            current_app.config['WEKO_ITEMS_AUTOFILL_DEFAULT_PAGE_NUMBER'])
    else:
        try:
            num_page = int(num_pages[1]) - int(num_pages[0])
            return pack_single_value_as_dict(str(num_page))
        except Exception:
            return pack_single_value_as_dict(None)


def get_start_and_end_page(data, index):
    """Get start data and end date from CrossRef data.

    Arguments:
        data -- page data
        index -- Index in page array. 0 for start and 1 for end

    Returns:
        Start/End date is packed

    """
    num_pages = data.split('-')
    if len(num_pages) == 1:
        try:
            start_page = int(data)
            new_data = dict()
            new_data['@value'] = str(start_page)
            return new_data
        except Exception:
            new_data = dict()
            new_data['@value'] = None
            return new_data
    else:
        try:
            new_data = dict()
            end_page = int(num_pages[index])
            new_data['@value'] = str(end_page)
            return new_data
        except Exception:
            new_data = dict()
            new_data['@value'] = None
            return new_data


def get_crossref_issue_date(data):
    """Get crossref issued date.

    Arguments:
        data -- issued data

    Returns:
        Issued date is packed

    """
    result = dict()
    date = data.get('date-parts')
    if isinstance(date, list) and len(date) == 3:
        issued_date = '-'.join(str(e) for e in date)
        result['@value'] = issued_date
        result['@type'] = "Issued"
    else:
        result['@value'] = None
        result['@type'] = None
    return result


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


def get_crossref_relation_data(data):
    """Get CrossRef relation data.

    :param data:
    :return:
    """
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

    created = data.get('created')
    if created is None:
        return None
    page = data.get('page')

    if keyword == 'title' and created.get('title'):
        result[keyword] = get_crossref_title_data(created.get('title'))
    elif keyword == 'language':
        result[keyword] = pack_single_value_as_dict('eng')
    elif keyword == 'creator' and data.get('author'):
        result[keyword] = get_crossref_creator_data(data.get('author'))
    elif keyword == 'numPages' and page:
        result[keyword] = get_crossref_numpage_data(page)
    elif keyword == 'pageStart' and page:
        result[keyword] = get_start_and_end_page(page, 0)
    elif keyword == 'pageEnd' and page:
        result[keyword] = get_start_and_end_page(page, 1)
    elif keyword == 'date' and data.get('issued'):
        result[keyword] = get_crossref_issue_date(data.get('issued'))
    elif keyword == 'publisher' and created.get('publisher'):
        result[keyword] = get_crossref_publisher_data(created.get('publisher'))
    elif keyword == 'relation' and created.get('ISBN'):
        result[keyword] = get_crossref_relation_data(created.get('ISBN'))
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


def get_autofill_key_tree(schema_form, item):
    """Get auto fill key tree.

    :param schema_form: schema form
    :param item:
    :return:
    """
    result = dict()
    if not isinstance(item, dict):
        return None

    for key, val in item.items():
        if isinstance(val, dict) and 'model_id' in val.keys():
            parent_key = val['model_id']
            key_data = dict()
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
                result[key] = key_data
        elif isinstance(val, list):
            key_data = ""
            if key == "date":
                for date in val:
                    date_object = date.get("date")
                    if date_object.get("@value") and \
                            date_object.get("@attributes"):
                        key_data = get_key_value(
                            schema_form, date_object,
                            date.get("model_id"))
            if key_data:
                result[key] = key_data
    return result


def get_key_value(schema_form, val, parent_key):
    """Get key value.

    :param schema_form: Schema form
    :param val: Schema form value
    :param parent_key:
    :return:
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
    :return:
    """
    result = dict()
    key_result = ''
    try:
        for item in schema_form:
            if item.get("key") == parent_key:
                items_list = item.get("items")
                for item_data in items_list:
                    if child_key in item_data.get("key"):
                        key_result = item_data.get("key")
                    elif item_data.get("items"):
                        item_data_child_list = item_data.get("items")
                        for item_data_child in item_data_child_list:
                            if child_key in item_data_child.get("key"):
                                key_result = item_data_child.get("key")
        result['key'] = key_result
    except Exception as e:
        result['key'] = None
        result['error'] = str(e)

    return result


def build_record_model(item_autofill_key, api_data):
    """Build record model.

    :param item_autofill_key:  Item auto fill key
    :param api_data: Api data
    :return:
    """
    record_model = list()
    if not api_data or not item_autofill_key:
        return record_model
    for key, value in item_autofill_key.items():
        data = api_data.get(key)
        if data is None:
            continue
        model = dict()
        child_data = None
        sub_child_data = dict()
        multi_data = list()
        parent_key = ""
        child_key = ""
        is_list = False
        if value.get("@value"):
            key_list = value.get("@value").split(".")
            if key_list:
                if "[]" in key_list[0]:
                    is_list = True
                parent_key = key_list[0].replace("[]", "")
                if not isinstance(model.get(parent_key), list):
                    model[parent_key] = list()
                if len(key_list) == 2:
                    child_data = dict()
                elif len(key_list) == 3:
                    child_data = list()
                    child_key = key_list[1].replace("[]", "")
        else:
            continue

        if isinstance(data, list):
            for data_object in data:
                build_record(
                    data_object, value, child_data, sub_child_data)
                if child_data:
                    multi_data.append(child_data.copy())
                elif sub_child_data:
                    multi_data.append(sub_child_data.copy())
        else:
            build_record(data, value, child_data, sub_child_data)
        if model:
            model["key"] = key
            if sub_child_data:
                if multi_data:
                    child_data = multi_data
                elif sub_child_data:
                    child_data.append(sub_child_data)
                model[parent_key].append({child_key: child_data})
            else:
                if multi_data:
                    if is_list:
                        model[parent_key] = multi_data
                    else:
                        model[parent_key] = multi_data[0]
                elif child_data:
                    if is_list:
                        model[parent_key].append(child_data)
                    else:
                        model[parent_key] = child_data
            record_model.append(model)

    return record_model


def build_record(data, value, child_data, sub_child_data):
    """Build record.

    :param data: API data
    :param value: Model key value
    :param child_data: Child data
    :param sub_child_data: Sub child data
    """
    for k, v in data.items():
        if not value.get(k) or not v:
            continue
        if isinstance(child_data, dict):
            child_key_list = value.get(k).split(".")
            if child_key_list and len(child_key_list) == 2:
                sub_key = child_key_list[1].replace("[]", "")
                child_data[sub_key] = convert_html_escape(v)
        elif isinstance(child_data, list):
            child_key_list = value.get(k).split(".")
            if child_key_list and len(child_key_list) == 3:
                sub_key = child_key_list[2].replace("[]", "")
                sub_child_data[sub_key] = convert_html_escape(v)


def get_workflow_journal(activity_id):
    """Get workflow journal data.

    :param activity_id: The identify of Activity.
    :return: Workflow journal data
    """
    journal_data = dict()
    with db.session.no_autoflush:
        journal = ActionJournal.query.filter_by(
            activity_id=activity_id).one_or_none()
        if journal:
            journal_data = journal.action_journal
    return journal_data
