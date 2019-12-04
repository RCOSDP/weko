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

import base64
import io
import json
import os
import shutil
import sys
import tempfile
import traceback
from collections import defaultdict
from datetime import datetime
from functools import reduce
from operator import getitem

import bagit
from flask import abort, current_app, jsonify, request
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer
from invenio_records.api import Record
from invenio_search import RecordsSearch
from weko_deposit.api import WekoIndexer, WekoRecord
from weko_indextree_journal.api import Journals

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

    :argument
        index_id -- {int} index id
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

    :argument
        item {Object PostgreSql} -- list work flow

    :return
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


def get_base64_string(data: str) -> str:
    """Get base64 string.

    :argument
        data        -- {string} string has base64 string.
    :return
       return       -- {string} base64 string.

    """
    result = data.split(",")
    return result[-1]


def is_tsv(name):
    """Check file is tsv file.

    :argument
        name        -- {string} file name.
    :return
       return       -- {bool} True if its tsv file.

    """
    term = name.split('.')
    return term[-1] == "tsv"


def set_nested_item(data_dict, map_list, val):
    """Set item in nested dictionary."""
    reduce(getitem, map_list[:-1], data_dict)[map_list[-1]] = val

    return data_dict


def convert_nested_item_to_list(data_dict, map_list):
    """Set item in nested dictionary."""
    a = reduce(getitem, map_list[:-1], data_dict)[map_list[-1]]
    a = list(a.values())
    reduce(getitem, map_list[:-1], data_dict)[map_list[-1]] = a

    return data_dict


def define_default_dict():
    """Define nested dict.

    :return
       return       -- {dict}.
    """
    return defaultdict(define_default_dict)


def defaultify(d: dict) -> dict:
    """Create default dict.

    :argument
        d            -- {dict} current dict.
    :return
        return       -- {dict} default dict.

    """
    if not isinstance(d, dict):
        return d
    return defaultdict(
        define_default_dict,
        {k: defaultify(v) for k, v in d.items()}
    )


def handle_generate_key_path(key) -> list:
    """Handle generate key path.

    :argument
        key     -- {string} string key.
    :return
        return       -- {list} list key path after convert.

    """
    key = key.replace(
        '#.',
        '.'
    ).replace(
        '[',
        '.'
    ).replace(
        ']',
        ''
    ).replace(
        '#',
        '.'
    )
    key_path = key.split(".")
    if len(key_path) > 0 and not key_path[0]:
        del key_path[0]

    return key_path


def parse_to_json_form(data: list) -> dict:
    """Parse set argument to json object.

    :argument
        key     -- {list zip} argument if json object.
    :return
        return       -- {dict} dict after convert argument.

    """
    import json
    result = defaultify({})

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


def import_items(file_content: str):
    """Validation importing zip file.

    :argument
        file_content     -- {string} 'doi' (default) or 'cnri'.
    :return
        return       -- PID object if exist.

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
            return {
                'list_record': list_record,
                'data_path': data_path
            }
        else:
            return {
                'error': 'Zip file is not follow Bagit format.'
            }
    except Exception:
        current_app.logger.error('-' * 60)
        traceback.print_exc(file=sys.stdout)
        current_app.logger.error('-' * 60)
    finally:
        temp_path.cleanup()


def unpackage_import_file(data_path: str, tsv_file_name: str) -> list:
    """Getting record data from TSV file.

    :argument
        file_content     -- {string} 'doi' (default) or 'cnri'.
    :return
        return       -- PID object if exist.

    """
    tsv_file_path = '{}/{}'.format(data_path, tsv_file_name)
    data = read_stats_tsv(tsv_file_path)
    list_record = handle_validate_item_import(data.get('tsv_data'), data.get(
        'item_type_schema', {}
    ))
    return list_record


def read_stats_tsv(tsv_file_path: str) -> dict:
    """Read importing TSV file.

    :argument
        file_content     -- {string} 'doi' (default) or 'cnri'.
    :return
        return       -- PID object if exist.

    """
    result = {
        'error': False,
        'error_code': 0,
        'tsv_data': [],
        'item_type_schema': {}
    }
    tsv_data = []
    item_path = []
    item_path_name = []
    check_item_type = {},
    schema = ''
    with open(tsv_file_path, 'r') as tsvfile:
        for num, row in enumerate(tsvfile, start=1):
            data_row = row.rstrip('\n').split('\t')
            if num == 1:
                if data_row[-1] and data_row[-1].split('/')[-1]:
                    item_type_id = data_row[-1].split('/')[-1]
                    check_item_type = get_item_type(int(item_type_id))
                    schema = data_row[-1]
                    if not check_item_type:
                        result['item_type_schema'] = {}
                    else:
                        result['item_type_schema'] = check_item_type['schema']

            elif num == 2:
                item_path = data_row
            elif num == 3:
                item_path_name = data_row
            else:
                data_parse_metadata = parse_to_json_form(
                    zip(item_path, item_path_name, data_row)
                )

                json_data_parse = parse_to_json_form(
                    zip(item_path_name, item_path, data_row)
                )
                if isinstance(check_item_type, dict):
                    item_type_name = check_item_type.get(
                        'name')
                    item_type_id = check_item_type.get('item_type_id')
                    tsv_item = dict(
                        **json_data_parse,
                        **data_parse_metadata,
                        **{
                            'item_type_name': item_type_name or '',
                            'item_type_id': item_type_id or '',
                            '$schema': schema if schema else ''
                        }
                    )
                else:
                    tsv_item = dict(**json_data_parse, **data_parse_metadata)
                tsv_data.append(tsv_item)
    result['tsv_data'] = tsv_data
    return result


def handle_validate_item_import(list_recond, schema) -> list:
    """Validate item import.

    :argument
        list_recond     -- {list} list recond import.
        schema     -- {dict} item_type schema.
    :return
        return       -- list_item_error.

    """
    from jsonschema import validate, Draft4Validator
    from jsonschema.exceptions import ValidationError
    result = []
    v2 = Draft4Validator(schema) if schema else None
    for record in list_recond:
        if record.get('metadata'):
            errors = []
            if v2:
                a = v2.iter_errors(record.get('metadata'))
                errors = [error.message for error in a]
            else:
                errors = ['ItemType is not exist']
            if record.get('metadata').get('path'):
                if not handle_check_index(record.get('metadata').get('path')):
                    errors.append('Index Error')
        item_error = dict(**record, **{
            'errors': errors if len(errors) else None
        })
        result.append(item_error)
    return result


def handle_check_index(list_index: list) -> bool:
    """Handle check index.

    :argument
        list_index     -- {list} list index id.
    :return
        return       -- true if exist.

    """
    result = True
    from weko_index_tree.api import Indexes
    index_lst = []
    if list_index:
        index_id_lst = []
        for index in list_index:
            if not index.isdigit():
                return False
            indexes = str(index).split('/')
            index_id_lst.append(indexes[len(indexes) - 1])
        index_lst = index_id_lst

    plst = Indexes.get_path_list(index_lst)
    if not plst or len(index_lst) != len(plst):
        result = False
    return result


def get_item_type(item_type_id=0) -> dict:
    """Get item type.

    :param item_type_id: Item type ID. (Default: 0).
    :return: The json object.

    """
    from weko_records.api import ItemTypes
    result = None
    if item_type_id > 0:
        itemtype = ItemTypes.get_by_id(item_type_id)
        if itemtype and itemtype.schema and itemtype.item_type_name.name and item_type_id:
            result = {
                'schema': itemtype.schema,
                'name': itemtype.item_type_name.name,
                'item_type_id': item_type_id
            }

    if result is None:
        return {}

    return result


def handle_check_exist_record(list_recond) -> list:
    """Check record is exist in system.

    :argument
        list_recond     -- {list} list recond import.
    :return
        return       -- list record has property status.

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
            else:
                try:
                    item_exist = WekoRecord.get_record_by_pid(item.get('id'))
                    if item_exist:
                        item['errors'] = ['Item already exists in the system']
                        item['status'] = None
                except BaseException:
                    current_app.logger.error('Unexpected error: ',
                                             sys.exc_info()[0])
        if item.get('status') == 'new':
            handle_remove_identifier(item)
        result.append(item)
    return result


def handle_check_identifier(name) -> str:
    """Check data is Identifier of Identifier Registration.

    :argument
        name_path     -- {list} list name path.
    :return
        return       -- Name of key if is Identifier.

    """
    result = ''
    if 'Identifier' in name or 'Identifier Registration' in name:
        result = name[0]
    return result


def handle_remove_identifier(item) -> dict:
    """Remove Identifier of Identifier Registration.

    :argument
        item         -- Item.
    :return
        return       -- Item had been removed property.

    """
    if item and item.get('Identifier key'):
        del item['metadata'][item.get('Identifier key')]
        del item['Identifier key']
        del item['Identifier']
    if item and item.get('Identifier Registration key'):
        del item['metadata'][item.get('Identifier Registration key')]
        del item['Identifier Registration key']
        del item['Identifier Registration']
    return item


def compare_identifier(item, item_exist):
    """Compare data is Identifier.

    :argument
        item           -- {dict} item import.
        item_exist     -- {dict} item in system.
    :return
        return       -- Name of key if is Identifier.

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

    :argument
        item           -- {dict} item import.
        item_exist     -- {dict} item in system.
    :return
        return       -- Name of key if is Identifier.

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


def create_deposit(rids):
    """Create deposit.

    :argument
        item           -- {dict} item import.
        item_exist     -- {dict} item in system.

    """
    from invenio_db import db
    from weko_deposit.api import WekoDeposit
    try:
        for rid in rids:
            try:
                WekoDeposit.create({}, recid=int(rid))
                db.session.commit()
                current_app.logger.info('Deposit id: %s created.' % rid)
            except Exception as ex:
                current_app.logger.error(
                    'Error occurred during creating deposit id: %s' % rid)
                current_app.logger.info(str(ex))
                db.session.rollback()
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])


def up_load_file_content(list_record, file_path):
    """Upload file content.

    :argument
        list_record    -- {list} list item import.
        file_path      -- {str} file path.

    """
    from invenio_db import db
    from invenio_files_rest.models import ObjectVersion
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_records.models import RecordMetadata
    try:
        for record in list_record:
            try:
                current_app.logger.debug(record)
                if record.get('file_path'):
                    for file_name in record.get('file_path'):
                        with open(file_path + '/' + file_name,
                                  'rb') as file:
                            pid = PersistentIdentifier.query.filter_by(
                                pid_type='recid',
                                pid_value=record.get('id')).first()
                            rec = RecordMetadata.query.filter_by(
                                id=pid.object_uuid).first()
                            bucket = rec.json['_buckets']['deposit']
                            obj = ObjectVersion.create(bucket,
                                                       get_file_name(file_name))
                            obj.set_contents(file)
                            db.session.commit()
            except Exception as ex:
                current_app.logger.info(str(ex))
                db.session.rollback()
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])


def get_file_name(file_path):
    """Get file name.

    :argument
        file_path    -- {str} file_path.
    :returns         -- {str} file name

    """
    return file_path.split('/')[-1] if file_path.split('/')[-1] else ''


def register_item_metadata(list_record):
    """Upload file content.

    :argument
        list_record    -- {list} list item import.
        file_path      -- {str} file path.
    """
    from invenio_db import db
    from weko_deposit.api import WekoDeposit
    from invenio_pidstore.models import PersistentIdentifier
    from invenio_records.models import RecordMetadata
    try:
        success_count = 0
        failure_list = []
        for data in list_record:
            try:
                item_id = str(data.get('id'))
                item_status = {
                    'index': data.get('IndexID'),
                    'actions': 'publish',
                }

                pid = PersistentIdentifier.query.filter_by(
                    pid_type='recid',
                    pid_value=item_id
                ).first()
                r = RecordMetadata.query.filter_by(
                    id=pid.object_uuid).first()
                _depisit_data = r.json.get('_deposit')
                dep = WekoDeposit(r.json, r)
                #
                new_data = dict(
                    **data.get('metadata'),
                    **_depisit_data,
                    **{
                        '$schema': data.get('$schema'),
                        'title': handle_get_title(data.get('Title')),
                    }
                )
                if not new_data.get('pid'):
                    new_data = dict(**new_data, **{
                        'pid': {
                            'revision_id': 0,
                            'type': 'recid',
                            'value': item_id
                        }
                    })
                dep.update(item_status, new_data)
                dep.commit()
                dep.publish()
                handle_workflow(data)
                with current_app.test_request_context() as ctx:
                    first_ver = dep.newversion(pid)
                    first_ver.publish()

                db.session.commit()

                success_count += 1
            except Exception as ex:
                db.session.rollback()
                current_app.logger.error('item id: %s update error.' % item_id)
                current_app.logger.error(ex)
                failure_list.append(item_id)
        current_app.logger.info('%s items updated.' % success_count)
        current_app.logger.info('failure list:')
        current_app.logger.info(failure_list)

    except Exception as e:
        current_app.logger.error(e)


def handle_get_title(title) -> str:
    """Handle get title.

    :argument
        title           -- {dict or list} title.
    :return
        return       -- title string.

    """
    if isinstance(title, dict):
        return title.get('Title', '')
    elif isinstance(title, list):
        return title[0].get('Title') if title[0] and isinstance(title[0], dict)\
            else ''


def handle_workflow(item: dict):
    """Handle workflow.

    :argument
        title           -- {dict or list} title.
    :return
        return       -- title string.

    """
    from weko_workflow.api import GetCommunity, WorkActivity
    from weko_workflow.models import FlowDefine, WorkFlow
    activity = WorkActivity()
    wf_activity = activity.get_workflow_activity_by_item_id(
        item_id=item.get('item_id'))
    if wf_activity:
        return
    else:
        workflow = WorkFlow.query.filter_by(
            itemtype_id=item.get('item_type_id')).first()
        if workflow:
            return
        else:
            create_work_flow(item.get('item_type_id'))


def create_work_flow(item_type_id):
    """Handle create work flow.

    :argument
        item_type_id        -- {str} item_type_id.
    :return

    """
    from weko_workflow.models import FlowDefine, WorkFlow
    from weko_records.api import ItemTypes
    import uuid
    flow_define = FlowDefine.query.filter_by(
            flow_name='Registration Flow').first()
    it = ItemTypes.get_by_id(item_type_id)

    if not flow_define:
        create_flow_define()
        flow_define = FlowDefine.query.filter_by(
            flow_name='Registration Flow').first()
    if flow_define and it:
        with db.session.begin_nested():
            data = WorkFlow()
            data.flows_id = uuid.uuid4()
            data.flows_name = it.item_type_name.name
            data.itemtype_id = it.id
            data.flow_id = flow_define.id
            db.session.add(data)
        db.session.commit()
        current_app.logger.info('creating workflow is finished')
    else:
        if not flow_define:
            current_app.logger.error('workflow define is not exist')
        if not it:
            current_app.logger.error('item type is not exist')


def create_flow_define():
    """Handle create flow_define."""
    from weko_workflow.api import Flow
    from .config import WEKO_FLOW_DEFINE, WEKO_FLOW_DEFINE_LIST_ACTION
    the_flow = Flow()
    flow = the_flow.create_flow(WEKO_FLOW_DEFINE)
    the_flow.upt_flow_action(flow.flow_id, WEKO_FLOW_DEFINE_LIST_ACTION)
