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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Utilities for convert response json."""
import copy
import pickle
import gzip
import json
import xml.etree.ElementTree as Et
from datetime import datetime
from io import SEEK_END, SEEK_SET, BytesIO
from uuid import UUID
from xml.etree.ElementTree import tostring

import redis
from redis import sentinel
from elasticsearch.exceptions import NotFoundError
from flask import Markup, Response, abort, current_app, jsonify, request
from flask_babelex import gettext as _
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.errors import FileInstanceAlreadySetError, \
    FilesException, UnexpectedFileSizeError
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_search import RecordsSearch
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import asc
from sqlalchemy.orm.exc import MultipleResultsFound
from weko_admin.models import AdminLangSettings
from weko_index_tree.api import Indexes
from weko_records.api import Mapping, ItemTypes
from weko_records.serializers.utils import get_mapping
from weko_records_ui.utils import get_pair_value
from weko_redis.redis import RedisConnection
from weko_search_ui.query import item_search_factory
from weko_theme import config as theme_config

from . import config
from .models import WidgetDesignPage, WidgetDesignSetting, WidgetType


def get_widget_type_list():
    """Get all Widget types.

    :param: None
    :return: options json
    """
    widget_types = WidgetType.get_all_widget_types()
    options = []
    if isinstance(widget_types, list):
        for widget_type in widget_types:
            option = dict()
            option["text"] = widget_type.type_name
            option["value"] = widget_type.type_id
            options.append(option)
    result = {"options": options}

    return result


def delete_item_in_preview_widget_item(data_id, json_data):
    """Delete item in preview widget design.

    Arguments:
        data_id {widget_item} -- [id of widget item]
        json_data {dict} -- [data to be updated]

    Returns:
        [data] -- [data after updated]

    """
    remove_list = []
    if isinstance(json_data, list):
        for item in json_data:
            if str(item.get('name')) == str(data_id.get('label')) and str(
                    item.get('type')) == str(data_id.get('widget_type')):
                remove_list.append(item)
    for item in remove_list:
        json_data.remove(item)
    data = json.dumps(json_data)
    return data


def convert_popular_data(source_data, des_data):
    """Convert popular data.

    Arguments:
        source_data {dict} -- Source data
        des_data {dict} -- Destination data

    """
    des_data['background_color'] = source_data.get('background_color')
    des_data['label_enable'] = source_data.get('label_enable')
    des_data['theme'] = source_data.get('theme')
    if des_data['theme'] != "simple":
        des_data['frame_border_color'] = source_data.get('frame_border_color')
        des_data['border_style'] = source_data.get('border_style')
    if des_data['label_enable']:
        des_data['label_text_color'] = source_data.get('label_text_color')
        des_data['label_color'] = source_data.get('label_color')


def update_general_item(item, data_result):
    """Update general field item.

    :param item: item need to be update
    :param data_result: result
    """
    convert_popular_data(data_result, item)
    item['name'] = data_result.get('label')
    item['type'] = data_result.get('widget_type')
    item['multiLangSetting'] = data_result.get('multiLangSetting')
    settings = data_result.get('settings')
    widget_type = data_result.get('widget_type')
    if widget_type == config.WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE:
        update_access_counter_item(item, settings)
    elif widget_type == config.WEKO_GRIDLAYOUT_NEW_ARRIVALS_TYPE:
        update_new_arrivals_item(item, settings)
    elif widget_type == config.WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE:
        update_menu_item(item, settings)
    elif widget_type == config.WEKO_GRIDLAYOUT_HEADER_WIDGET_TYPE:
        _build_header_setting_data(item, data_result)


def update_menu_item(item, data_result):
    """Update widget item type Menu.

    Arguments:
        item {WidgetItem} -- Item need to be update
        data_result {dict} -- [data to update]

    """
    item['menu_orientation'] = data_result.get('menu_orientation')
    item['menu_bg_color'] = data_result.get('menu_bg_color')
    item['menu_active_bg_color'] = data_result.get('menu_active_bg_color')
    item['menu_default_color'] = data_result.get('menu_default_color')
    item['menu_active_color'] = data_result.get('menu_active_color')
    item['menu_show_pages'] = data_result.get('menu_show_pages')


def update_access_counter_item(item, data_result):
    """Update widget item type Access Counter.

    Arguments:
        item {WidgetItem} -- Item need to be update
        data_result {dict} -- [data to update]

    """
    item['access_counter'] = data_result.get('access_counter')
    item['preceding_message'] = data_result.get('preceding_message')
    item['following_message'] = data_result.get('following_message')
    item['other_message'] = data_result.get('other_message')
    item['count_start_date'] = data_result.get('count_start_date')


def update_new_arrivals_item(item, data_result):
    """Update widget item type New Arrivals.

    Arguments:
        item {WidgetItem} -- Item need to be update
        data_result {dict} -- [data to update]

    """
    item['new_dates'] = data_result.get('new_dates')
    item['display_result'] = data_result.get('display_result')
    item['rss_feed'] = data_result.get('rss_feed')


def get_default_language():
    """Get default Language.

    :return:
    """
    result = get_register_language()
    if isinstance(result, list):
        return result[0]
    return ""


def get_unregister_language():
    """Get unregister Language.

    :return:
    """
    result = AdminLangSettings.query.filter_by(is_registered=False)
    return AdminLangSettings.parse_result(result)


def get_register_language():
    """Get register language."""
    result = AdminLangSettings.query.filter_by(is_registered=True).order_by(
        asc('admin_lang_settings_sequence'))
    return AdminLangSettings.parse_result(result)


def get_system_language():
    """Get system language for widget setting.

    Returns:
        result -- dictionary contains language list

    """
    result = {
        'language': [],
        'error': ''
    }
    try:
        sys_lang = AdminLangSettings.load_lang()
        result['language'] = sys_lang
    except Exception as e:
        result['error'] = str(e)

    return result


def build_data(data):
    """Build data get from client to dictionary.

    Arguments:
        data {json} -- Client data

    Returns:
        dictionary -- server data

    """
    result = dict()
    result['repository_id'] = data.get('repository')
    result['widget_type'] = data.get('widget_type')
    result['settings'] = json.dumps(build_data_setting(data))
    result['is_enabled'] = data.get('enable')

    multi_lang_data = data.get('multiLangSetting').copy()
    _escape_html_multi_lang_setting(multi_lang_data)
    result['multiLangSetting'] = multi_lang_data

    result['is_deleted'] = False
    result['locked'] = False
    result['locked_by_user'] = None
    return result


def _escape_html_multi_lang_setting(multi_lang_setting: dict):
    """Escape unsafe html.

    :param multi_lang_setting:
    """
    for k, v in multi_lang_setting.items():
        if isinstance(v, dict):
            _escape_html_multi_lang_setting(v)
        else:
            if k not in ["description", "more_description"]:
                multi_lang_setting[k] = Markup.escape(v)


def build_data_setting(data):
    """Build setting pack.

    Arguments:
        data {json} -- client data

    Returns:
        dictionary -- setting pack

    """
    result = dict()
    convert_popular_data(data, result)
    setting = data['settings']
    widget_type = data.get('widget_type')
    if widget_type == config.WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE:
        _build_access_counter_setting_data(result, setting)
    elif widget_type == config.WEKO_GRIDLAYOUT_NEW_ARRIVALS_TYPE:
        _build_new_arrivals_setting_data(result, setting)
    elif widget_type == config.WEKO_GRIDLAYOUT_NOTICE_TYPE:
        _build_notice_setting_data(result, setting)
    elif widget_type == config.WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE:
        color = config.WEKO_GRIDLAYOUT_WIDGET_DEFAULT_COLOR
        result['menu_orientation'] = data['settings'].get(
            'menu_orientation') or 'horizontal'
        result['menu_bg_color'] = data['settings'].get(
            'menu_bg_color') or color
        result['menu_active_bg_color'] = data['settings'].get(
            'menu_active_bg_color') or color
        result['menu_default_color'] = data['settings'].get(
            'menu_default_color') or color
        result['menu_active_color'] = data['settings'].get(
            'menu_active_color') or color
        result['menu_show_pages'] = data['settings'].get(
            'menu_show_pages') or []
    elif widget_type == config.WEKO_GRIDLAYOUT_HEADER_WIDGET_TYPE:
        _build_header_setting_data(result, data)
    return result


def _build_access_counter_setting_data(result, setting):
    """Build Access Counter setting data.

    :param result:
    :param setting:
    """
    result['access_counter'] = Markup.escape(
        setting.get('access_counter')) or '0'
    result['following_message'] = Markup.escape(
        setting.get('following_message')) or ''
    result['other_message'] = Markup.escape(
        setting.get('other_message')) or ''
    result['preceding_message'] = Markup.escape(
        setting.get('preceding_message')) or ''
    result['count_start_date'] = Markup.escape(
        setting.get('count_start_date')) or ''


def _build_new_arrivals_setting_data(result, setting):
    """Build New Arrivals setting data.

    :param result:
    :param setting:
    """
    result['new_dates'] = Markup.escape(
        setting.get('new_dates')) or config.WEKO_GRIDLAYOUT_DEFAULT_NEW_DATE
    result['display_result'] = Markup.escape(setting.get(
        'display_result')) or config.WEKO_GRIDLAYOUT_DEFAULT_DISPLAY_RESULT
    result['rss_feed'] = setting.get('rss_feed') or False


def _build_notice_setting_data(result, setting):
    """Build notice setting data.

    :param result:
    :param setting:
    """
    result['hide_the_rest'] = Markup.escape(setting.get('setting'))
    result['read_more'] = Markup.escape(setting.get('read_more'))


def _build_header_setting_data(result, setting):
    """Build header setting data.

    @param result:
    @param setting:
    """
    result['fixedHeaderBackgroundColor'] = setting.get(
        'fixedHeaderBackgroundColor')
    result['fixedHeaderTextColor'] = setting.get('fixedHeaderTextColor')


def build_multi_lang_data(widget_id, multi_lang_json):
    """Build multiple language data.

    Arguments:
        widget_id {sequence} -- id of widget
        multi_lang_json {json} -- multiple language data as json

    Returns:
        dictionary -- multiple language data

    """
    if not multi_lang_json:
        return None

    result = list()
    for k, v in multi_lang_json.items():
        new_lang_data = dict()
        new_lang_data['widget_id'] = widget_id
        new_lang_data['lang_code'] = k
        new_lang_data['label'] = Markup.escape(v.get('label'))
        new_lang_data['description_data'] = json.dumps(v.get('description'))
        result.append(new_lang_data)
    return result


def convert_widget_data_to_dict(widget_data):
    """Convert widget data object to dict.

    Arguments:
        widget_data {object} -- Object data

    Returns:
        dictionary -- dictionary data

    """
    result = dict()
    settings = json.loads(widget_data.settings) \
        if isinstance(widget_data.settings, str) else widget_data.settings

    result['widget_id'] = widget_data.widget_id
    result['repository_id'] = widget_data.repository_id
    result['widget_type'] = widget_data.widget_type
    result['settings'] = settings
    result['is_enabled'] = widget_data.is_enabled
    result['is_deleted'] = widget_data.is_deleted
    result['updated'] = widget_data.updated.timestamp()
    return result


def convert_widget_multi_lang_to_dict(multi_lang_data):
    """Convert multiple language data object to dict.

    Arguments:
        multi_lang_data {object} -- object data

    Returns:
        dictionary -- dictionary data

    """
    result = dict()
    description = json.loads(multi_lang_data.description_data) \
        if isinstance(multi_lang_data.description_data, str) \
        else multi_lang_data.description_data

    result['id'] = multi_lang_data.id
    result['widget_id'] = multi_lang_data.widget_id
    result['lang_code'] = multi_lang_data.lang_code
    result['label'] = multi_lang_data.label
    result['description_data'] = description
    return result


def convert_data_to_design_pack(widget_data, list_multi_lang_data):
    """Convert loaded data to widget design data pack.

    Arguments:
        widget_data {dict} -- widget data
        list_multi_lang_data {list} -- List of multiple language data

    Returns:
        dictionary -- widget design data pack

    """
    if not widget_data or not list_multi_lang_data:
        return None
    result = dict()
    result['widget_id'] = widget_data.get('widget_id')
    result['repository_id'] = widget_data.get('repository_id')
    result['widget_type'] = widget_data.get('widget_type')
    result['is_enabled'] = widget_data.get('is_enabled')
    result['is_deleted'] = widget_data.get('is_deleted')
    result['updated'] = widget_data.get('updated')

    multi_lang_setting = dict()
    for data in list_multi_lang_data:
        new_data = dict()
        converted_data = convert_widget_multi_lang_to_dict(data)
        new_data['label'] = converted_data.get('label')
        new_data['description'] = converted_data.get('description_data')
        multi_lang_setting[converted_data.get('lang_code')] = new_data
    settings = widget_data.get('settings')
    settings['multiLangSetting'] = multi_lang_setting
    result['settings'] = settings

    return result


def convert_data_to_edit_pack(data):
    """Convert loaded data to edit data pack.

    Arguments:
        data {dict} -- loaded data

    Returns:
        dictionary -- edit data pack

    """
    if not data:
        return None
    result = dict()
    result_settings = dict()
    settings = pickle.loads(pickle.dumps(data.get('settings'), -1))
    convert_popular_data(settings, result)
    result['widget_id'] = data.get('widget_id')
    result['is_enabled'] = data.get('is_enabled')
    result['enable'] = data.get('is_enabled')
    result['multiLangSetting'] = settings.get('multiLangSetting')
    result['repository_id'] = data.get('repository_id')
    result['widget_type'] = data.get('widget_type')
    result['updated'] = data.get('updated')
    widget_type = data.get('widget_type')
    if widget_type == config.WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE:
        result_settings['access_counter'] = settings.get('access_counter')
        result_settings['preceding_message'] = settings.get(
            'preceding_message')
        result_settings['following_message'] = settings.get(
            'following_message')
        result_settings['other_message'] = settings.get('other_message')
        result_settings['count_start_date'] = settings.get('count_start_date')
    if widget_type == config.WEKO_GRIDLAYOUT_NEW_ARRIVALS_TYPE:
        result_settings['new_dates'] = settings.get('new_dates')
        result_settings['display_result'] = settings.get('display_result')
        result_settings['rss_feed'] = settings.get('rss_feed')
    if widget_type == config.WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE:
        update_menu_item(result_settings, settings)
    if widget_type == config.WEKO_GRIDLAYOUT_HEADER_WIDGET_TYPE:
        _build_header_setting_data(result_settings, settings)
    result['settings'] = result_settings
    return result


def build_rss_xml(data=None, index_id=0, page=1, count=20, term=0, lang=''):
    """Build RSS data as XML format.

    Arguments:
        data {dictionary} -- Elastic search data
        term {int} -- The term

    Returns:
        xml response -- RSS data as XML

    """
    root_url = str(request.url_root).replace('/api/', '/')
    root = Et.Element('rdf:RDF')
    root.set('xmlns', config.WEKO_XMLNS)
    root.set('xmlns:rdf', config.WEKO_XMLNS_RDF)
    root.set('xmlns:rdfs', config.WEKO_XMLNS_RDFS)
    root.set('xmlns:dc', config.WEKO_XMLNS_DC)
    root.set('xmlns:prism', config.WEKO_XMLNS_PRISM)
    root.set('xmlns:lang', lang)

    # First layer
    requested_url = root_url + 'rss/records?index_id=' + str(index_id) + \
        '&page=' + str(page) + '&term=' + str(term) + \
        '&count=' + str(count) + '&lang=' + str(lang)
    channel = Et.SubElement(root, 'channel')
    channel.set('rdf:about', requested_url)

    # Channel layer
    Et.SubElement(channel, 'title').text = 'WEKO3'
    Et.SubElement(channel, 'link').text = requested_url
    if index_id:
        index_detail = Indexes.get_index(index_id)
        Et.SubElement(channel, 'description').text = index_detail.comment \
            or index_detail.index_name \
            or index_detail.index_name_english
    else:
        Et.SubElement(channel, 'description').text = \
            theme_config.THEME_SITENAME
    current_time = datetime.now()
    Et.SubElement(
        channel,
        'dc:date').text = current_time.isoformat() + '+00:00'
    items = Et.SubElement(channel, 'items')
    seq = Et.SubElement(items, 'rdf:Seq')
    if not data or not isinstance(data, list):
        xml_str = tostring(root, encoding='utf-8')
        xml_str = str.encode(
            config.WEKO_XML_FORMAT) + xml_str
        return Response(
            xml_str,
            mimetype='text/xml')
    items = [idx for idx in range((page - 1) * count, page * count)]
    item_idx = 0

    # add item layer
    for data_item in data:
        if item_idx not in items:
            item_idx = item_idx + 1
            continue
        item = Et.Element('item')
        item.set('rdf:about', find_rss_value(
            data_item,
            'link'))
        Et.SubElement(item, 'title').text = find_rss_value(
            data_item,
            'title')
        Et.SubElement(item, 'link').text = find_rss_value(
            data_item,
            'link')
        see_also = Et.SubElement(item, 'rdfs:seeAlso')
        see_also.set('rdf:resource', find_rss_value(
            data_item,
            'seeAlso'))

        if isinstance(find_rss_value(data_item, 'creator'), list):
            for creator in find_rss_value(data_item, 'creator'):
                Et.SubElement(item, 'dc:creator').text = creator
        else:
            Et.SubElement(item, 'dc:creator').text = find_rss_value(
                data_item,
                'creator')
        Et.SubElement(item, 'dc:publisher').text = find_rss_value(
            data_item,
            'publisher')
        Et.SubElement(item, 'prism:publicationName').text = find_rss_value(
            data_item,
            'sourceTitle')
        Et.SubElement(item, 'prism:issn').text = find_rss_value(
            data_item,
            'issn')
        Et.SubElement(item, 'prism:volume').text = find_rss_value(
            data_item,
            'volume')
        Et.SubElement(item, 'prism:number').text = find_rss_value(
            data_item,
            'issue')
        Et.SubElement(item, 'prism:startingPage').text = find_rss_value(
            data_item,
            'pageStart')
        Et.SubElement(item, 'prism:endingPage').text = find_rss_value(
            data_item,
            'pageEnd')
        Et.SubElement(item, 'prism:publicationDate').text = find_rss_value(
            data_item,
            'date')
        Et.SubElement(item, 'description').text = find_rss_value(
            data_item,
            'description')
        Et.SubElement(item, 'dc:date').text = find_rss_value(
            data_item,
            '_updated'
        )
        li = Et.SubElement(seq, 'rdf:li')
        li.set('rdf:resource', find_rss_value(
            data_item,
            'link'))
        root.append(item)
        item_idx = item_idx + 1
    xml_str = tostring(root, encoding='utf-8')
    xml_str = str.encode(config.WEKO_XML_FORMAT) + xml_str
    response = current_app.response_class()
    response.data = xml_str
    response.headers['Content-Type'] = 'application/xml'
    return response


def find_rss_value(data, keyword):
    """Analyze rss data from elasticsearch data.

    Arguments:
        data {dictionary} -- elasticsearch data
        keyword {string} -- The keyword

    Returns:
        string -- data for the keyword

    """
    if not data or not data.get('_source'):
        return None

    source = data.get('_source')
    meta_data = source.get('_item_metadata')

    if keyword == 'title':
        return meta_data.get('item_title')
    elif keyword == 'link':
        root_url = request.url_root
        root_url = str(root_url).replace('/api/', '/')
        record_number = get_rss_data_source(
            meta_data,
            'control_number')
        return '' if record_number == '' else \
            root_url + 'records/' + record_number
    elif keyword == 'seeAlso':
        return config.WEKO_RDF_SCHEMA
    elif keyword == 'creator':
        if source.get('creator'):
            creator = source.get('creator')
            if (not creator or not creator.get('familyName')
                    or not creator.get('givenName')):
                return ''
            else:
                family_name = creator.get('familyName')
                given_name = creator.get('givenName')
                list_creator = list()
                for i in range(0, len(family_name)):
                    if family_name[i]:
                        if given_name[i]:
                            list_creator.append(
                                family_name[i] + '.' + given_name[i])
                        else:
                            list_creator.append(family_name[i])
                    else:
                        continue
                return list_creator
        else:
            return ''
    elif keyword == 'publisher':
        return get_rss_data_source(source, 'publisher')
    elif keyword == 'sourceTitle':
        return get_rss_data_source(source, 'sourceTitle')
    elif keyword == 'issn':
        result = ''
        if source.get('sourceIdentifier') and source.get(
                'sourceIdentifier')[0]:
            source_identifier = source.get('sourceIdentifier')[0]
            result = get_rss_data_source(source_identifier, 'value')
        return result
    elif keyword == 'volume':
        return get_rss_data_source(source, 'volume')
    elif keyword == 'issue':
        return get_rss_data_source(source, 'issue')
    elif keyword == 'pageStart':
        return get_rss_data_source(source, 'pageStart')
    elif keyword == 'pageEnd':
        return get_rss_data_source(source, 'pageEnd')
    elif keyword == 'date':
        result = ''
        if source.get('date') and source.get('date')[0] and \
            get_rss_data_source(source.get('date')[0], 'dateType') == \
                'Issued':
            result = get_rss_data_source(source.get('date')[0], 'value')
        return result
    elif keyword == 'description':
        res = ''
        if source.get('description') and source.get('description')[0]:
            from weko_items_ui.utils import get_options_and_order_list, get_hide_list_by_schema_form

            item_type_id = source.get('_item_metadata').get('item_type_id')
            item_type = ItemTypes.get_by_id(item_type_id)
            hide_list = []
            if item_type:
                meta_option = get_options_and_order_list(
                    item_type_id,
                    item_type_data=ItemTypes(item_type.schema, model=item_type),
                    mapping_flag=False)
                hide_list = get_hide_list_by_schema_form(schemaform=item_type.render.get('table_row_map', {}).get('form', []))
            else:
                meta_option = get_options_and_order_list(item_type_id, mapping_flag=False)
            item_map = get_mapping(item_type_id, "jpcoar_mapping", item_type=item_type)
            desc_typ_list = item_map.get('description.@attributes.descriptionType').split(',')
            desc_val_list = item_map.get('description.@value').split(',')
            for desc_val in desc_val_list:
                skip_flag = False
                val_key_list = desc_val.split('.')
                for desc_typ in desc_typ_list:
                    typ_key_list = desc_typ.split('.')
                if val_key_list[0] == typ_key_list[0]:
                    prop_hidden = meta_option.get(val_key_list[0], {}).get('option', {}).get('hidden', False)
                    desc_dat = source.get('_item_metadata').get(typ_key_list[0])
                    if desc_dat and desc_dat.get('attribute_value_mlt') and not prop_hidden:
                        for h in hide_list:
                            if h.startswith(val_key_list[0]) and h.endswith(val_key_list[-1]):
                                skip_flag = True
                                break
                        if not skip_flag:
                            list_des_data = get_pair_value(val_key_list[1:],
                                                           typ_key_list[1:],
                                                           desc_dat.get('attribute_value_mlt'))
                            for des_text, des_type in list_des_data:
                                if des_type == 'Abstract':
                                    res = des_text
        return res
    elif keyword == '_updated':
        return get_rss_data_source(source, '_updated')
    else:
        return ''


def get_rss_data_source(source, keyword):
    """Get data from source tree.

    Arguments:
        source {dictionary} -- Source tree
        keyword {string} -- The keyword

    Returns:
        string -- data of keyword in source tree

    """
    if source.get(keyword):
        if isinstance(source.get(keyword), list):
            return source.get(keyword)[0]
        return source.get(keyword)
    else:
        return ''


def get_elasticsearch_result_by_date(start_date, end_date, query_with_publish_status=False):
    """Get data from elastic search.

    Arguments:
        start_date {string} -- start date
        end_date {string} -- end date
        query_with_publish_status {bool} -- Only query public items

    Returns:
        dictionary -- elastic search data

    """
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    result = None
    try:
        search_instance, _qs_kwargs = item_search_factory(
            None, records_search, start_date, end_date, None,
            query_with_publish_status, False)
        search_result = search_instance.execute()
        result = search_result.to_dict()
    except NotFoundError:
        current_app.logger.debug('Indexes do not exist yet!')

    return result


# Validation
def validate_main_widget_insertion(repository_id, new_settings, page_id=0):
    """Validate that no page or main layout contains main widget."""
    # If the main_settings has no main, no need to check anyway
    if not has_main_contents_widget(new_settings):
        return True

    # Check if main design has main widget
    main_design = \
        WidgetDesignSetting.select_by_repository_id(repository_id or '')
    settings = json.loads(main_design.get('settings', '[]')) if isinstance(
        main_design.get('settings', '[]'), str) else main_design.get('settings')
    main_has_main = has_main_contents_widget(settings) if main_design else False

    # Get page which has main
    page_with_main = get_widget_design_page_with_main(repository_id)
    existing_page = WidgetDesignPage.get_by_id_or_none(page_id or 0)

    # Case 1 Neither main design or page design has main widget
    if not main_has_main and not page_with_main:
        return True

    # Case 2: Updating main widget design which already has main
    elif main_has_main and not page_with_main and not existing_page:
        return True

    # Case 3: We are updating a page which already has main -- if not False
    elif not main_has_main and page_with_main and existing_page:
        return page_with_main.id == existing_page.id
    return False


def get_widget_design_page_with_main(repository_id):
    """Get the page which contains Main contents widget."""
    if repository_id:
        for page in WidgetDesignPage.get_by_repository_id(repository_id):
            if page.settings and has_main_contents_widget(
                    json.loads(page.settings)
                    if isinstance(page.settings, str) else page.settings):
                return page
    return None


def main_design_has_main_widget(repository_id):
    """Check if main design has main widget.

    Args:
        repository_id (_type_): _description_

    Returns:
        bool: _description_
    """
    main_design = WidgetDesignSetting.select_by_repository_id(repository_id)
    if main_design:
        settings = json.loads(main_design.get('settings', '[]')) \
            if isinstance(main_design.get('settings', '[]'), str) \
            else main_design.get('settings')
        return has_main_contents_widget(settings)
    return False


def has_main_contents_widget(settings):
    """Check if settings contains the main contents widget.

    Args:
        settings (_type_): _description_

    Returns:
        _type_: _description_
    """    
    if settings:
        for item in settings:
            if item.get('type') == config.WEKO_GRIDLAYOUT_MAIN_TYPE:
                return True
    return False


def get_widget_design_setting(repository_id, current_language, page_id=None):
    """Get widget design setting.

    @param repository_id: The repository identifier
    @param current_language: The current language
    @param page_id: The Page identifier.
    @return:
    """
    def validate_response():
        """Check the response data can compress with gzip.

        @return: True if the response data can compress with gzip
        """
        is_valid = True
        accept_encoding = request.headers.get('Accept-Encoding', '')
        response = jsonify({})
        if not config.WEKO_GRIDLAYOUT_IS_COMPRESS_WIDGET or \
            response.direct_passthrough or \
            'gzip' not in accept_encoding.lower() or \
                'Content-Encoding' in response.headers:
            is_valid = False
        return is_valid

    def get_widget_response(_page_id):
        """Get widget setting response.

        :param _page_id: The Page identifier.
        @return: The widget setting response
        """
        lang_code = current_language or get_default_language()
        if _page_id:
            from .services import WidgetDesignPageServices
            widget_setting_data = WidgetDesignPageServices\
                .get_widget_design_setting(_page_id, lang_code)
        else:
            from .services import WidgetDesignServices
            widget_setting_data = WidgetDesignServices\
                .get_widget_design_setting(
                    repository_id, lang_code)
        return jsonify(widget_setting_data)

    if validate_response() and current_language:
        if page_id:
            key = (config.WEKO_GRIDLAYOUT_WIDGET_PAGE_CACHE_KEY
                   + repository_id + "_" + page_id + "_" + current_language)
        else:
            key = (config.WEKO_GRIDLAYOUT_WIDGET_CACHE_KEY
                   + repository_id + "_" + current_language)
        if current_cache.get(key) is None:
            data = compress_widget_response(get_widget_response(page_id))
            current_cache.set(key, data)
            return data
        else:
            return current_cache.get(key)
    else:
        return get_widget_response(page_id)


def compress_widget_response(response):
    """Compress widget response.

    @param response: The response data
    @return: The response data is compressed
    """
    gzip_buffer = BytesIO()
    gzip_file = gzip \
        .GzipFile(mode='wb',
                  compresslevel=config.WEKO_GRIDLAYOUT_COMPRESS_LEVEL,
                  fileobj=gzip_buffer)
    gzip_file.write(response.get_data())
    gzip_file.close()
    response.set_data(gzip_buffer.getvalue())
    response.headers['Content-Encoding'] = 'gzip'
    response.headers['Content-Length'] = len(response.get_data())
    return response


def delete_widget_cache(repository_id, page_id=None):
    """Delete widget cache.

    @param repository_id: The repository identifier
    @param page_id: The Page identifier
    @return:
    """
    redis_connection = RedisConnection()
    cache_store = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
    if page_id:
        cache_key = ("*" + config.WEKO_GRIDLAYOUT_WIDGET_PAGE_CACHE_KEY
                     + str(repository_id) + "_" + str(page_id) + "_*")
    else:
        cache_key = ("*" + config.WEKO_GRIDLAYOUT_WIDGET_CACHE_KEY
                     + str(repository_id) + "_*")

    for key in cache_store.redis.scan_iter(cache_key):
        cache_store.redis.delete(key)


class WidgetBucket:
    """The widget file bucket."""

    def __init__(self):
        """Initial."""
        self.bucket_id = current_app.config['WEKO_GRIDLAYOUT_BUCKET_UUID']

    def initialize_widget_bucket(self):
        """Initialize the widget file bucket."""
        bucket_id = UUID(self.bucket_id)

        if Bucket.query.get(bucket_id):
            raise FilesException(
                _("Bucket with UUID {} already exists.".format(bucket_id))
            )
        else:
            try:
                storage_class = current_app.config[
                    'FILES_REST_DEFAULT_STORAGE_CLASS']
                location = Location.get_default()
                bucket = Bucket(id=bucket_id,
                                location=location,
                                default_storage_class=storage_class)
                db.session.add(bucket)
                db.session.commit()
            except Exception as ex:
                current_app.logger.error(ex)
                db.session.rollback()

    def __validate(self, file_stream, file_name, community_id="0", file_size=0):
        """Validate upload file.

        :param file_stream: file stream.
        :param file_name: file name.
        :param community_id: community identifier.
        :param file_size: file size.
        :return:
        """
        cfg = current_app.config
        file_max_size = cfg['WEKO_GRIDLAYOUT_FILE_MAX_SIZE']
        file_bucket = Bucket.query.get(self.bucket_id)

        if file_size > file_max_size:
            raise UnexpectedFileSizeError(
                _(
                    '{} is greater than the maximum value allowed ({}).'
                    .format(file_size, file_max_size)
                )
            )

        key = "{0}_{1}".format(community_id, file_name)
        file_stream.seek(0)  # Rewind the stream to the beginning
        try:
            if ObjectVersion.get(file_bucket, key):
                raise FileInstanceAlreadySetError(
                    _("The {} file is already exists.".format(file_name))
                )
            else:
                return True
        except MultipleResultsFound:
            raise FileInstanceAlreadySetError(
                _("The {} file is already exists.".format(file_name))
            )

    def save_file(self, file_stream, file_name: str, mimetype: str,
                  community_id="0"):
        """Save widget static file.

        :param file_stream: file stream.
        :param file_name: file name.
        :param mimetype: mime type.
        :param community_id: community identifier.
        :return:
        """
        rtn = {
            "status": True,
            "duplicated": False,
            "url": "",
            "msg": "OK",
            "mimetype": mimetype,
            "file_name": file_name,
        }
        file_bucket = Bucket.query.get(self.bucket_id)
        #community_id = community_id.split("@")[0]
        community_id = community_id.split("@")[0] if community_id.split("@")[0] else "0"
        key = "{0}_{1}".format(community_id, file_name)
        root_url = request.host_url
        try:
            file_stream.seek(SEEK_SET, SEEK_END)  # Seek from beginning to end
            file_size = file_stream.tell()
            if self.__validate(file_stream, file_name, community_id, file_size):
                file_stream.seek(0)  # Rewind the stream to the beginning
                ObjectVersion.create(
                    file_bucket, key, stream=file_stream, size=file_size,
                    mimetype=mimetype
                )
                db.session.commit()
                rtn["url"] = "/widget/uploaded/{}/{}".format(
                    file_name,community_id
                )
                return rtn
        except UnexpectedFileSizeError as error:
            db.session.rollback()
            current_app.logger.error(error)
            rtn['status'] = False
            rtn['msg'] = str(error.errors)
            return rtn
        except FileInstanceAlreadySetError as error:
            db.session.rollback()
            current_app.logger.error(error.errors)
            rtn['status'] = False
            rtn['duplicated'] = True
            rtn['msg'] = str(error.errors)
            rtn["url"] = "/widget/uploaded/{}/{}".format(
                file_name, community_id
            )
            return rtn
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            rtn['status'] = False
            rtn['msg'] = str(ex)
            return rtn

    def get_file(self, file_name, community_id=0):
        """Get widget static file.

        :param file_name:
        :param community_id:
        :return:
        """
        key = '{0}_{1}'.format(community_id, file_name)
        obj = ObjectVersion.get(self.bucket_id, key)
        if not obj:
            key = '{0}'.format(file_name)
            obj = ObjectVersion.get(self.bucket_id, key)
            if not obj:
                abort(404, '{} does not exists.'.format(file_name))
        #obj.key = file_name
        return obj.send_file()


def validate_upload_file(community_id: str):
    """Validate upload file.

    @param community_id:
    @return:
    """
    if 'file' not in request.files:
        return _("No file part")
    file = request.files['file']
    if file.filename == '':
        return _("No selected file")
    community_id = community_id.split("@")
    if len(community_id) > 1 and community_id[0] == '0':
        return _("Repository is required!")
    return ""
