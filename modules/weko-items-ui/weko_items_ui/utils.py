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

"""Module of weko-items-ui utils.."""

import csv
import json
import os
import shutil
import sys
import tempfile
import traceback
from collections import OrderedDict
from datetime import datetime
from io import StringIO

import bagit
import numpy
import redis
from elasticsearch.exceptions import NotFoundError
from flask import abort, current_app, flash, redirect, request, send_file, \
    session, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_accounts.models import Role, userrole
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_records.api import RecordBase
from invenio_search import RecordsSearch
from jsonschema import ValidationError
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import MetaData, Table
from weko_deposit.api import WekoRecord
from weko_records.api import ItemTypes
from weko_records_ui.permissions import check_file_download_permission
from weko_search_ui.query import item_search_factory
from weko_user_profiles import UserProfile
from weko_workflow.models import Action as _Action


def get_list_username():
    """Get list username.

    Query database to get all available username
    return: list of username
    """
    current_user_id = current_user.get_id()
    user_index = 1
    result = list()
    while True:
        try:
            if not int(current_user_id) == user_index:
                user_info = UserProfile.get_by_userid(user_index)
                result.append(user_info.get_username)
            user_index = user_index + 1
        except Exception as e:
            current_app.logger.error(e)
            break

    return result


def get_list_email():
    """Get list email.

    Query database to get all available email
    return: list of email
    """
    current_user_id = current_user.get_id()
    result = list()
    try:
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if not int(current_user_id) == item[0]:
                result.append(item[1])
    except Exception as e:
        result = str(e)

    return result


def get_user_info_by_username(username):
    """Get user information by username.

    Query database to get user id by using username
    Get email from database using user id
    Pack response data: user id, user name, email

    parameter:
        username: The username
    return: response pack
    """
    result = dict()
    try:
        user = UserProfile.get_by_username(username)
        user_id = user.user_id

        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if item[0] == user_id:
                result['username'] = username
                result['user_id'] = user_id
                result['email'] = item[1]
                return result
        return None
    except Exception as e:
        result['error'] = str(e)


def validate_user(username, email):
    """Validate user information.

    Get user id from database using username
    Get user id from database using email
    Compare 2 user id to validate user information
    Pack responde data:
        results: user information (username, user id, email)
        validation: username is match with email or not
        error: null if no error occurs

    param:
        username: The username
        email: The email
    return: response data
    """
    result = {
        'results': '',
        'validation': False,
        'error': ''
    }
    try:
        user = UserProfile.get_by_username(username)
        user_id = 0

        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if item[1] == email:
                user_id = item[0]
                break

        if user.user_id == user_id:
            user_info = dict()
            user_info['username'] = username
            user_info['user_id'] = user_id
            user_info['email'] = email
            result['results'] = user_info
            result['validation'] = True
        return result
    except Exception as e:
        result['error'] = str(e)

    return result


def get_user_info_by_email(email):
    """
    Get user information by email.

    Query database to get user id by using email
    Get username from database using user id
    Pack response data: user id, user name, email

    parameter:
        email: The email
    return: response
    """
    result = dict()
    try:
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()
        for item in data:
            if item[1] == email:
                user = UserProfile.get_by_userid(item[0])
                if user is None:
                    result['username'] = ""
                else:
                    result['username'] = user.get_username
                result['user_id'] = item[0]
                result['email'] = email
                return result
        return None
    except Exception as e:
        result['error'] = str(e)


def get_user_information(user_id):
    """
    Get user information user_id.

    Query database to get email by using user_id
    Get username from database using user id
    Pack response data: user id, user name, email

    parameter:
        user_id: The user_id
    return: response
    """
    result = {
        'username': '',
        'email': ''
    }
    user_info = UserProfile.get_by_userid(user_id)
    if user_info is not None:
        result['username'] = user_info.get_username

    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table_name = 'accounts_user'

    user_table = Table(table_name, metadata)
    record = db.session.query(user_table)

    data = record.all()

    for item in data:
        if item[0] == user_id:
            result['email'] = item[1]
            return result

    return result


def get_user_permission(user_id):
    """
    Get user permission user_id.

    Compare current id with id of current user
    parameter:
        user_id: The user_id
    return: true if current id is the same with id of current user.
    If not return false
    """
    current_id = current_user.get_id()
    if current_id is None:
        return False
    if str(user_id) == current_id:
        return True
    return False


def get_current_user():
    """
    Get user id of user currently login.

    parameter:
    return: current_id
    """
    current_id = current_user.get_id()
    return current_id


def get_actionid(endpoint):
    """
    Get action_id by action_endpoint.

    parameter:
    return: action_id
    """
    with db.session.no_autoflush:
        action = _Action.query.filter_by(
            action_endpoint=endpoint).one_or_none()
        if action:
            return action.id
        else:
            return None


def parse_ranking_results(results,
                          display_rank,
                          list_name='all',
                          title_key='title',
                          count_key=None,
                          pid_key=None,
                          search_key=None,
                          date_key=None):
    """Parse the raw stats results to be usable by the view."""
    ranking_list = []
    if pid_key:
        url = '../records/{0}'
        key = pid_key
    elif search_key:
        url = '../search?page=1&size=20&search_type=1&q={0}'
        key = search_key
    else:
        url = None

    if date_key == 'create_date':
        data_list = parse_ranking_new_items(results)
        results = dict()
        results['all'] = data_list
    if results and list_name in results:
        rank = 1
        count = 0
        date = ''
        for item in results[list_name]:
            t = {}
            if count_key:
                if not count == int(item[count_key]):
                    rank = len(ranking_list) + 1
                    count = int(item[count_key])
                t['rank'] = rank
                t['count'] = count
            elif date_key:
                new_date = item[date_key]
                if new_date == date:
                    t['date'] = ''
                else:
                    t['date'] = new_date
                    date = new_date
            title = item[title_key]
            if title_key == 'user_id':
                user_info = UserProfile.get_by_userid(title)
                if user_info:
                    title = user_info.username
                else:
                    title = 'None'
            t['title'] = title
            t['url'] = url.format(item[key]) if url and key in item else None
            ranking_list.append(t)
            if len(ranking_list) == display_rank:
                break
    return ranking_list


def parse_ranking_new_items(result_data):
    """Parse ranking new items.

    :param result_data: result data
    """
    data_list = list()
    if not result_data or not result_data.get('hits') \
            or not result_data.get('hits').get('hits'):
        return data_list
    for item_data in result_data.get('hits').get('hits'):
        item_created = item_data.get('_source')
        data = dict()
        data['create_date'] = item_created.get('publish_date', '')
        data['pid_value'] = item_created.get('control_number')
        meta_data = item_created.get('_item_metadata')
        item_title = ''
        if isinstance(meta_data, dict):
            item_title = meta_data.get('item_title')
        data['record_name'] = item_title
        data_list.append(data)
    return data_list


def validate_form_input_data(result: dict, item_id: str, data: dict):
    """Validate input data.

    :param result: result dictionary.
    :param item_id: item type identifier.
    :param data: form input data
    """
    item_type = ItemTypes.get_by_id(item_id)
    json_schema = item_type.schema.copy()

    data['$schema'] = json_schema.copy()
    validation_data = RecordBase(data)
    try:
        validation_data.validate()
    except ValidationError as error:
        result["is_valid"] = False
        if 'required' == error.validator:
            result['error'] = _('Please input all required item.')
        elif 'pattern' == error.validator:
            result['error'] = _('Please input the correct data.')
        else:
            result['error'] = _(error.message)


def update_json_schema_by_activity_id(json_data, activity_id):
    """Update json schema by activity id.

    :param json_data: The json schema
    :param activity_id: Activity ID
    :return: json schema
    """
    sessionstore = RedisStore(redis.StrictRedis.from_url(
        'redis://{host}:{port}/1'.format(
            host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
            port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
    if not sessionstore.redis.exists(
        'updated_json_schema_{}'.format(activity_id)) \
        and not sessionstore.get(
            'updated_json_schema_{}'.format(activity_id)):
        return None
    session_data = sessionstore.get(
        'updated_json_schema_{}'.format(activity_id))
    error_list = json.loads(session_data.decode('utf-8'))

    if error_list:
        for item in error_list['required']:
            sub_item = item.split('.')
            if len(sub_item) == 1:
                json_data['required'] = sub_item
            else:
                if json_data['properties'][sub_item[0]].get('items'):
                    if not json_data['properties'][sub_item[0]]['items'].get(
                            'required'):
                        json_data['properties'][sub_item[0]][
                            'items']['required'] = []
                    json_data['properties'][sub_item[0]]['items'][
                        'required'].append(sub_item[1])
                else:
                    if not json_data[
                            'properties'][sub_item[0]].get('required'):
                        json_data['properties'][sub_item[0]]['required'] = []
                    json_data['properties'][sub_item[0]]['required'].append(
                        sub_item[1])
        for item in error_list['pattern']:
            sub_item = item.split('.')
            if len(sub_item) == 2:
                creators = json_data['properties'][sub_item[0]].get('items')
                if not creators:
                    break
                for creator in creators.get('properties'):
                    if creators['properties'][creator].get('items'):
                        givename = creators['properties'][creator]['items']
                        if givename['properties'].get(sub_item[1]):
                            if not givename.get('required'):
                                givename['required'] = []
                            givename['required'].append(sub_item[1])
    return json_data


def package_export_file(item_type_data):
    """Export TSV Files.

    Arguments:
    pid_type     -- {string} 'doi' (default) or 'cnri'
    reg_value    -- {string} pid_value
    Returns:
    return       -- PID object if exist
    """
    tsv_output = StringIO()
    jsonschema_url = item_type_data.get('root_url') + item_type_data.get(
        'jsonschema')

    tsv_writer = csv.writer(tsv_output, delimiter='\t')
    tsv_writer.writerow(['#ItemType',
                         item_type_data.get('name'),
                         jsonschema_url])

    keys = item_type_data['keys']
    labels = item_type_data['labels']
    tsv_metadata_writer = csv.DictWriter(tsv_output,
                                         fieldnames=keys,
                                         delimiter='\t')
    tsv_metadata_label_writer = csv.DictWriter(tsv_output,
                                               fieldnames=labels,
                                               delimiter='\t')
    tsv_metadata_data_writer = csv.writer(tsv_output,
                                          delimiter='\t')
    tsv_metadata_writer.writeheader()
    tsv_metadata_label_writer.writeheader()
    for recid in item_type_data.get('recids'):
        tsv_metadata_data_writer.writerow(
            [recid, item_type_data.get('root_url') + 'records/' + str(recid)]
            + item_type_data['data'].get(recid)
        )

    return tsv_output


def make_stats_tsv(item_type_id, recids):
    """Prepare TSV data for each Item Types.

    Arguments:
        item_type_id    -- ItemType ID
        recids          -- List records ID
    Returns:
        ret             -- Key properties
        ret_label       -- Label properties
        records.attr_output -- Record data

    """
    item_type = ItemTypes.get_by_id(item_type_id).render
    table_row_properties = item_type['table_row_map']['schema'].get(
        'properties')

    class RecordsManager:
        """Management data for exporting records"""
        first_recid = 0
        cur_recid = 0
        filepath_idx = 1
        recids = []
        records = {}
        attr_data = {}
        attr_output = {}

        def __init__(self, record_ids):
            """Class initialization."""
            self.recids = record_ids
            self.first_recid = record_ids[0]
            for record_id in record_ids:
                record = WekoRecord.get_record_by_pid(record_id)
                self.records[record_id] = record
                self.attr_output[record_id] = []

        def get_max_ins(self, attr):
            """Get max data each main property in all exporting records."""
            largest_size = 1
            self.attr_data[attr] = {'max_size': 0}
            for record in self.records:
                if isinstance(self.records[record].get(attr), dict) \
                    and self.records[record].get(attr).get(
                        'attribute_value_mlt'):
                    self.attr_data[attr][record] = self.records[record][attr][
                        'attribute_value_mlt']
                else:
                    if self.records[record].get(attr):
                        self.attr_data[attr][record] = \
                            self.records[record].get(attr)
                    else:
                        self.attr_data[attr][record] = []
                rec_size = len(self.attr_data[attr][record])
                if rec_size > largest_size:
                    largest_size = rec_size
            self.attr_data[attr]['max_size'] = largest_size

            return self.attr_data[attr]['max_size']

        def get_max_items(self, item_attrs):
            """Get max data each sub property in all exporting records."""
            list_attr = item_attrs.split('.')
            max_length = None
            if len(list_attr) == 1:
                return self.attr_data[item_attrs]['max_size']
            elif len(list_attr) == 2:
                max_length = 1
                first_attr = list_attr[0].split('[')
                item_attr = first_attr[0]
                idx = int(first_attr[1].split(']')[0])
                sub_attr = list_attr[1].split('[')[0]
                for record in self.records:
                    if self.records[record].get(item_attr) \
                        and len(self.records[record][item_attr][
                            'attribute_value_mlt']) > idx \
                        and self.records[record][item_attr][
                            'attribute_value_mlt'][idx].get(sub_attr):
                        cur_len = len(self.records[record][item_attr][
                            'attribute_value_mlt'][idx][sub_attr])
                        if cur_len > max_length:
                            max_length = cur_len
            elif len(list_attr) == 3:
                max_length = 1
                first_attr = list_attr[0].split('[')
                key2 = list_attr[1].split('[')
                item_attr = first_attr[0]
                idx = int(first_attr[1].split(']')[0])
                sub_attr = list_attr[1].split('[')[0]
                idx_2 = int(key2[1].split(']')[0])
                sub_attr_2 = list_attr[2].split('[')[0]
                for record in self.records:
                    if self.records[record].get(item_attr):
                        attr_val = self.records[record][item_attr][
                            'attribute_value_mlt']
                        if len(attr_val) > idx and attr_val[idx].get(sub_attr) \
                            and len(attr_val[idx][sub_attr]) > idx_2 \
                                and attr_val[idx][sub_attr][idx_2].get(sub_attr_2):
                            cur_len = len(attr_val[idx][sub_attr][idx_2][
                                sub_attr_2])
                            if cur_len > max_length:
                                max_length = cur_len
            return max_length

        def get_subs_item(self,
                          item_key,
                          item_label,
                          properties,
                          data=None,
                          is_object=False):
            """Building key, label and data from key properties.

            Arguments:
                item_key    -- Key properties
                item_label  -- Label properties
                properties  -- Data properties
                data        -- Record data
                is_object   -- Is objecting property?
            Returns:
                o_ret       -- Key properties
                o_ret_label -- Label properties
                ret_data    -- Record data

            """
            o_ret = []
            o_ret_label = []
            ret_data = []
            max_items = self.get_max_items(item_key)
            max_items = 1 if is_object else max_items
            for idx in range(max_items):
                key_list = []
                key_label = []
                key_data = []
                for key in sorted(properties):
                    if properties[key]['type'] == 'array':
                        if data and idx < len(data) and data[idx].get(key):
                            m_data = data[idx][key]
                        else:
                            m_data = None
                        sub, sublabel, subdata = self.get_subs_item(
                            '{}[{}].{}'.format(item_key, str(idx), key),
                            '{}#{}.{}'.format(item_label, str(idx + 1),
                                              properties[key].get('title')),
                            properties[key]['items']['properties'],
                            m_data)
                        if is_object:
                            _sub_ = []
                            for item in sub:
                                if 'item_' in item:
                                    _sub_.append(item.split('.')[0].replace(
                                        '[0]', '') + '.' + '.'.join(
                                        item.split('.')[1:]))
                                else:
                                    _sub_.append(item)
                            sub = _sub_
                        key_list.extend(sub)
                        key_label.extend(sublabel)
                        key_data.extend(subdata)
                    else:
                        if isinstance(data, dict):
                            data = [data]
                        if is_object:
                            key_list.append('{}.{}'.format(
                                item_key,
                                key))
                            key_label.append('{}.{}'.format(
                                item_label,
                                properties[key].get('title')))
                        else:
                            key_list.append('{}[{}].{}'.format(
                                item_key,
                                str(idx),
                                key))
                            key_label.append('{}#{}.{}'.format(
                                item_label,
                                str(idx + 1),
                                properties[key].get('title')))
                        if data and idx < len(data) and data[idx].get(key):
                            key_data.append(data[idx][key])
                        else:
                            key_data.append('')

                key_list_len = len(key_list)
                for key_index in range(key_list_len):
                    if 'filename' in key_list[key_index] \
                        or 'thumbnail_label' in key_list[key_index] \
                            and len(item_key.split('.')) == 2:
                        key_list.insert(0, '.file_path#'
                                        + str(self.filepath_idx + idx))
                        key_label.insert(0, '.ファイルパス#'
                                         + str(self.filepath_idx + idx))
                        if key_data[key_index]:
                            key_data.insert(0, 'recid_{}/{}'.format(str(
                                self.cur_recid), key_data[key_index]))
                        else:
                            key_data.insert(0, '')
                        if idx == max_items - 1 \
                                and self.first_recid == self.cur_recid:
                            self.filepath_idx += max_items
                        break

                o_ret.extend(key_list)
                o_ret_label.extend(key_label)
                ret_data.extend(key_data)

            return o_ret, o_ret_label, ret_data

    records = RecordsManager(recids)

    ret = ['#.id', '.uri']
    ret_label = ['#ID', 'URI']

    max_path = records.get_max_ins('path')
    ret.extend(['.metadata.path[{}]'.format(i) for i in range(max_path)])
    ret_label.extend(['.IndexID#{}'.format(i + 1) for i in range(max_path)])
    ret.append('.metadata.pubdate')
    ret_label.append('公開日')

    for recid in recids:
        records.attr_output[recid].extend(records.attr_data['path'][recid])
        records.attr_output[recid].extend([''] * (max_path - len(
            records.attr_output[recid])))
        records.attr_output[recid].append(records.records[recid][
            'pubdate']['attribute_value'])

    for item_key in item_type.get('table_row'):
        item = table_row_properties.get(item_key)
        records.get_max_ins(item_key)
        keys = []
        labels = []
        for recid in recids:
            records.cur_recid = recid
            if item.get('type') == 'array':
                key, label, data = records.get_subs_item(
                    item_key,
                    item.get('title'),
                    item['items']['properties'],
                    records.attr_data[item_key][recid]
                )
                if not keys:
                    keys = key
                if not labels:
                    labels = label
                records.attr_output[recid].extend(data)
            elif item.get('type') == 'object':
                key, label, data = records.get_subs_item(
                    item_key,
                    item.get('title'),
                    item['properties'],
                    records.attr_data[item_key][recid],
                    True
                )
                if not keys:
                    keys = key
                if not labels:
                    labels = label
                records.attr_output[recid].extend(data)
            else:
                if not keys:
                    keys = [item_key]
                if not labels:
                    labels = [item.get('title')]
                data = records.attr_data[item_key].get(recid) or ['']
                records.attr_output[recid].extend(data)

        new_keys = []
        for key in keys:
            if 'file_path' not in key:
                key = '.metadata.{}'.format(key)
            new_keys.append(key)
        ret.extend(new_keys)
        ret_label.extend(labels)

    return ret, ret_label, records.attr_output


def get_list_file_by_record_id(recid):
    """Get file buckets by record id.

    Arguments:
        recid     -- {number} record id.
    Returns:
        list_file  -- list file name of record.

    """
    body = {
        "query": {
            "function_score": {
                "query": {
                    "match": {
                        "_id": recid
                    }
                }
            }
        },
        "_source": ["file"],
        "size": 1
    }
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['INDEXER_DEFAULT_INDEX'],
        body=body
    )
    list_file_name = []

    if isinstance(result, dict) and isinstance(result.get('hits'), dict) and \
            isinstance(result['hits'].get('hits'), list) and \
            len(result['hits']['hits']) > 0 and \
            isinstance(result['hits']['hits'][0], dict) and \
            isinstance(result['hits']['hits'][0].get('_source'), dict) and \
            isinstance(result['hits']['hits'][0]['_source'].get('file'), dict)\
            and result['hits']['hits'][0]['_source']['file'].get('URI'):
        list_file = result['hits']['hits'][0]['_source']['file'].get('URI')

        list_file_name = [
            recid + '/' + item.get('value') for item in list_file]
    return list_file_name


def export_items(post_data):
    """Gather all the item data and export and return as a JSON or BIBTEX.

    :return: JSON, BIBTEX
    """
    include_contents = True if \
        post_data['export_file_contents_radio'] == 'True' else False
    export_format = post_data['export_format_radio']
    record_ids = json.loads(post_data['record_ids'])
    record_metadata = json.loads(post_data['record_metadata'])
    if len(record_ids) > _get_max_export_items():
        return abort(400)
    elif len(record_ids) == 0:
        flash(_('Please select Items to export.'), 'error')
        return redirect(url_for('weko_items_ui.export'))

    result = {'items': []}
    temp_path = tempfile.TemporaryDirectory()
    item_types_data = {}

    try:
        # Set export folder
        export_path = temp_path.name + '/' + \
            datetime.utcnow().strftime("%Y%m%d%H%M%S")
        # Double check for limits
        for record_id in record_ids:
            record_path = export_path + '/recid_' + str(record_id)
            os.makedirs(record_path, exist_ok=True)
            exported_item = _export_item(
                record_id,
                export_format,
                include_contents,
                record_path,
                record_metadata.get(str(record_id))
            )

            result['items'].append(exported_item)

            item_type_id = exported_item.get('item_type_id')
            item_type = ItemTypes.get_by_id(item_type_id)
            if not item_types_data.get(item_type_id):
                item_types_data[item_type_id] = {}

                item_types_data[item_type_id] = {
                    'item_type_id': item_type_id,
                    'name': '{}({})'.format(
                        item_type.item_type_name.name,
                        item_type_id),
                    'root_url': request.url_root,
                    'jsonschema': 'items/jsonschema/' + item_type_id,
                    'keys': [],
                    'labels': [],
                    'recids': [],
                    'data': {},
                }
            item_types_data[item_type_id]['recids'].append(record_id)

        # Create export info file
        for item_type_id in item_types_data:
            keys, labels, records = make_stats_tsv(
                item_type_id,
                item_types_data[item_type_id]['recids'])
            item_types_data[item_type_id]['recids'].sort()
            item_types_data[item_type_id]['keys'] = keys
            item_types_data[item_type_id]['labels'] = labels
            item_types_data[item_type_id]['data'] = records
            item_type_data = item_types_data[item_type_id]

            with open('{}/{}.tsv'.format(export_path, item_type_data.get(
                    'name')), 'w') as file:
                tsvs_output = package_export_file(item_type_data)
                file.write(tsvs_output.getvalue())

        # Create bag
        bagit.make_bag(export_path)
        # Create download file
        shutil.make_archive(export_path, 'zip', export_path)
    except Exception:
        current_app.logger.error('-' * 60)
        traceback.print_exc(file=sys.stdout)
        current_app.logger.error('-' * 60)
        flash(_('Error occurred during item export.'), 'error')
        return redirect(url_for('weko_items_ui.export'))
    return send_file(export_path + '.zip')


def _get_max_export_items():
    """Get max amount of items to export."""
    max_table = current_app.config['WEKO_ITEMS_UI_MAX_EXPORT_NUM_PER_ROLE']
    non_user_max = max_table[current_app.config[
        'WEKO_PERMISSION_ROLE_GENERAL']]
    current_user_id = current_user.get_id()

    if not current_user_id:  # Non-logged in users
        return non_user_max

    try:
        roles = db.session.query(Role).join(userrole).filter_by(
            user_id=current_user_id).all()
    except Exception:
        return current_app.config['WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM']

    current_max = non_user_max
    for role in roles:
        if role in max_table and max_table[role] > current_max:
            current_max = max_table[role]
    return current_max


def _export_item(record_id,
                 export_format,
                 include_contents,
                 tmp_path=None,
                 records_data=None):
    """Exports files for record according to view permissions."""
    exported_item = {}
    record = WekoRecord.get_record_by_pid(record_id)

    if record:
        exported_item['record_id'] = record.id
        exported_item['name'] = 'recid_{}'.format(record_id)
        exported_item['files'] = []
        exported_item['path'] = 'recid_' + str(record_id)
        exported_item['item_type_id'] = record.get('item_type_id')
        if not records_data:
            records_data = record

        # Create metadata file.
        with open('{}/{}_metadata.json'.format(tmp_path,
                                               exported_item['name']),
                  'w',
                  encoding='utf8') as output_file:
            json.dump(records_data, output_file, indent=2,
                      sort_keys=True, ensure_ascii=False)
        # First get all of the files, checking for permissions while doing so
        if include_contents:
            # Get files
            for file in record.files:  # TODO: Temporary processing
                if check_file_download_permission(record, file.info()):
                    exported_item['files'].append(file.info())
                    # TODO: Then convert the item into the desired format
                    if file:
                        shutil.copy2(file.obj.file.uri,
                                     tmp_path + '/' + file.obj.basename)

    return exported_item


def get_new_items_by_date(start_date: str, end_date: str) -> dict:
    """Get ranking new item by date.

    :param start_date:
    :param end_date:
    :return:
    """
    record_search = RecordsSearch(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
    result = dict()

    try:
        search_instance, _qs_kwargs = item_search_factory(None,
                                                          record_search,
                                                          start_date,
                                                          end_date)
        search_result = search_instance.execute()
        result = search_result.to_dict()
    except NotFoundError as e:
        current_app.logger.debug("Indexes do not exist yet: ", str(e))

    return result


def update_schema_remove_hidden_item(schema, render, items_name):
    """Update schema: remove hidden items.

    :param schema: json schema
    :param render: json render
    :param items_name: list items which has hidden flg
    :return: The json object.
    """
    for item in items_name:
        hidden_flg = False
        key = schema[item]['key']
        if render['meta_list'].get(key):
            hidden_flg = render['meta_list'][key]['option']['hidden']
        if render['meta_system'].get(key):
            hidden_flg = render['meta_system'][key]['option']['hidden']
        if hidden_flg:
            schema[item]['condition'] = 1

    return schema


def to_files_js(record):
    """List files in a deposit."""
    res = []
    files = record.files
    if files is not None:
        for f in files:
            res.append({
                'displaytype': f.get('displaytype', ''),
                'filename': f.get('filename', ''),
                'mimetype': f.mimetype,
                'licensetype': f.get('licensetype', ''),
                'key': f.key,
                'version_id': str(f.version_id),
                'checksum': f.file.checksum,
                'size': f.file.size,
                'completed': True,
                'progress': 100,
                'links': {
                    'self': (
                        current_app.config['DEPOSIT_FILES_API']
                        + u'/{bucket}/{key}?versionId={version_id}'.format(
                            bucket=f.bucket_id,
                            key=f.key,
                            version_id=f.version_id,
                        )),
                },
                'is_show': f.is_show,
                'is_thumbnail': f.is_thumbnail
            })

    return res
