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

"""Module of weko-items-ui utils.."""

import csv
from datetime import datetime
from io import StringIO

import numpy
from flask import current_app, session
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_records.api import RecordBase
from jsonschema import ValidationError
from sqlalchemy import MetaData, Table
from weko_deposit.api import WekoRecord
from weko_records.api import ItemTypes
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
                new_date = \
                    datetime.utcfromtimestamp(
                        item[date_key]).strftime('%Y-%m-%d')
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


def update_json_schema_by_activity_id(json, activity_id):
    """Update json schema by activity id.

    :param json: The json schema
    :param activity_id: Activity ID
    :return: json schema
    """
    if not session.get('update_json_schema') or not session[
            'update_json_schema'].get(activity_id):
        return None
    error_list = session['update_json_schema'][activity_id]

    if error_list:
        for item in error_list['required']:
            sub_item = item.split('.')
            if len(sub_item) == 1:
                json['required'] = sub_item
            else:
                if json['properties'][sub_item[0]].get('items'):
                    if not json['properties'][sub_item[0]]['items'].get(
                            'required'):
                        json['properties'][sub_item[0]]['items']['required'] \
                            = []
                    json['properties'][sub_item[0]]['items'][
                        'required'].append(sub_item[1])
                else:
                    json['properties'][sub_item[0]]['required'].append(
                        sub_item[1])
        for item in error_list['pattern']:
            sub_item = item.split('.')
            if len(sub_item) == 2:
                creators = json['properties'][sub_item[0]].get('items')
                if not creators:
                    break
                for creator in creators.get('properties'):
                    if creators['properties'][creator].get('items'):
                        givename = creators['properties'][creator]['items']
                        if givename['properties'].get(sub_item[1]):
                            if not givename.get('required'):
                                givename['required'] = []
                            givename['required'].append(sub_item[1])
    return json


def package_exports(item_type_data):
    """Export TSV Files.

        Arguments:
            pid_type     -- {string} 'doi' (default) or 'cnri'
            reg_value    -- {string} pid_value

        Returns:
            return       -- PID object if exist

    """
    """Package the .tsv files into one zip file."""
    tsv_output = StringIO()
    jsonschema_url = item_type_data.get('root_url') + \
                     item_type_data.get('jsonschema')

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
            [recid, item_type_data.get('root_url') + 'records/' + str(recid)] + item_type_data['data'].get(recid)
        )

    return tsv_output

def make_stats_tsv(item_type_id, recids):
    """Prepare TSV data for each Item Types.

        Arguments:
            pid_type     -- {string} 'doi' (default) or 'cnri'
            reg_value    -- {string} pid_value

        Returns:
            return       -- PID object if exist

    """
    item_type = ItemTypes.get_by_id(item_type_id).render

    table_row_properties = item_type['table_row_map']['schema'].get(
        'properties')

    class Records:
        recids = []
        records = {}
        attr_data = {}
        attr_output = {}

        def __init__(self, recids):
            self.recids = recids
            for recid in recids:
                record = WekoRecord.get_record_by_pid(recid)
                self.records[recid] = record
                self.attr_output[recid] = []

        def get_max_ins(self, attr):
            max = 0
            self.attr_data[attr] = {'max_size': 0
            }
            for record in self.records:
                if isinstance(self.records[record].get(attr), dict) and self.records[record].get(attr).get('attribute_value_mlt'):
                    self.attr_data[attr][record] = self.records[record][attr]['attribute_value_mlt']
                else:
                    if self.records[record].get(attr):
                        self.attr_data[attr][record] = self.records[record].get(attr)
                    else:
                        self.attr_data[attr][record] = []
                rec_size = len(self.attr_data[attr][record])
                if rec_size > max:
                    max = rec_size
            self.attr_data[attr]['max_size'] = max

            return self.attr_data[attr]['max_size']

        def get_max_items(self, item_key):
            keys = item_key.split('.')
            max_length = None
            if len(keys) == 1:
                return self.attr_data[item_key]['max_size']
            elif len(keys) == 2:
                key = keys[0].split('[')
                item_attr = key[0]
                idx = int(key[1].split(']')[0])
                sub_attr = keys[1].split('[')[0]
                max_length = 0
                for record in self.records:
                    if self.records[record].get(item_attr) and len(self.records[record][item_attr]['attribute_value_mlt']) > idx:
                        if self.records[record][item_attr]['attribute_value_mlt'][idx].get(sub_attr):
                            cur_len = len(self.records[record][item_attr]['attribute_value_mlt'][idx][sub_attr])
                            if cur_len > max_length:
                                max_length = cur_len
                return max_length
            elif len(keys) == 3:
                key = keys[0].split('[')
                key2 = keys[1].split('[')
                item_attr = key[0]
                idx = int(key[1].split(']')[0])
                sub_attr = keys[1].split('[')[0]
                idx_2 = int(key2[1].split(']')[0])
                sub_attr_2 = keys[2].split('[')[0]

                max_length = 0
                for record in self.records:
                    data = self.records[record][item_attr]['attribute_value_mlt']
                    if len(data) > idx and data[idx].get(sub_attr):
                        if len(data[idx][sub_attr]) > idx_2:
                            if data[idx][sub_attr][idx_2].get(sub_attr_2):
                                cur_len = len(data[idx][sub_attr][idx_2][sub_attr_2])
                                if cur_len > max_length:
                                    max_length = cur_len
            return max_length

        def get_subs_item(self, item_key, item_label, properties, data=None):
            """Prepare TSV data for each Item Types.

                Arguments:
                    properties     -- {string} 'doi' (default) or 'cnri'

                Returns:
                    return       -- PID object if exist

            """
            ret = []
            ret_label = []
            ret_data = []
            max_items = self.get_max_items(item_key)

            for idx in range(max_items):
                for key in properties:
                    key_data = []
                    if properties[key]['type'] == 'array':
                        if data and idx < len(data) and data[idx].get(key):
                            m_data = data[idx][key]
                        else:
                            m_data = None
                        sub, sublabel, subdata = self.get_subs_item(
                            item_key + ('[{}]').format(str(idx)) + '.' + key,
                            item_label + ('#{}').format(str(idx)) + '.' + properties[key].get('title'),
                            properties[key]['items']['properties'],
                            m_data)
                        ret.extend(sub)
                        ret_label.extend(sublabel)
                        key_data.extend(subdata)
                    elif properties[key]['type'] == 'object':
                        if data and idx < len(data) and data[idx].get(key):
                            m_data = data[idx][key]
                        else:
                            m_data = None
                        sub, sublabel, subdata = self.get_subs_item(
                            item_key + ('[{}]').format(str(idx)) + '.' + key,
                            item_label + ('#{}').format(str(idx)) + '.' + properties[key].get('title'),
                            properties[key]['properties'],
                            m_data)
                        ret.extend(sub)
                        ret_label.extend(sublabel)
                        key_data.extend(subdata)
                    else:
                        if isinstance(data, dict):
                            data = [data]
                        ret.append(item_key + ('[{}]').format(str(idx)) + '.' + key)
                        ret_label.append(item_label + ('#{}').format(str(idx)) + '.' + properties[key].get('title'))
                        if data and idx < len(data) and data[idx].get(key):
                            key_data.append(data[idx][key])
                        else:
                            key_data.append('')
                    ret_data.extend(key_data)
                    
            return ret, ret_label, ret_data

    records = Records(recids)

    ret = ['#.id', '.uri',]
    ret_label = ['#ID', 'URI',]

    # for idx in range(records.get_max_ins('path')):
    max_path = records.get_max_ins('path')
    ret.extend(['.path[{}]'.format(i) for i in range(max_path)])
    ret_label.extend(['.インデックス[{}]'.format(i) for i in range(max_path)])
    ret.append('.metadata.pubdate')
    ret_label.append('公開日')
    for recid in recids:
        records.attr_output[recid].extend(records.attr_data['path'][recid])
        records.attr_output[recid].extend(['' for i in range(max_path - len(records.attr_output[recid]))])
        records.attr_output[recid].append(records.records[recid]['pubdate']['attribute_value'])

    for item_key in item_type.get('table_row'):
        item = table_row_properties.get(item_key)
        max_path = records.get_max_ins(item_key)
        keys = []
        labels = []

        for recid in recids:
            if item.get('type') == 'array':
                key, label, data = records.get_subs_item(item_key,
                                        item.get('title'),
                                        item['items']['properties'],
                                        records.attr_data[item_key][recid])
                if not keys:
                    keys = key
                if not labels:
                    labels = label
                records.attr_output[recid].extend(data)
            elif item.get('type') == 'object':
                key, label, data = records.get_subs_item(item_key,
                                        item.get('title'),
                                        item['properties'],
                                        records.attr_data[item_key][recid])
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
        ret.extend(keys)
        ret_label.extend(labels)

    return ret, ret_label, records.attr_output

def get_author_id_by_name(names=[]):
    """Get Author_id by list name.

        Arguments:
            names     -- {string} list names

        Returns:
            weko_id       -- author id of author has search result

    """
    query_should = [
        {
            "match": {
                "authorNameInfo.fullName": name
            }
        } for name in names]

    body = {
        "query": {
            "bool": {
                "should": query_should
            }
        },
        "size": 1
    }
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        body=body
    )
    weko_id = None

    if isinstance(result, dict) and isinstance(result.get('hits'), dict) and \
            isinstance(result['hits'].get('hits'), list) and \
            len(result['hits']['hits']) > 0 and \
            isinstance(result['hits']['hits'][0], dict) and \
            isinstance(result['hits']['hits'][0].get('_source'), dict) and \
            result['hits']['hits'][0]['_source']['pk_id']:
        weko_id = result['hits']['hits'][0]['_source']['pk_id']
    return weko_id


def get_list_file_by_record_id(recid):
    """Get Author_id by list name.

        Arguments:
            recid     -- {number} record id

        Returns:
            list_file  -- list file name of record

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
            isinstance(result['hits']['hits'][0]['_source'].get('file'), dict) \
            and result['hits']['hits'][0]['_source']['file'].get('URI'):
        list_file = result['hits']['hits'][0]['_source']['file'].get('URI')

        list_file_name = [
            recid + '/' + item.get('value') for item in list_file]
    return list_file_name


def get_metadata_by_list_id(list_id=[]):
    """Get Author_id by list name.

        Arguments:
            list_id     -- {string} list Id record

        Returns:
            result       -- list_metadata of record has id in list_id

    """
    query_should = [
        {
            "match": {
                "control_number": rec_id
            }
        } for rec_id in list_id]

    body = {
        "query": {
            "bool": {
                "should": query_should
            }
        }
    }
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['INDEXER_DEFAULT_INDEX'],
        body=body
    )
    list_metadata = []

    if isinstance(result, dict) and isinstance(result.get('hits'), dict) and \
            isinstance(result['hits'].get('hits'), list):
        list_source = result['hits'].get('hits')

        list_metadata = [
            item.get('_source').get("_item_metadata")
            for item in list_source
            if (isinstance(item.get('_source'), dict) and isinstance(item.get(
                '_source').get("_item_metadata"), dict))
        ]
    return list_metadata
