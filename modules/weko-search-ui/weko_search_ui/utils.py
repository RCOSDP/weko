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

"""Weko Search-UI admin."""

import json
import os
import sys

from functools import reduce
from operator import getitem
from collections import defaultdict
from flask import abort, current_app, request, jsonify
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer
from invenio_records.api import Record
from invenio_search import RecordsSearch
from weko_deposit.api import WekoIndexer
from weko_indextree_journal.api import Journals
from weko_deposit.api import WekoRecord
from .config import WEKO_REPO_USER, WEKO_SYS_USER
from .query import feedback_email_search_factory, item_path_search_factory


def get_tree_items(index_tree_id):
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance, qs_kwargs = item_path_search_factory(
        None, records_search, index_id=index_tree_id)
    search_result = search_instance.execute()
    rd = search_result.to_dict()
    return rd.get('hits').get('hits')


def delete_records(index_tree_id):
    """Bulk delete records."""
    record_indexer = RecordIndexer()
    hits = get_tree_items(index_tree_id)
    for hit in hits:
        recid = hit.get('_id')
        record = Record.get_record(recid)
        if record is not None and record['path'] is not None:
            paths = record['path']
            if len(paths) > 0:
                # Remove the element which matches the index_tree_id
                removed_path = None
                for path in paths:
                    if path.endswith(str(index_tree_id)):
                        removed_path = path
                        paths.remove(path)
                        break

                # Do update the path on record
                record.update({'path': paths})
                record.commit()
                db.session.commit()

                # Indexing
                indexer = WekoIndexer()
                indexer.update_path(record, update_revision=False)

                if len(paths) == 0 and removed_path is not None:
                    from weko_deposit.api import WekoDeposit
                    WekoDeposit.delete_by_index_tree_id(removed_path)
                    Record.get_record(recid).delete()  # flag as deleted
                    db.session.commit()  # terminate the transaction


def get_journal_info(index_id=0):
    """Get journal information.

    :return: The object.
    """
    try:
        if index_id == 0:
            return None
        schema_file = os.path.join(
            os.path.abspath(__file__ + "/../../../"),
            'weko-indextree-journal/weko_indextree_journal',
            current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE'])
        schema_data = json.load(open(schema_file))

        cur_lang = current_i18n.language
        journal = Journals.get_journal_by_index_id(index_id)
        if len(journal) <= 0 or journal.get('is_output') is False:
            return None

        result = {}
        for value in schema_data:
            title = value.get('title_i18n')
            if title is not None:
                data = journal.get(value['key'])
                if data is not None and len(str(data)) > 0:
                    data_map = value.get('titleMap')
                    if data_map is not None:
                        res = [x['name']
                               for x in data_map if x['value'] == data]
                        data = res[0]
                    val = title.get(cur_lang) + '{0}{1}'.format(': ', data)
                    result.update({value['key']: val})
        open_search_uri = journal.get('title_url')
        result.update({'openSearchUrl': open_search_uri})

    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        abort(500)
    return result


def get_feedback_mail_list():
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance = feedback_email_search_factory(None, records_search)
    search_result = search_instance.execute()
    rd = search_result.to_dict()
    return rd.get('aggregations').get('feedback_mail_list')\
        .get('email_list').get('buckets')


def parse_feedback_mail_data(data):
    """Parse data."""
    result = {}
    if data is not None and isinstance(data, list):
        for author in data:
            if author.get('doc_count'):
                email = author.get('key')
                hits = author.get('top_tag_hits').get('hits').get('hits')
                result[email] = {
                    'author_id': '',
                    'item': []
                }
                for index in hits:
                    if not result[email]['author_id']:
                        result[email]['author_id'] = index.get(
                            '_source').get('author_id')
                    result[email]['item'].append(index.get('_id'))
    return result


def check_permission():
    """Check user login is repo_user or sys_user."""
    from flask_security import current_user
    is_permission_user = False
    for role in list(current_user.roles or []):
        if role == WEKO_SYS_USER or role == WEKO_REPO_USER:
            is_permission_user = True

    return is_permission_user


def get_content_workflow(item):
    """Get content workflow.

    Arguments:
        item {Object PostgreSql} -- list work flow

    Returns:
        result {dictionary} -- content of work flow

    """
    result = dict()
    result['flows_name'] = item.flows_name
    result['id'] = item.id
    result['itemtype_id'] = item.itemtype_id
    result['flow_id'] = item.flow_id
    result['flow_name'] = item.flow_define.flow_name
    result['item_type_name'] = item.itemtype.item_type_name.name
    return result


def get_base64_string(data):
    result = data.split(",")
    return result[-1]


def is_tsv(name):
    term = name.split('.')
    return term[-1] == "tsv"


def set_nested_item(data_dict, map_list, val):
    """Set item in nested dictionary"""
    reduce(getitem, map_list[:-1], data_dict)[map_list[-1]] = val

    return data_dict


def convert_nested_item_to_list(data_dict, map_list):
    """Set item in nested dictionary"""
    a = reduce(getitem, map_list[:-1], data_dict)[map_list[-1]]
    a = list(a.values())
    reduce(getitem, map_list[:-1], data_dict)[map_list[-1]] = a

    return data_dict


def define_default_dict():
    return defaultdict(define_default_dict)


def defaultify(d):
    if not isinstance(d, dict):
        return d
    return defaultdict(define_default_dict, {k: defaultify(v) for k, v in d.items()})


def handle_generate_key_path(key):
    key = key.replace('#.', '.').replace('[', '.').replace(']', '').replace('#', '.')
    key_path = key.split(".")
    if len(key_path) > 0 and not key_path[0]:
        del key_path[0]
    # if len key_pathnot key_path[-1]:
    #     del key_path[-1]

    return key_path


def parse_to_json_form(data):
    result = defaultify({})
    import json

    def convert_data(pro, path=[]):
        term_path = path
        if isinstance(pro, dict):
            list_pro = list(pro.keys())
            for pro_name in list_pro:
                term = list(term_path)
                term.append(pro_name)
                convert_data(pro[pro_name], term)
            if list_pro[0].isnumeric():
                convert_nested_item_to_list(result, term_path)
        else:
            return
    for key, name, value in data:
        key_path = handle_generate_key_path(key)
        name_path = handle_generate_key_path(name)
        if value:
            a = handle_check_identifier(name_path)
            if not a:
                set_nested_item(result, key_path, value)
            else:
                set_nested_item(result, key_path, value)
                a += ' key'
                set_nested_item(result, [a], key_path[1])

    convert_data(result)
    result = json.loads(json.dumps(result))
    return result


import io
import bagit
import tempfile
import traceback
import shutil
from datetime import datetime
import base64


def import_items(file_content: str) -> list:
    """Validation importing zip file.

    Arguments:
        file_content     -- {string} 'doi' (default) or 'cnri'
    Returns:
        return       -- PID object if exist
    """
    file_content_decoded = base64.b64decode(file_content)
    temp_path = tempfile.TemporaryDirectory()
    try:
        # Create temp dir for import data
        import_path = temp_path.name + '/' + \
            datetime.utcnow().strftime(r'%Y%m%d%H%M%S')
        data_path = temp_path.name + '/import'

        with open(import_path + '.zip', 'wb+') as f:
            f.write(file_content_decoded)
        shutil.unpack_archive(import_path + '.zip', extract_dir=data_path)
        bag = bagit.Bag(data_path)

        # Valid importing zip file format
        if bag.is_valid():
            data_path += '/data'
            list_record = []
            for tsv_entry in os.listdir(data_path):
                if tsv_entry.endswith('.tsv'):
                    list_record.extend(
                        unpackage_import_file(data_path, tsv_entry))
            list_record = handle_check_exist_record(list_record)
            return list_record
        else:
            # TODO: Handle import file isn't zip file
            pass
    except Exception:
        current_app.logger.error('-' * 60)
        traceback.print_exc(file=sys.stdout)
        current_app.logger.error('-' * 60)
    finally:
        temp_path.cleanup()


def unpackage_import_file(data_path: str, tsv_file_name: str) -> list:
    """Getting record data from TSV file.

    Arguments:
        file_content     -- {string} 'doi' (default) or 'cnri'
    Returns:
        return       -- PID object if exist
    """
    tsv_file_path = '{}/{}'.format(data_path, tsv_file_name)
    data = read_stats_tsv(tsv_file_path)
    list_record = handle_validate_item_import(data.get('tsv_data'), data.get(
        'item_type_schema', {}
    ))
    return list_record


def read_stats_tsv(tsv_file_path: str) -> dict:
    """Read importing TSV file.

    Arguments:
        file_content     -- {string} 'doi' (default) or 'cnri'
    Returns:
        return       -- PID object if exist
    """
    from .config import WEKO_READ_FILE_ERROR_CODE
    result = {
        'error': False,
        'error_code': 0,
        'tsv_data': [],
        'item_type_schema': {}
    }
    tsv_data = []
    item_path = []
    item_path_name = []
    check_item_type = {}
    with open(tsv_file_path, 'r') as tsvfile:
        for num, row in enumerate(tsvfile, start=1):
            data_row = row.rstrip('\n').split('\t')
            if num == 1:
                if data_row[-1] and data_row[-1].split('/')[-1]:
                    item_type_id = data_row[-1].split('/')[-1]
                    check_item_type = get_item_type(
                        int(item_type_id)
                    )
                    if not check_item_type:
                        result['item_type_schema'] = {}
                    else:
                        result['item_type_schema'] = check_item_type['schema']

            elif num == 2:
                item_path = data_row
            elif num == 3:
                item_path_name = data_row
            else:
                data_parse_metadata = parse_to_json_form(zip(
                    item_path,
                    item_path_name,
                    data_row)
                )

                json_data_parse = parse_to_json_form(zip(
                    item_path_name,
                    item_path,
                    data_row)
                )
                tsv_item = dict(**json_data_parse, **data_parse_metadata, **{
                    'item_type_name': check_item_type['name']
                    if check_item_type else '',
                    'item_type_id': check_item_type['item_type_id']
                    if check_item_type else ''
                })
                tsv_data.append(tsv_item)
    result['tsv_data'] = tsv_data
    return result


def handle_validate_item_import(list_recond, schema) -> list:
    """Validate item import.
    Arguments:
        list_recond     -- {list} list recond import
        schema     -- {dict} item_type schema
    Returns:
        return       -- list_item_error
    """
    result = []

    from jsonschema import validate, Draft4Validator
    from jsonschema.exceptions import ValidationError

    v2 = Draft4Validator(schema) if schema else None
    for record in list_recond:
        if record.get('metadata'):
            errors = []
            if v2:
                a = v2.iter_errors(record.get('metadata'))
                errors = [error.message for error in a]
            else:
                errors = ['ItemType is not exist']
        item_error = dict(**record, **{
            'errors': errors if len(errors) else None
        })
        result.append(item_error)
    return result


def get_item_type(item_type_id=0) -> dict:
    """Get item type.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """

    from weko_records.api import ItemTypes
    try:
        result = None
        cur_lang = current_i18n.language

        if item_type_id > 0:
            itemType = ItemTypes.get_by_id(item_type_id)
            result = {
                'schema': itemType.schema,
                'name': itemType.item_type_name.name,
                'item_type_id': item_type_id
            } if itemType else None

        if result is None:
            return {}

        return result

    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


def handle_check_exist_record(list_recond) -> list:
    """Check record is exist in system.
    Arguments:
        list_recond     -- {list} list recond import
    Returns:
        return       -- list record has property status
    """

    result = []
    url_root = request.url_root
    for item in list_recond:
        if not item.get('errors'):
            item = dict(**item, **{
                'status': 'new'
            })
            if url_root in item.get('uri', ''):
                try:
                    item_exist = WekoRecord.get_record_by_pid(item.get('id'))
                    if item_exist:
                        if item_exist.pid.is_deleted():
                            continue
                        else:
                            item['status'] = 'update'
                            compare_identifier(item, item_exist)
                    else:
                        item['status'] = 'new'
                        check_identifier_new(item)
                except BaseException:
                    current_app.logger.error('Unexpected error: ',
                                             sys.exc_info()[0])
        if item.get('status') == 'new':
            handle_remove_identifier(item)
        result.append(item)
    return result


def handle_check_identifier(name) -> str:
    """Check data is Identifier of Identifier Registration.
        Arguments:
            name_path     -- {list} list name path
        Returns:
            return       -- Name of key if is Identifier
        """
    url_root = request.url_root
    result = ''
    if 'Identifier' in name or 'Identifier Registration' in name:
        result = name[0]
    return result


def handle_remove_identifier(item) -> dict:
    """Remove Identifier of Identifier Registration.
        Arguments:
            item         -- Item
        Returns:
            return       -- Item had been removed property
        """
    if item and item.get('Identifier key'):
        del item.metadata[item.get('Identifier key')]
        del item['Identifier key']
        del item['Identifier']
    if item and item.get('Identifier Registration key'):
        del item.metadata[item.get('Identifier Registration key')]
        del item['Identifier Registration key']
        del item['Identifier Registration']
    return item


def compare_identifier(item, item_exist):
    """Compare data is Identifier.
        Arguments:
            item           -- {dict} item import
            item_exist     -- {dict} item in system
        Returns:
            return       -- Name of key if is Identifier
    """
    if item.get('Identifier key'):
        item_iden = item.get('metadata', '').get(item.get('Identifier key'))
        item_exist_iden = item_exist.get(item.get(
            'Identifier key')).get('attribute_value_mlt')
        if len(item_iden) == len(item_exist_iden):
            list_dif = difference(item_iden, item_exist_iden)
            if list_dif:
                item['errors'] = ['Errors in Identifier']
                item['status'] = ''
        elif len(item_iden) > len(item_exist_iden):
            list_dif = difference(item_iden, item_exist_iden)
            for i in list_dif + item_iden:
                if i not in item_exist_iden:
                    try:
                        pids = [
                            k for k in i.values() if k != 'DOI' or k != 'HDL']
                        for pid in pids:
                            item_check = \
                                WekoRecord.get_record_by_pid(pid)
                            if item_check and item_check.id != item.id:
                                item['errors'] = ['Errors in Identifier']
                                item['status'] = ''
                    except BaseException:
                        current_app.logger.error('Unexpected error: ',
                                                 sys.exc_info()[0])
            if item['errors']:
                item['metadata'][item.get('Identifier key')] = list(set([
                    it for it in list_dif + item_iden
                ]))
        elif len(item_iden) < len(item_exist_iden):
            item['metadata'][item.get('Identifier key')] = item_exist_iden
    return item


def make_stats_tsv(raw_stats):
    """Make TSV report file for stats."""
    import csv
    from io import StringIO
    tsv_output = StringIO()

    writer = csv.writer(tsv_output, delimiter='\t',
                        lineterminator="\n")
    cols = []
    list_name = ['No', 'Item type', 'Item id', 'Title', 'Check result']
    writer.writerow(list_name)
    for item in raw_stats:
        term = []
        for name in list_name:
            term.append(item.get(name))
        writer.writerow(term)

    return tsv_output


def difference(list1, list2):
    """Make TSV report file for stats."""
    list_dif = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return list_dif


def check_identifier_new(item):
    """Check data Identifier.
        Arguments:
            item           -- {dict} item import
            item_exist     -- {dict} item in system
        Returns:
            return       -- Name of key if is Identifier
    """
    if item.get('Identifier key'):
        item_iden = item.get('metadata', '').get(item.get('Identifier key'))
        for it in item_iden:
            try:
                pids = [
                    k for k in it.values() if k != 'DOI' or k != 'HDL']
                for pid in pids:
                    item_check = \
                        WekoRecord.get_record_by_pid(pid)
                    if item_check and item_check.id != item.id:
                        item['errors'] = ['Errors in Identifier']
                        item['status'] = ''

            except BaseException:
                current_app.logger.error('Unexpected error: ',
                                         sys.exc_info()[0])
    return item
