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
import csv
import json
import os
import re
import shutil
import sys
import tempfile
import traceback
import uuid
import zipfile
from collections import Callable, OrderedDict
from datetime import datetime
from functools import partial, reduce, wraps
from io import StringIO
from operator import getitem

import bagit
import redis
from celery.result import AsyncResult
from celery.task.control import revoke
from flask import abort, current_app, request
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_db import db
from invenio_files_rest.models import FileInstance, Location, ObjectVersion
from invenio_i18n.ext import current_i18n
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from invenio_search import RecordsSearch
from jsonschema import Draft4Validator
from weko_admin.models import SessionLifetime
from weko_admin.utils import get_redis_cache
from weko_authors.utils import check_email_existed
from weko_deposit.api import WekoDeposit, WekoIndexer, WekoRecord
from weko_deposit.pidstore import get_latest_version_id
from weko_handle.api import Handle
from weko_index_tree.api import Indexes
from weko_index_tree.utils import check_index_permissions, \
    check_restrict_doi_with_indexes
from weko_indextree_journal.api import Journals
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping
from weko_workflow.api import Flow, WorkActivity
from weko_workflow.config import IDENTIFIER_GRANT_LIST, \
    IDENTIFIER_GRANT_SUFFIX_METHOD
from weko_workflow.models import FlowDefine, WorkFlow
from weko_workflow.utils import IdentifierHandle, check_existed_doi, \
    get_identifier_setting, get_sub_item_value, get_url_root, \
    item_metadata_validation, register_hdl_by_handle, \
    register_hdl_by_item_id, saving_doi_pidstore

from .config import ACCESS_RIGHT_TYPE_URI, DATE_ISO_TEMPLATE_URL, \
    RESOURCE_TYPE_URI, VERSION_TYPE_URI, \
    WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_EXTENSION, \
    WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LANGUAGES, \
    WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LOCATION, \
    WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FIRST_FILE_NAME, \
    WEKO_ADMIN_LIFETIME_DEFAULT, WEKO_FLOW_DEFINE, \
    WEKO_FLOW_DEFINE_LIST_ACTION, WEKO_IMPORT_DOI_TYPE, \
    WEKO_IMPORT_EMAIL_PATTERN, WEKO_IMPORT_PUBLISH_STATUS, \
    WEKO_IMPORT_SUFFIX_PATTERN, WEKO_IMPORT_SYSTEM_ITEMS, \
    WEKO_IMPORT_THUMBNAIL_FILE_TYPE, WEKO_IMPORT_VALIDATE_MESSAGE, \
    WEKO_REPO_USER, WEKO_SEARCH_TYPE_DICT, WEKO_SEARCH_UI_BULK_EXPORT_TASK, \
    WEKO_SEARCH_UI_BULK_EXPORT_URI, WEKO_SYS_USER
from .query import feedback_email_search_factory, item_path_search_factory

err_msg_suffix = 'Suffix of {} can only be used with half-width' \
    + ' alphanumeric characters and half-width symbols "_-.; () /".'


class DefaultOrderedDict(OrderedDict):
    """Default Dictionary that remembers insertion order."""

    def __init__(self, default_factory=None, *a, **kw):
        """Initialize an default ordered dictionary.

        The signature
        is the same as regular dictionaries.  Keyword argument order
        is preserved.
        """
        if default_factory is not None and \
                not isinstance(default_factory, Callable):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        """Modify inherited dict provides __getitem__."""
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        """Needed so that self[missing_item] does not raise KeyError."""
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        """Return state information for pickling."""
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        """Modify inherited dict provides copy.

        od.copy() -> a shallow copy of od.
        """
        return self.__copy__()

    def __copy__(self):
        """Modify inherited dict provides __copy__."""
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        """Modify inherited dict provides __deepcopy__."""
        import copy
        return type(self)(self.default_factory,
                          copy.deepcopy(self.items()))

    def __repr__(self):
        """Return a nicely formatted representation string."""
        return 'OrderedDefaultDict(%s, %s)' % (self.default_factory,
                                               OrderedDict.__repr__(self))


def get_tree_items(index_tree_id):
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance, _ = item_path_search_factory(
        None, records_search, index_id=index_tree_id)
    search_result = search_instance.execute()
    rd = search_result.to_dict()
    return rd.get('hits').get('hits')


def delete_records(index_tree_id):
    """Bulk delete records."""
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
    result = {}
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
        open_search_uri = request.host_url + journal.get('title_url')
        result.update({'openSearchUrl': open_search_uri})

    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        abort(500)
    return result


def get_feedback_mail_list():
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
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
        item    -- {Object PostgreSql} list work flow

    :return
        result  -- {dictionary} content of work flow

    """
    result = dict()
    result['flows_name'] = item.flows_name
    result['id'] = item.id
    result['itemtype_id'] = item.itemtype_id
    result['flow_id'] = item.flow_id
    result['flow_name'] = item.flow_define.flow_name
    result['item_type_name'] = item.itemtype.item_type_name.name

    return result


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
    return DefaultOrderedDict(define_default_dict)


def defaultify(d: dict) -> dict:
    """Create default dict.

    :argument
        d            -- {dict} current dict.
    :return
        return       -- {dict} default dict.

    """
    if not isinstance(d, dict):
        return d
    return DefaultOrderedDict(
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


def parse_to_json_form(data: list, item_path_not_existed: list) -> dict:
    """Parse set argument to json object.

    :argument
        data    -- {list zip} argument if json object.
        item_path_not_existed -- {list} item paths not existed in metadata.
    :return
        return  -- {dict} dict after convert argument.

    """
    result = defaultify({})

    def convert_data(pro, path=None):
        """Convert data."""
        if path is None:
            path = []

        term_path = path
        if isinstance(pro, dict):
            list_pro = list(pro.keys())
            for pro_name in list_pro:
                term = list(term_path)
                term.append(pro_name)
                convert_data(pro[pro_name], term)
            if list_pro and list_pro[0].isnumeric():
                convert_nested_item_to_list(result, term_path)
        else:
            return

    for key, value in data:
        if key in item_path_not_existed:
            continue
        key_path = handle_generate_key_path(key)
        if value or key_path[0] in ['file_path', 'thumbnail_path'] \
                or key_path[-1] == 'filename':
            set_nested_item(result, key_path, value)

    convert_data(result)
    result = json.loads(json.dumps(result))
    return result


def check_import_items(file_name: str, file_content: str,
                       is_change_identifier: bool):
    """Validation importing zip file.

    :argument
        file_name -- file name.
        file_content -- content file's name.
        is_change_identifier -- Change Identifier Mode.
    :return
        return       -- PID object if exist.

    """
    file_content_decoded = base64.b64decode(file_content)
    tmp_prefix = current_app.config['WEKO_SEARCH_UI_IMPORT_TMP_PREFIX']
    temp_path = tempfile.TemporaryDirectory(prefix=tmp_prefix)
    save_path = tempfile.gettempdir()
    import_path = temp_path.name + '/' + \
        datetime.utcnow().strftime(r'%Y%m%d%H%M%S')
    data_path = save_path + '/' + tmp_prefix + \
        datetime.utcnow().strftime(r'%Y%m%d%H%M%S')
    result = {'data_path': data_path}

    try:
        # Create temp dir for import data
        os.mkdir(data_path)

        with open(import_path + '.zip', 'wb+') as f:
            f.write(file_content_decoded)
        with zipfile.ZipFile(import_path + '.zip') as z:
            for info in z.infolist():
                try:
                    info.filename = info.orig_filename.encode(
                        'cp437').decode('cp932')
                    if os.sep != "/" and os.sep in info.filename:
                        info.filename = info.filename.replace(os.sep, "/")
                except Exception:
                    current_app.logger.warn('-' * 60)
                    traceback.print_exc(file=sys.stdout)
                    current_app.logger.warn('-' * 60)
                z.extract(info, path=data_path)

        data_path += '/data'
        list_record = []
        list_tsv = list(
            filter(lambda x: x.endswith('.tsv'), os.listdir(data_path)))
        if not list_tsv:
            raise FileNotFoundError()
        for tsv_entry in list_tsv:
            list_record.extend(unpackage_import_file(data_path, tsv_entry))
        list_record = handle_check_exist_record(list_record)
        handle_item_title(list_record)
        handle_check_and_prepare_publish_status(list_record)
        handle_check_and_prepare_index_tree(list_record)
        handle_check_and_prepare_feedback_mail(list_record)
        handle_set_change_identifier_flag(
            list_record, is_change_identifier)
        handle_check_cnri(list_record)
        handle_check_doi_indexes(list_record)
        handle_check_doi_ra(list_record)
        handle_check_doi(list_record)
        handle_check_date(list_record)
        handle_check_file_metadata(list_record, data_path)
        result['list_record'] = list_record
    except Exception as ex:
        error = _('Internal server error')
        if isinstance(ex, zipfile.BadZipFile):
            error = _('The format of the specified file {} does not'
                      + ' support import. Please specify one of the'
                      + ' following formats: zip, tar, gztar, bztar,'
                      + ' xztar.').format(file_name)
        elif isinstance(ex, FileNotFoundError):
            error = _('The TSV file was not found in the specified file {}.'
                      + ' Check if the directory structure is correct.') \
                .format(file_name)
        elif isinstance(ex, UnicodeDecodeError):
            error = ex.reason
        elif ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_msg'):
            error = ex.args[0].get('error_msg')
        result['error'] = error
        current_app.logger.error('-' * 60)
        traceback.print_exc(file=sys.stdout)
        current_app.logger.error('-' * 60)
    finally:
        temp_path.cleanup()
    return result


def unpackage_import_file(data_path: str, tsv_file_name: str) -> list:
    """Getting record data from TSV file.

    :argument
        file_content -- Content files.
    :return
        return       -- PID object if exist.

    """
    tsv_file_path = '{}/{}'.format(data_path, tsv_file_name)
    data = read_stats_tsv(tsv_file_path, tsv_file_name)
    list_record = data.get('tsv_data')
    handle_fill_system_item(list_record)
    list_record = handle_validate_item_import(list_record, data.get(
        'item_type_schema', {}
    ))
    return list_record


def read_stats_tsv(tsv_file_path: str, tsv_file_name: str) -> dict:
    """Read importing TSV file.

    :argument
        tsv_file_path -- tsv file's url.
        tsv_file_name -- tsv file name.
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
    check_item_type = {}
    item_path_not_existed = []
    schema = ''
    with open(tsv_file_path, 'r') as tsvfile:
        csv_reader = csv.reader(tsvfile, delimiter='\t')
        try:
            for num, data_row in enumerate(csv_reader, start=1):
                # current_app.logger.debug(num)
                # current_app.logger.debug(data_row)
                if num == 1:
                    first_line_format_exception = Exception({
                        'error_msg': _('There is an error in the format of the'
                                       + ' first line of the header of the TSV'
                                       + ' file.')
                    })
                    if len(data_row) < 3:
                        raise first_line_format_exception

                    item_type_id = data_row[2].split('/')[-1]
                    if not item_type_id or \
                            not re.search(r'^[0-9]*$', item_type_id):
                        raise first_line_format_exception
                    check_item_type = get_item_type(int(item_type_id))
                    schema = data_row[2]
                    if not check_item_type:
                        result['item_type_schema'] = {}
                        raise Exception({
                            'error_msg': _('The item type ID specified in'
                                           + ' the TSV file does not exist.')
                        })
                    else:
                        result['item_type_schema'] = check_item_type['schema']
                        if not check_item_type.get('is_lastest'):
                            raise Exception({
                                'error_msg': _('Cannot register because the '
                                               + 'specified item type is not '
                                               + 'the latest version.')
                            })
                elif num == 2:
                    item_path = data_row
                    duplication_item_ids = \
                        handle_check_duplication_item_id(item_path)
                    current_app.logger.debug(duplication_item_ids)
                    if duplication_item_ids:
                        msg = _(
                            'The following metadata keys are duplicated.'
                            '<br/>{}')
                        raise Exception({
                            'error_msg':
                                msg.format('<br/>'.join(duplication_item_ids))
                        })
                    if check_item_type:
                        not_consistent_list = \
                            handle_check_consistence_with_item_type(
                                check_item_type.get('item_type_id'),
                                item_path)
                        if not_consistent_list:
                            msg = _('The item does not consistent with the '
                                    'specified item type.<br/>{}')
                            raise Exception({
                                'error_msg':
                                    msg.format(
                                        '<br/>'.join(not_consistent_list))
                            })
                        item_path_not_existed = \
                            handle_check_metadata_not_existed(
                                item_path, check_item_type.get('item_type_id'))
                elif (num == 4 or num == 5) and data_row[0].startswith('#'):
                    continue
                elif num > 5:
                    data_parse_metadata = parse_to_json_form(
                        zip(item_path, data_row),
                        item_path_not_existed
                    )

                    if not data_parse_metadata:
                        raise Exception({
                            'error_msg': _('Cannot read tsv file correctly.')
                        })
                    if isinstance(check_item_type, dict):
                        item_type_name = check_item_type.get('name')
                        item_type_id = check_item_type.get('item_type_id')
                        tsv_item = dict(
                            **data_parse_metadata,
                            **{
                                'item_type_name': item_type_name or '',
                                'item_type_id': item_type_id or '',
                                '$schema': schema if schema else ''
                            }
                        )
                    else:
                        tsv_item = dict(**data_parse_metadata)
                    if item_path_not_existed:
                        str_keys = ', '.join(item_path_not_existed) \
                            .replace('.metadata.', '')
                        tsv_item['warnings'] = [
                            _('The following items are not registered because '
                              + 'they do not exist in the specified '
                              + 'item type. {}')
                            .format(str_keys)
                        ]
                    tsv_data.append(tsv_item)
        except UnicodeDecodeError as ex:
            ex.reason = _('The TSV file could not be read. Make sure the file'
                          + ' format is TSV and that the file is'
                          + ' UTF-8 encoded.').format(tsv_file_name)
            raise ex
        except Exception as ex:
            raise ex
    result['tsv_data'] = tsv_data
    return result


def handle_convert_validate_msg_to_jp(message: str):
    """Convert validation messages from en to jp.

    :argument
        message     -- {str} English message.
    :return
        return       -- Japanese message.

    """
    result = None
    for msg_en, msg_jp in WEKO_IMPORT_VALIDATE_MESSAGE.items():
        msg_en_pattern = '^{}$'.format(msg_en.replace('%r', '.*'))
        if re.search(msg_en_pattern, message):
            msg_paths = msg_en.split('%r')
            prev_position = 0
            data = []
            for idx, path in enumerate(msg_paths, start=1):
                position = message.index(path)
                if path == '':
                    if idx == 1:
                        continue
                    elif idx == len(msg_paths):
                        prev_position += len(msg_paths[idx - 2])
                        position = len(message)
                if position >= 0:
                    data.append(message[prev_position: position])
                    prev_position = position
            if data:
                result = msg_jp
            for value in data:
                result = result.replace('%r', value, 1)
            return result
    return message


def handle_validate_item_import(list_record, schema) -> list:
    """Validate item import.

    :argument
        list_record     -- {list} list record import.
        schema     -- {dict} item_type schema.
    :return
        return       -- list_item_error.

    """
    result = []
    v2 = Draft4Validator(schema) if schema else None
    for record in list_record:
        errors = record.get('errors') or []
        record_id = record.get("id")
        if record_id and (not represents_int(record_id)
                          or re.search(r'([０-９])', record_id)):
            errors.append(_('Please specify item ID by half-width number.'))
        if record.get('metadata'):
            if v2:
                a = v2.iter_errors(record.get('metadata'))
                if current_i18n.language == 'ja':
                    _errors = []
                    for error in a:
                        _errors.append(handle_convert_validate_msg_to_jp(
                            error.message))
                    errors = errors + _errors
                else:
                    errors = errors + [error.message for error in a]
            else:
                errors = errors = errors + \
                    [_('Specified item type does not exist.')]

        item_error = dict(**record)
        item_error['errors'] = errors if len(errors) else None
        result.append(item_error)

    return result


def represents_int(s):
    """Handle check string is int.

    :argument
        s     -- {str} string number.
    :return
        return       -- true if is Int.

    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_item_type(item_type_id=0) -> dict:
    """Get item type.

    :param item_type_id: Item type ID. (Default: 0).
    :return: The json object.
    """
    result = None
    if item_type_id > 0:
        itemtype = ItemTypes.get_by_id(item_type_id)
        if itemtype and itemtype.schema \
                and itemtype.item_type_name.name and item_type_id:
            lastest_id = itemtype.item_type_name.item_type.first().id
            result = {
                'schema': itemtype.schema,
                'is_lastest': lastest_id == item_type_id,
                'name': itemtype.item_type_name.name,
                'item_type_id': item_type_id
            }

    if result is None:
        return {}

    return result


def handle_check_exist_record(list_record) -> list:
    """Check record is exist in system.

    :argument
        list_record -- {list} list record import.
    :return
        return      -- list record has property status.

    """
    result = []
    current_app.logger.debug('handle_check_exist_record')
    for item in list_record:
        item = dict(**item, **{
            'status': 'new'
        })
        errors = item.get('errors') or []
        try:
            item_id = item.get('id')
            current_app.logger.debug(item_id)
            if item_id:
                system_url = request.url_root + 'records/' + item_id
                if item.get('uri') != system_url:
                    errors.append(_('Specified URI and system'
                                    ' URI do not match.'))
                    item['status'] = None
                else:
                    item_exist = WekoRecord.get_record_by_pid(item_id)
                    if item_exist:
                        if item_exist.pid.is_deleted():
                            item['status'] = None
                            errors.append(_('Item already DELETED'
                                            ' in the system'))
                        else:
                            exist_url = request.url_root + \
                                'records/' + item_exist.get('recid')
                            if item.get('uri') == exist_url:
                                _edit_mode = item.get('edit_mode')
                                if not _edit_mode or _edit_mode.lower() \
                                        not in ['keep', 'upgrade']:
                                    errors.append(
                                        _('Please specify either \"Keep\"'
                                          ' or "Upgrade".'))
                                    item['status'] = None
                                else:
                                    item['status'] = _edit_mode.lower()
            else:
                item['id'] = None
#                if item.get('uri'):
#                    errors.append(_('Item ID does not match the'
#                                    + ' specified URI information.'))
#                    item['status'] = None
        except PIDDoesNotExistError:
            pass
        except BaseException:
            current_app.logger.error(
                'Unexpected error: ',
                sys.exc_info()[0]
            )
        if errors:
            item['errors'] = errors
        result.append(item)
    return result


def make_tsv_by_line(lines):
    """Make TSV file."""
    tsv_output = StringIO()

    writer = csv.writer(tsv_output, delimiter='\t')
    writer.writerows(lines)

    return tsv_output


def make_stats_tsv(raw_stats, list_name):
    """Make TSV report file for stats."""
    tsv_output = StringIO()

    writer = csv.writer(tsv_output, delimiter='\t',
                        lineterminator="\n")

    writer.writerow(list_name)
    for item in raw_stats:
        term = []
        for name in list_name:
            term.append(item.get(name))
        writer.writerow(term)

    return tsv_output


def create_deposit(item_id):
    """Create deposit.

    :argument
        item           -- {dict} item import.
        item_exist     -- {dict} item in system.

    """
    if item_id is not None:
        dep = WekoDeposit.create({}, recid=int(item_id))
    else:
        dep = WekoDeposit.create({})
    return dep['recid']


def clean_thumbnail_file(bucket, root_path, thumbnail_path):
    """Remove all thumbnail in bucket.

    :argument
        bucket         -- {object} bucket.
        root_path      -- {str} location of temp folder.
        thumbnail_path -- {list} thumbnails path.
    """
    list_not_remove = list(filter(
        lambda path: not os.path.isfile(root_path + '/' + path),
        thumbnail_path))
    list_not_remove = [get_file_name(path) for path in list_not_remove]
    all_file_version = ObjectVersion.get_by_bucket(
        bucket, True, True).all()
    for file in all_file_version:
        if file.is_thumbnail is True and file.key not in list_not_remove:
            file.remove()


def up_load_file(record, root_path):
    """Upload thumbnail or file content.

    :argument
        record         -- {dict} item import.
        root_path      -- {str} root_path.

    """
    file_path = list(filter(lambda path: path, record.get('file_path', [])))
    thumbnail_path = record.get('thumbnail_path', [])
    if isinstance(thumbnail_path, str):
        thumbnail_path = [thumbnail_path]
    else:
        thumbnail_path = list(filter(lambda path: path, thumbnail_path))
    if file_path or thumbnail_path:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value=record.get('id')).first()
        rec = RecordMetadata.query.filter_by(
            id=pid.object_uuid).first()
        bucket = rec.json['_buckets']['deposit']
        clean_thumbnail_file(bucket, root_path, thumbnail_path)
        for path in [*file_path, *thumbnail_path]:
            if not os.path.isfile(root_path + '/' + path):
                continue
            with open(root_path + '/' + path, 'rb') as file:
                obj = ObjectVersion.create(
                    bucket,
                    get_file_name(path)
                )
                if path in thumbnail_path:
                    obj.is_thumbnail = True
                obj.set_contents(file)


def get_file_name(file_path):
    """Get file name.

    :argument
        file_path    -- {str} file_path.
    :returns         -- {str} file name

    """
    return file_path.split('/')[-1] if file_path.split('/')[-1] else ''


def register_item_metadata(item):
    """Upload file content.

    :argument
        list_record    -- {list} list item import.
        file_path      -- {str} file path.
    """
    def clean_file_metadata(item_type_id, data):
        # clear metadata of file information
        item_map = get_mapping(Mapping.get_record(
            item_type_id), 'jpcoar_mapping')
        _, key = get_data_by_property(
            item, item_map, "file.URI.@value")
        if key:
            key = key.split('.')[0]
            if not data.get(key):
                deleted_items = data.get('deleted_items') or []
                deleted_items.append(key)
                data['deleted_items'] = deleted_items
        return data

    def autofill_thumbnail_metadata(item_type_id, data):
        key = get_thumbnail_key(item_type_id)
        if key:
            all_file_version = ObjectVersion.get_by_bucket(
                deposit.files.bucket, True, True).all()
            thumbnail_item = {}
            subitem_thumbnail = []
            for file in all_file_version:
                if file.is_thumbnail is True:
                    subitem_thumbnail.append({
                        'thumbnail_label': file.key,
                        'thumbnail_uri':
                            current_app.config['DEPOSIT_FILES_API']
                            + u'/{bucket}/{key}?versionId={version_id}'.format(
                                bucket=file.bucket_id,
                                key=file.key,
                                version_id=file.version_id)
                    })
            if subitem_thumbnail:
                thumbnail_item['subitem_thumbnail'] = subitem_thumbnail
            if thumbnail_item:
                data[key] = thumbnail_item
            else:
                deleted_items = data.get('deleted_items') or []
                deleted_items.append(key)
                data['deleted_items'] = deleted_items
        return data

    def clean_file_bucket(deposit):
        # clean bucket
        file_names = [file.get('filename', '')
                      for file in deposit.get_file_data()]
        lastest_files_version = []
        # remove lastest version
        for file in deposit.files:
            if file.obj.is_thumbnail is False \
                    and file.obj.key not in file_names:
                file.obj.remove()
            else:
                lastest_files_version.append(file.obj.version_id)
        # remove old version of file
        all_file_version = ObjectVersion.get_by_bucket(
            deposit.files.bucket, True, True).all()
        for file in all_file_version:
            if file.version_id not in lastest_files_version:
                file.remove()

    def clean_all_file_in_bucket(deposit):
        all_file_version = ObjectVersion.get_by_bucket(
            deposit.files.bucket, True, True).all()
        for file in all_file_version:
            if file.is_thumbnail is False:
                file.remove()

    item_id = str(item.get('id'))
    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value=item_id
    ).first()

    record = WekoDeposit.get_record(pid.object_uuid)

    _deposit_data = record.dumps().get("_deposit")
    deposit = WekoDeposit(record, record.model)
    new_data = dict(
        **item.get('metadata'),
        **_deposit_data,
        **{
            '$schema': item.get('$schema'),
            'title': item.get('item_title'),
        }
    )
    item_status = {
        'index': new_data['path'],
        'actions': 'publish',
    }
    if not new_data.get('pid'):
        new_data = dict(**new_data, **{
            'pid': {
                'revision_id': 0,
                'type': 'recid',
                'value': item_id
            }
        })
    new_data = autofill_thumbnail_metadata(item['item_type_id'], new_data)
    new_data = clean_file_metadata(item['item_type_id'], new_data)
    deposit.update(item_status, new_data)
    if list(filter(lambda path: path, item.get('file_path', []))):
        # update
        clean_file_bucket(deposit)
    else:
        # delete
        clean_all_file_in_bucket(deposit)
    deposit.commit()
    deposit.publish_without_commit()

    feedback_mail_list = item['metadata'].get('feedback_mail_list')
    if feedback_mail_list:
        FeedbackMailList.update(
            item_id=deposit.id,
            feedback_maillist=feedback_mail_list
        )
        deposit.update_feedback_mail()
    else:
        FeedbackMailList.delete_without_commit(deposit.id)
        deposit.remove_feedback_mail()

    with current_app.test_request_context(get_url_root()):
        if item['status'] in ['upgrade', 'new']:
            _deposit = deposit.newversion(pid)
            _deposit.publish_without_commit()
        else:
            _pid = PIDVersioning(child=pid).last_child
            _record = WekoDeposit.get_record(_pid.object_uuid)
            _deposit = WekoDeposit(_record, _record.model)
            _deposit.merge_data_to_record_without_version(pid)
            _deposit.publish_without_commit()

        if feedback_mail_list:
            FeedbackMailList.update(
                item_id=_deposit.id,
                feedback_maillist=feedback_mail_list
            )
            _deposit.update_feedback_mail()


def update_publish_status(item_id, status):
    """Handle get title.

    :argument
        item_id     -- {str} Item Id.
        status      -- {str} Publish status (0: public, 1: private)
    :return

    """
    record = WekoRecord.get_record_by_pid(item_id)
    record['publish_status'] = status
    record.commit()
    indexer = WekoIndexer()
    indexer.update_publish_status(record)


def handle_workflow(item: dict):
    """Handle workflow.

    :argument
        title           -- {dict or list} title.
    :return
        return       -- title string.

    """
    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid', pid_value=item.get('id')).first()
    if pid:
        activity = WorkActivity()
        wf_activity = activity.get_workflow_activity_by_item_id(
            pid.object_uuid)
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
    flow_define = FlowDefine.query.filter_by(
        flow_name='Registration Flow').first()
    it = ItemTypes.get_by_id(item_type_id)

    if flow_define and it:
        try:
            data = WorkFlow()
            data.flows_id = uuid.uuid4()
            data.flows_name = it.item_type_name.name
            data.itemtype_id = it.id
            data.flow_id = flow_define.id
            db.session.add(data)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error("create work flow error")
            current_app.logger.error(ex)


def create_flow_define():
    """Handle create flow_define."""
    flow_define = FlowDefine.query.filter_by(
        flow_name='Registration Flow').first()

    if not flow_define:
        the_flow = Flow()
        flow = the_flow.create_flow(WEKO_FLOW_DEFINE)

        if flow and flow.flow_id:
            the_flow.upt_flow_action(flow.flow_id,
                                     WEKO_FLOW_DEFINE_LIST_ACTION)


def import_items_to_system(item: dict):
    """Validation importing zip file.

    :argument
        item        -- Items Metadata.
    :return
        return      -- PID object if exist.

    """
    if not item:
        return None
    else:
        try:
            root_path = item.get('root_path', '')
            if item.get('status') == 'new':
                item_id = create_deposit(item.get('id'))
                item['id'] = item_id
            else:
                handle_check_item_is_locked(item)

            up_load_file(item, root_path)
            register_item_metadata(item)
            if current_app.config.get('WEKO_HANDLE_ALLOW_REGISTER_CRNI'):
                register_item_handle(item)
            register_item_doi(item)

            status_number = WEKO_IMPORT_PUBLISH_STATUS.index(
                item.get('publish_status')
            )
            register_item_update_publish_status(item, str(status_number))

            db.session.commit()
        except Exception as ex:
            if item.get('id'):
                handle_remove_es_metadata(item)

            db.session.rollback()
            current_app.logger.error('item id: %s update error.' % item['id'])
            current_app.logger.error(ex)
            error_id = None
            if ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                    and ex.args[0].get('error_id'):
                error_id = ex.args[0].get('error_id')

            return {
                'success': False,
                'error_id': error_id
            }
    return {
        'success': True
    }


def remove_temp_dir(path):
    """Validation importing zip file.

    :argument
        path     -- {string} path temp_dir.
    :return

    """
    shutil.rmtree(path)


def handle_item_title(list_record):
    """Prepare item title.

    :argument
        list_record -- {list} list record import.
    :return

    """
    for item in list_record:
        error = None
        item_type_mapping = Mapping.get_record(item['item_type_id'])
        item_map = get_mapping(item_type_mapping, 'jpcoar_mapping')
        title_data, _title_key = get_data_by_property(
            item, item_map, "title.@value")
        if not title_data:
            error = _('Title is required item.')
        else:
            item['item_title'] = title_data[0]

        if error:
            item['errors'] = item['errors'] + [error] \
                if item.get('errors') else [error]


def handle_check_and_prepare_publish_status(list_record):
    """Check and prepare publish status.

    :argument
        list_record -- {list} list record import.
    :return

    """
    for item in list_record:
        error = None
        publish_status = item.get('publish_status')
        if not publish_status:
            error = _('{} is required item.').format('PUBLISH_STATUS')
        elif publish_status not in WEKO_IMPORT_PUBLISH_STATUS:
            error = _('Please set "public" or "private" for {}.') \
                .format('PUBLISH_STATUS')

        if error:
            item['errors'] = item['errors'] + [error] \
                if item.get('errors') else [error]


def handle_check_and_prepare_index_tree(list_record):
    """Check index existed and prepare index tree data.

    :argument
        list_record -- {list} list record import.
    :return

    """
    errors = []
    warnings = []

    def check(index_ids, index_names, parent_id=0, is_root=False):
        index_id = index_ids[0]
        index_name = index_names[0]
        index = None
        try:
            index = Indexes.get_index(index_id)
        except Exception:
            current_app.logger.warning("Specified IndexID is invalid!")

        if index and (
            (is_root and not index.parent)
            or (not is_root and parent_id and index.parent == parent_id)
        ):
            if index.index_name_english != index_name:
                warnings.append(
                    _('Specified {} does not match with existing index.')
                    .format('POS_INDEX'))
        elif index_name:
            index = Indexes.get_index_by_name_english(
                index_name, parent_id)
            msg_not_exist = _('The specified {} does not exist in system.')
            if not index:
                if index_id:
                    errors.append(msg_not_exist.format('IndexID, POS_INDEX'))
                    return None
                else:
                    errors.append(msg_not_exist.format('POS_INDEX'))
                    return None
            else:
                if index_id:
                    errors.append(msg_not_exist.format('IndexID'))
                    return None

        data = {
            'index_id': index.id if index else index_id,
            'index_name': index.index_name_english if index else index_name,
            'parent_id': parent_id
        }

        if len(index_ids) > 1:
            child = check(index_ids[1:], index_names[1:],
                          data['index_id'], False)
            if child:
                data['child'] = child
            else:
                return None

        return data

    for item in list_record:
        indexes = []
        index_ids = item.get('metadata', {}).get('path', [])
        pos_index = item.get('pos_index')

        if not index_ids and not pos_index:
            errors = [_('Both of IndexID and POS_INDEX are not being set.')]
        else:
            if not index_ids:
                index_ids = ['' for i in range(len(pos_index))]
            for x, index_id in enumerate(index_ids):
                tree_ids = [i.strip() for i in index_id.split('/')]
                tree_names = []
                if pos_index and x <= len(pos_index) - 1:
                    tree_names = [
                        i.strip().replace('\\/', '/')
                        for i in re.split(r'(?<!\\)\/', pos_index[x])
                    ]
                    if index_id == '':
                        tree_ids = ['' for i in tree_names]
                else:
                    tree_names = ['' for i in range(len(tree_ids))]

                root = check(tree_ids, tree_names, 0, True)
                if root:
                    indexes.append(root)

        if indexes:
            item['indexes'] = indexes
            handle_index_tree(item)

        if errors:
            errors = list(set(errors))
            item['errors'] = item['errors'] + errors \
                if item.get('errors') else errors
            errors = []

        if warnings:
            warnings = list(set(warnings))
            item['warnings'] = item['warnings'] + warnings \
                if item.get('warnings') else warnings
            warnings = []


def handle_index_tree(item):
    """Handle get index_id of item need import to.

    :argument
        item     -- {object} record item.
    :return

    """
    def check_and_create_index(index):
        if index.get('child'):
            return check_and_create_index(index['child'])
        else:
            return index['index_id']  # Return last child index_id

    indexes = item['indexes']
    if indexes:
        path = []
        for index in indexes:
            path.append(check_and_create_index(index))
        item['metadata']['path'] = path


def handle_check_and_prepare_feedback_mail(list_record):
    """Check feedback email is existed in database and prepare data.

    :argument
        list_record -- {list} list record import.
    :return

    """
    for item in list_record:
        errors = []
        feedback_mail = []
        if item.get('feedback_mail'):
            for mail in item.get('feedback_mail'):
                if not re.search(WEKO_IMPORT_EMAIL_PATTERN, mail):
                    errors.append(_('Specified {} is invalid.').format(mail))
                else:
                    email_checked = check_email_existed(mail)
                    feedback_mail.append(email_checked)

            if feedback_mail:
                item['metadata']['feedback_mail_list'] = feedback_mail
            if errors:
                errors = list(set(errors))
                item['errors'] = item['errors'] + errors \
                    if item.get('errors') else errors


def handle_set_change_identifier_flag(list_record, is_change_identifier):
    """Set Change Identifier Mode flag.

    :argument
        list_record -- {list} list record import.
        is_change_identifier -- {bool} Change Identifier Mode.
    :return

    """
    for item in list_record:
        item['is_change_identifier'] = is_change_identifier


def handle_check_cnri(list_record):
    """Check CNRI.

    :argument
        list_record -- {list} list record import.
    :return

    """
    for item in list_record:
        error = None
        item_id = str(item.get('id'))
        cnri = item.get('cnri')
        cnri_set = current_app.config.get('WEKO_HANDLE_ALLOW_REGISTER_CRNI')

        if item.get('is_change_identifier') and cnri_set:
            if not cnri:
                error = _('Please specify {}.').format('CNRI')
            else:
                if len(cnri) > 290:
                    error = _('The specified {} exceeds the maximum length.') \
                        .format('CNRI')
                else:
                    split_cnri = cnri.split('/')
                    if len(split_cnri) > 1:
                        prefix = '/'.join(split_cnri[0:-1])
                        suffix = split_cnri[-1]
                    else:
                        prefix = cnri
                        suffix = ''
                    if not suffix:
                        item['cnri_suffix_not_existed'] = True

                    if prefix != Handle().get_prefix():
                        error = _('Specified Prefix of {} is incorrect.') \
                            .format('CNRI')
                    if not re.search(WEKO_IMPORT_SUFFIX_PATTERN, suffix):
                        error = _(err_msg_suffix).format('CNRI')
        else:
            if item.get('status') == 'new' \
                    or item.get('is_change_identifier') or not cnri_set:
                if cnri:
                    error = _('{} cannot be set.').format('CNRI')
            else:
                pid_cnri = None
                try:
                    pid_cnri = WekoRecord.get_record_by_pid(item_id).pid_cnri
                    if pid_cnri:
                        if not cnri:
                            error = _('Please specify {}.').format('CNRI')
                        elif not pid_cnri.pid_value.endswith(str(cnri)):
                            error = _('Specified {} is different from existing'
                                      + ' {}.').format('CNRI', 'CNRI')
                    elif cnri:
                        error = _('Specified {} is different '
                                  + 'from existing {}.').format('CNRI', 'CNRI')
                except Exception as ex:
                    current_app.logger.error(
                        'item id: %s not found.' % item_id)
                    current_app.logger.error(ex)

        if error:
            item['errors'] = item['errors'] + [error] \
                if item.get('errors') else [error]
            item['errors'] = list(set(item['errors']))


def handle_check_doi_indexes(list_record):
    """Check restrict DOI with Indexes.

    :argument
        list_record -- {list} list record import.
    :return

    """
    err_msg_register_doi = _('When assigning a DOI to an item, it must be'
                             ' associated with an index whose index status is'
                             ' "Public" and Harvest Publishing is "Public".')
    err_msg_update_doi = _('Since the item has a DOI, it must be associated'
                           ' with an index whose index status is "Public"'
                           ' and whose Harvest Publishing is "Public".')
    for item in list_record:
        errors = []
        doi_ra = item.get('doi_ra')
        # Check DOI and Publish status:
        publish_status = item.get('publish_status')
        if doi_ra and publish_status == WEKO_IMPORT_PUBLISH_STATUS[1]:
            errors.append(
                _('You cannot keep an item private because it has a DOI.'))
        # Check restrict DOI with Indexes:
        index_ids = [str(idx) for idx in item['metadata'].get('path', [])]
        if doi_ra and check_restrict_doi_with_indexes(index_ids):
            if item.get('status') == 'new':
                errors.append(err_msg_register_doi)
            else:
                pid_doi = WekoRecord.get_record_by_pid(item.get('id')).pid_doi
                errors.append(
                    err_msg_update_doi if pid_doi else err_msg_register_doi)
        if errors:
            item['errors'] = item['errors'] + errors \
                if item.get('errors') else errors
            item['errors'] = list(set(item['errors']))


def handle_check_doi_ra(list_record):
    """Check DOI_RA.

    :argument
        list_record -- {list} list record import.
    :return

    """
    def check_existed(item_id, doi_ra):
        error = None
        try:
            pid = WekoRecord.get_record_by_pid(item_id).pid_recid
            identifier = IdentifierHandle(pid.object_uuid)
            _value, doi_type = identifier.get_idt_registration_data()

            if doi_type and doi_type[0] != doi_ra:
                error = _('Specified {} is different from '
                          + 'existing {}.').format('DOI_RA', 'DOI_RA')
        except Exception as ex:
            current_app.logger.error('item id: %s not found.' % item_id)
            current_app.logger.error(ex)
        return error

    for item in list_record:
        error = None
        item_id = str(item.get('id'))
        doi_ra = item.get('doi_ra')

        if item.get('doi') and not doi_ra:
            error = _('Please specify {}.').format('DOI_RA')
        elif doi_ra:
            if doi_ra not in WEKO_IMPORT_DOI_TYPE:
                error = _('DOI_RA should be set by one of JaLC'
                          + ', Crossref, DataCite, NDL JaLC.')
                item['ignore_check_doi_prefix'] = True
            elif item.get('is_change_identifier'):
                if not handle_doi_required_check(item):
                    error = _('PID does not meet the conditions.')
            else:
                if item.get('status') == 'new':
                    if item.get('doi'):
                        error = _('{} cannot be set.').format('DOI')
                    elif not handle_doi_required_check(item):
                        error = _('PID does not meet the conditions.')
                else:
                    error = check_existed(item_id, doi_ra)

        if error:
            item['errors'] = item['errors'] + [error] \
                if item.get('errors') else [error]
            item['errors'] = list(set(item['errors']))


def handle_check_doi(list_record):
    """Check DOI.

    :argument
        list_record -- {list} list record import.
    :return

    """
    for item in list_record:
        error = None
        item_id = str(item.get('id'))
        doi = item.get('doi')
        doi_ra = item.get('doi_ra')

        if item.get('is_change_identifier') \
                and doi_ra and not doi:
            error = _('Please specify {}.').format('DOI')
        elif doi_ra:
            if item.get('is_change_identifier'):
                if not doi:
                    error = _('Please specify {}.').format('DOI')
                else:
                    if len(doi) > 290:
                        error = _('The specified {} exceeds'
                                  + ' the maximum length.').format('DOI')
                    else:
                        split_doi = doi.split('/')
                        if len(split_doi) > 1:
                            prefix = '/'.join(split_doi[0:-1])
                            suffix = split_doi[-1]
                        else:
                            prefix = doi
                            suffix = ''
                        if not suffix:
                            item['doi_suffix_not_existed'] = True

                        if not item.get('ignore_check_doi_prefix') \
                                and prefix != get_doi_prefix(doi_ra):
                            error = _('Specified Prefix of {} is incorrect.') \
                                .format('DOI')
                        if not re.search(WEKO_IMPORT_SUFFIX_PATTERN, suffix):
                            error = _(err_msg_suffix).format('DOI')
            else:
                if item.get('status') == 'new':
                    if doi:
                        error = _('{} cannot be set.').format('DOI')
                else:
                    pid_doi = None
                    try:
                        pid_doi = WekoRecord.get_record_by_pid(item_id).pid_doi
                    except Exception as ex:
                        current_app.logger.error(
                            'item id: %s not found.' % item_id)
                        current_app.logger.error(ex)
                    if pid_doi:
                        if not doi:
                            error = _('Please specify {}.').format('DOI')
                        elif not pid_doi.pid_value.endswith(doi):
                            error = _('Specified {} is different from'
                                      + ' existing {}.').format('DOI', 'DOI')

        if error:
            item['errors'] = item['errors'] + [error] \
                if item.get('errors') else [error]
            item['errors'] = list(set(item['errors']))


def register_item_handle(item):
    """Register item handle (CNRI).

    :argument
        item    -- {object} Record item.
    :return
        response -- {object} Process status.

    """
    item_id = str(item.get('id'))
    record = WekoRecord.get_record_by_pid(item_id)
    pid = record.pid_recid
    pid_hdl = record.pid_cnri
    cnri = item.get('cnri')

    if item.get('is_change_identifier'):
        if item.get('cnri_suffix_not_existed'):
            suffix = "{:010d}".format(int(item_id))
            cnri = cnri[:-1] if cnri[-1] == '/' else cnri
            cnri += '/' + suffix
        if item.get('status') == 'new':
            register_hdl_by_handle(cnri, pid.object_uuid)
        else:
            if pid_hdl and not pid_hdl.pid_value.endswith(cnri):
                pid_hdl.delete()
                register_hdl_by_handle(cnri, pid.object_uuid)
            elif not pid_hdl:
                register_hdl_by_handle(cnri, pid.object_uuid)
    else:
        if item.get('status') == 'new':
            register_hdl_by_item_id(item_id, pid.object_uuid, get_url_root())


def prepare_doi_setting():
    """Prepare doi link with empty."""
    identifier_setting = get_identifier_setting('Root Index')
    if identifier_setting:
        text_empty = '<Empty>'
        if not identifier_setting.jalc_doi:
            identifier_setting.jalc_doi = text_empty
        if not identifier_setting.jalc_crossref_doi:
            identifier_setting.jalc_crossref_doi = text_empty
        if not identifier_setting.jalc_datacite_doi:
            identifier_setting.jalc_datacite_doi = text_empty
        if not identifier_setting.ndl_jalc_doi:
            identifier_setting.ndl_jalc_doi = text_empty
        # Semi-automatic suffix
        suffix_method = current_app.config.get(
            'IDENTIFIER_GRANT_SUFFIX_METHOD', IDENTIFIER_GRANT_SUFFIX_METHOD)
        if identifier_setting.suffix and suffix_method == 1:
            identifier_setting.suffix = '/' + identifier_setting.suffix
        else:
            identifier_setting.suffix = ''
        return identifier_setting


def get_doi_prefix(doi_ra):
    """Get DOI prefix."""
    identifier_setting = prepare_doi_setting()
    if identifier_setting:
        suffix = identifier_setting.suffix or ''
        if doi_ra == WEKO_IMPORT_DOI_TYPE[0]:
            return identifier_setting.jalc_doi + suffix
        elif doi_ra == WEKO_IMPORT_DOI_TYPE[1]:
            return identifier_setting.jalc_crossref_doi + suffix
        elif doi_ra == WEKO_IMPORT_DOI_TYPE[2]:
            return identifier_setting.jalc_datacite_doi + suffix
        elif doi_ra == WEKO_IMPORT_DOI_TYPE[3]:
            return identifier_setting.ndl_jalc_doi + suffix


def get_doi_link(doi_ra, data):
    """Get DOI link."""
    if doi_ra == WEKO_IMPORT_DOI_TYPE[0]:
        return data.get('identifier_grant_jalc_doi_link')
    elif doi_ra == WEKO_IMPORT_DOI_TYPE[1]:
        return data.get('identifier_grant_jalc_cr_doi_link')
    elif doi_ra == WEKO_IMPORT_DOI_TYPE[2]:
        return data.get('identifier_grant_jalc_dc_doi_link')
    elif doi_ra == WEKO_IMPORT_DOI_TYPE[3]:
        return data.get('identifier_grant_ndl_jalc_doi_link')


def prepare_doi_link(item_id):
    """Get DOI link."""
    item_id = '%010d' % int(item_id)
    identifier_setting = prepare_doi_setting()
    suffix = identifier_setting.suffix or ''

    return {
        'identifier_grant_jalc_doi_link':
            IDENTIFIER_GRANT_LIST[1][2] + '/'
            + identifier_setting.jalc_doi
            + suffix + '/' + item_id,
        'identifier_grant_jalc_cr_doi_link':
            IDENTIFIER_GRANT_LIST[2][2] + '/'
            + identifier_setting.jalc_crossref_doi
            + suffix + '/' + item_id,
        'identifier_grant_jalc_dc_doi_link':
            IDENTIFIER_GRANT_LIST[3][2] + '/'
            + identifier_setting.jalc_datacite_doi
            + suffix + '/' + item_id,
        'identifier_grant_ndl_jalc_doi_link':
            IDENTIFIER_GRANT_LIST[4][2] + '/'
            + identifier_setting.ndl_jalc_doi
            + suffix + '/' + item_id
    }


def register_item_doi(item):
    """Register item DOI.

    :argument
        item    -- {object} Record item.
    :return
        response -- {object} Process status.

    """
    def check_doi_duplicated(doi_ra, data):
        duplicated_doi = check_existed_doi(get_doi_link(doi_ra, data))
        if duplicated_doi.get('isWithdrawnDoi'):
            return 'is_withdraw_doi'
        if duplicated_doi.get('isExistDOI'):
            return 'is_duplicated_doi'

    item_id = str(item.get('id'))
    is_change_identifier = item.get('is_change_identifier')
    doi_ra = item.get('doi_ra')
    doi = item.get('doi')

    record_without_version = WekoRecord.get_record_by_pid(item_id)
    pid = record_without_version.pid_recid
    pid_doi = record_without_version.pid_doi

    lastest_version_id = item_id + '.' + \
        str(get_latest_version_id(item_id) - 1)
    pid_lastest = WekoRecord.get_record_by_pid(
        lastest_version_id).pid_recid

    data = None
    if is_change_identifier:
        if item.get('doi_suffix_not_existed'):
            suffix = "{:010d}".format(int(item_id))
            doi = doi[:-1] if doi[-1] == '/' else doi
            doi += '/' + suffix
        if doi_ra and doi:
            data = {
                'identifier_grant_jalc_doi_link':
                    IDENTIFIER_GRANT_LIST[1][2] + '/' + doi,
                'identifier_grant_jalc_cr_doi_link':
                    IDENTIFIER_GRANT_LIST[2][2] + '/' + doi,
                'identifier_grant_jalc_dc_doi_link':
                    IDENTIFIER_GRANT_LIST[3][2] + '/' + doi,
                'identifier_grant_ndl_jalc_doi_link':
                    IDENTIFIER_GRANT_LIST[4][2] + '/' + doi
            }
            if pid_doi and not pid_doi.pid_value.endswith(doi):
                pid_doi.delete()
            if not pid_doi or not pid_doi.pid_value.endswith(doi):
                doi_duplicated = check_doi_duplicated(doi_ra, data)
                if doi_duplicated:
                    raise Exception({'error_id': doi_duplicated})

                saving_doi_pidstore(
                    pid_lastest.object_uuid,
                    pid.object_uuid,
                    data,
                    WEKO_IMPORT_DOI_TYPE.index(doi_ra) + 1,
                    is_feature_import=True
                )
    else:
        if doi_ra and not doi:
            data = prepare_doi_link(item_id)
            doi_duplicated = check_doi_duplicated(doi_ra, data)
            if doi_duplicated:
                raise Exception({'error_id': doi_duplicated})
            saving_doi_pidstore(
                pid_lastest.object_uuid,
                pid.object_uuid,
                data,
                WEKO_IMPORT_DOI_TYPE.index(doi_ra) + 1,
                is_feature_import=True
            )

    if data:
        deposit = WekoDeposit.get_record(pid.object_uuid)
        deposit.commit()
        deposit.publish_without_commit()
        deposit = WekoDeposit.get_record(pid_lastest.object_uuid)
        deposit.commit()
        deposit.publish_without_commit()


def register_item_update_publish_status(item, status):
    """Update Publish Status.

    :argument
        item    -- {object} Record item.
        status  -- {str} Publish Status.
    :return
        response -- {object} Process status.

    """
    item_id = str(item.get('id'))
    lastest_version_id = item_id + '.' + \
        str(get_latest_version_id(item_id) - 1)

    update_publish_status(item_id, status)
    if lastest_version_id:
        update_publish_status(lastest_version_id, status)


def handle_doi_required_check(record):
    """DOI Validation check (Resource Type, Required, either required).

    :argument
        record    -- {object} Record item.
    :return
        true/false -- {object} Validation result.

    """
    record_data = {'item_type_id': record.get('item_type_id')}
    for key, value in record.get('metadata', {}).items():
        record_data[key] = {'attribute_value_mlt': [value]}

    if 'doi_ra' in record and record['doi_ra'] in WEKO_IMPORT_DOI_TYPE:
        error_list = item_metadata_validation(
            None, str(WEKO_IMPORT_DOI_TYPE.index(record['doi_ra']) + 1),
            record_data, True)
        if isinstance(error_list, str):
            return False
        if error_list and (error_list.get('required')
                           or error_list.get('either')
                           or error_list.get('pattern')):
            return False
        else:
            return True
    return False


def get_data_by_property(record, item_map, item_property):
    """
    Get data by property text.

    :param item_property: property value in item_map
    :return: error_list or None
    """
    key = item_map.get(item_property)
    data = []
    if not key:
        current_app.logger.warn(str(item_property)
                                + ' jpcoar:mapping is not correct')
        return None, None
    attribute = record['metadata'].get(key.split('.')[0])
    if not attribute:
        return None, key
    else:
        data_result = get_sub_item_value(
            attribute, key.split('.')[-1])
        if data_result:
            for value in data_result:
                data.append(value)
    return data, key


def handle_check_date(list_record):
    """Support validate three pattern: yyyy-MM-dd, yyyy-MM, yyyy.

    :argument
        list_record -- {list} list record import.
    :return

    """
    for record in list_record:
        errors = []
        date_iso_keys = []
        item_type = ItemTypes.get_by_id(id_=record.get(
            'item_type_id', 0), with_deleted=True)
        if item_type:
            item_type = item_type.render
            form = item_type.get('table_row_map', {}).get('form', {})
            date_iso_keys = get_list_key_of_iso_date(form)
        for key in date_iso_keys:
            _keys = key.split('.')
            attribute = record.get('metadata').get(_keys[0])
            if attribute:
                data_result = get_sub_item_value(attribute, _keys[-1])
                for value in data_result:
                    if not validation_date_property(value):
                        errors.append(
                            _('Please specify the date with any format of'
                              + ' YYYY-MM-DD, YYYY-MM, YYYY.'))
                        break
                if errors:
                    break
        # validate pubdate
        try:
            pubdate = record.get('metadata').get('pubdate')
            if pubdate and pubdate != datetime.strptime(pubdate, '%Y-%m-%d') \
                    .strftime('%Y-%m-%d'):
                raise Exception
        except Exception:
            errors.append(_('Please specify PubDate with YYYY-MM-DD.'))
        # validate file open_date
        open_date_err_msg = validation_file_open_date(record)
        if open_date_err_msg:
            errors.append(open_date_err_msg)

        if errors:
            record['errors'] = record['errors'] + errors \
                if record.get('errors') else errors
            record['errors'] = list(set(record['errors']))


def get_data_in_deep_dict(search_key, _dict={}):
    """
    Get data of key in a deep dictionary.

    :param search_key: key.
    :param _dict: Dict.
    :return: List of result. Ex: [{'tree_key': key, 'value': value}]
    """
    def add_parrent_key(parrent_key, idx=None, data={}):
        if idx is not None:
            data['tree_key'] = '{}[{}].{}'.format(
                parrent_key, idx, data.get('tree_key', ''))
        else:
            data['tree_key'] = '{}.{}'.format(
                parrent_key, data.get('tree_key', ''))
        return data
    result = []
    for key in _dict.keys():
        value = _dict.get(key)
        if key == search_key:
            result.append({'tree_key': key, 'value': value})
            break
        else:
            if isinstance(value, dict):
                data = get_data_in_deep_dict(search_key, value)
                if data:
                    result.extend(list(map(
                        partial(add_parrent_key, key, None), data)))
            elif isinstance(value, list):
                for idx, sub in enumerate(value):
                    if not isinstance(sub, dict):
                        continue
                    data = get_data_in_deep_dict(search_key, sub)
                    if data:
                        result.extend(list(map(
                            partial(add_parrent_key, key, idx), data)))
    return result


def validation_file_open_date(record):
    """
    Validate file open date.

    :param record: Record
    :return: error or None
    """
    open_date_values = get_data_in_deep_dict('dateValue',
                                             record.get('metadata', {}))
    for data in open_date_values:
        try:
            value = data.get('value', '')
            if value and value != datetime.strptime(value, '%Y-%m-%d') \
                    .strftime('%Y-%m-%d'):
                raise Exception
        except Exception:
            return _('Please specify Open Access Date with YYYY-MM-DD.')


def validation_date_property(date_str):
    """
    Validate item property is either required.

    :param properties: Property's keywords
    :return: error_list or None
    """
    for fmt in ('%Y-%m-%d', '%Y-%m', '%Y'):
        try:
            return date_str == datetime.strptime(date_str, fmt).strftime(fmt)
        except ValueError:
            pass
    return False


def get_list_key_of_iso_date(schemaform):
    """Get list key of iso date."""
    keys = []
    for item in schemaform:
        if not item.get('items'):
            if item.get('templateUrl', '') == DATE_ISO_TEMPLATE_URL:
                keys.append(item.get('key').replace('[]', ''))
        else:
            keys.extend(get_list_key_of_iso_date(item.get('items')))
    return keys


def get_current_language():
    """Get current language.

    :return:
    """
    current_lang = current_i18n.language
    # In case current_lang is not English
    # neither Japanese set default to English
    languages = \
        WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LANGUAGES
    if current_lang not in languages:
        current_lang = 'en'
    return current_lang


def get_change_identifier_mode_content():
    """Read data of change identifier mode base on language.

    :return:
    """
    file_extension = \
        WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_EXTENSION
    first_file_name = \
        WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FIRST_FILE_NAME
    folder_path = \
        WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LOCATION
    current_lang = get_current_language()
    file_name = first_file_name + "_" + current_lang + file_extension
    data = []
    try:
        with open(folder_path + file_name) as file:
            data = file.read().splitlines()
    except FileNotFoundError as ex:
        current_app.logger.error(str(ex))
    return data


def get_root_item_option(item_id, item, sub_form={'title_i18n': {}}):
    """Handle if is root item."""
    _id = '.metadata.{}'.format(item_id)
    _name = sub_form.get('title_i18n', {}).get(
        current_i18n.language) or item.get('title')

    _option = []
    if item.get('option').get('required'):
        _option.append('Required')
    if item.get('option').get('hidden'):
        _option.append('Hide')
    if item.get('option').get('multiple'):
        _option.append('Allow Multiple')
        _id += '[0]'
        _name += '[0]'

    return _id, _name, _option


def get_sub_item_option(key, schemaform):
    """Get sub-item option."""
    _option = None
    for item in schemaform:
        if not item.get('items'):
            if item.get('key') == key:
                _option = []
                if item.get('required'):
                    _option.append('Required')
                if item.get('isHide'):
                    _option.append('Hide')
                break
        else:
            _option = get_sub_item_option(
                key, item.get('items'))
            if _option is not None:
                break
    return _option


def check_sub_item_is_system(key, schemaform):
    """Check the sub-item is system."""
    is_system = None
    for item in schemaform:
        if not item.get('items'):
            if item.get('key') == key:
                is_system = False
                if item.get('readonly'):
                    is_system = True
                break
        else:
            is_system = check_sub_item_is_system(
                key, item.get('items'))
            if is_system is not None:
                break
    return is_system


def get_lifetime():
    """Get db life time."""
    try:
        db_lifetime = SessionLifetime.get_validtime()
        if db_lifetime is None:
            return WEKO_ADMIN_LIFETIME_DEFAULT
        else:
            return db_lifetime.lifetime * 60
    except BaseException:
        return 0


def get_system_data_uri(key_type, key):
    """Get uri from key of System item."""
    if key_type == WEKO_IMPORT_SYSTEM_ITEMS[0]:
        return RESOURCE_TYPE_URI.get(key, None)
    elif key_type == WEKO_IMPORT_SYSTEM_ITEMS[1]:
        return VERSION_TYPE_URI.get(key, None)
    elif key_type == WEKO_IMPORT_SYSTEM_ITEMS[2]:
        return ACCESS_RIGHT_TYPE_URI.get(key, None)


def handle_fill_system_item(list_record):
    """Auto fill data into system item.

    :argument
        list_record -- {list} list record import.
    :return

    """
    def recursive_sub(keys, node, uri_key, current_type):
        current_app.logger.debug("recursive_sub")
        
        current_app.logger.debug(keys)
        current_app.logger.debug(node)
        current_app.logger.debug(uri_key)
        current_app.logger.debug(current_type)
        
        if isinstance(node, list):
            for sub_node in node:
                recursive_sub(keys[1:], sub_node, uri_key, current_type)
        elif isinstance(node, dict):
            if len(keys) > 1:
                recursive_sub(keys[1:], node.get(keys[0]),
                              uri_key, current_type)
            else:
                if len(keys) > 0:
                    type_data = node.get(keys[0])
                    uri = get_system_data_uri(current_type, type_data)
                    if uri is not None:
                        node[uri_key] = uri

    item_type_id = None
    item_map = None
    for item in list_record:
        if item_type_id != item['item_type_id']:
            item_type_id = item['item_type_id']
            item_map = get_mapping(Mapping.get_record(
                item_type_id), 'jpcoar_mapping')

        # Resource Type
        _, resourcetype_key = get_data_by_property(
            item, item_map, "type.@value")
        _, resourceuri_key = get_data_by_property(
            item, item_map, "type.@attributes.rdf:resource")
        if resourcetype_key and resourceuri_key:
            recursive_sub(resourcetype_key.split('.'),
                          item['metadata'],
                          resourceuri_key.split('.')[-1],
                          WEKO_IMPORT_SYSTEM_ITEMS[0])

        # Version Type
        _, versiontype_key = get_data_by_property(
            item, item_map, "versiontype.@value")
        _, versionuri_key = get_data_by_property(
            item, item_map, "versiontype.@attributes.rdf:resource")
        current_app.logger.debug("Version Type")
        if versiontype_key and versionuri_key:
            current_app.logger.debug(versiontype_key)
            current_app.logger.debug(versionuri_key)
            recursive_sub(versiontype_key.split('.'),
                          item['metadata'],
                          versionuri_key.split('.')[-1],
                          WEKO_IMPORT_SYSTEM_ITEMS[1])

        # Access Right
        _, accessRights_key = get_data_by_property(
            item, item_map, "accessRights.@value")
        _, accessRightsuri_key = get_data_by_property(
            item, item_map, "accessRights.@attributes.rdf:resource")
        current_app.logger.debug("Access Right")
        if accessRights_key and accessRightsuri_key:
            current_app.logger.debug(accessRights_key)
            current_app.logger.debug(accessRightsuri_key)
            recursive_sub(accessRights_key.split('.'),
                          item['metadata'],
                          accessRightsuri_key.split('.')[-1],
                          WEKO_IMPORT_SYSTEM_ITEMS[2])


def get_thumbnail_key(item_type_id=0):
    """Get thumbnail key.

    :argument
        item_type_id -- {int} item type id.
    :return

    """
    item_type = ItemTypes.get_by_id(id_=item_type_id, with_deleted=True)
    if item_type:
        item_type = item_type.render
        schema = item_type.get('schemaeditor', {}).get('schema', {})
        for key, item in schema.items():
            if item.get('properties') \
                    and item['properties'].get('subitem_thumbnail'):
                return key


def handle_check_thumbnail_file_type(thumbnail_paths):
    """Check thumbnail file type.

    :argument
        thumbnail_paths -- {list} thumbnails path.
    :return
        error -- {str} error message.
    """
    error = _('Please specify the image file(gif, jpg, jpe, jpeg,'
              + ' png, bmp, tiff, tif) for the thumbnail.')
    for path in thumbnail_paths:
        if not path:
            continue
        file_extend = path.split('.')[-1]
        if file_extend not in WEKO_IMPORT_THUMBNAIL_FILE_TYPE:
            return error


def handle_check_metadata_not_existed(str_keys, item_type_id=0):
    """Check and get list metadata not existed in item type.

    :argument
        str_keys -- {list} list key.
        item_type_id -- {int} item type id.
    :return

    """
    result = []
    ids = handle_get_all_id_in_item_type(item_type_id)
    ids = list(map(lambda x: re.sub(r'\[\d+\]', '', x), ids))
    for str_key in str_keys:
        if str_key.startswith('.metadata.'):
            pre_key = re.sub(r'\[\d+\]', '', str_key)
            if pre_key != '.metadata.path' and pre_key not in ids \
                    and 'iscreator' not in pre_key:
                result.append(str_key.replace('.metadata.', ''))
    return result


def handle_get_all_sub_id_and_name(
        items, root_id=None, root_name=None, form=[]):
    """Get all sub id, sub name of root item with full-path.

    :argument
        items - {dict} sub items.
        root_id -- {str} root id.
        root_name -- {str} root name.
    :return
        ids - {list} full-path of ids.
        names - {list} full-path of names.
    """
    ids, names = [], []
    for key in sorted(items.keys()):
        if key == 'iscreator':
            continue
        item = items.get(key)
        sub_form = next(
            (x for x in form if key in x.get('key', '')),
            {'title_i18n': {}})
        title = sub_form.get('title_i18n', {}).get(
            current_i18n.language) or item.get('title')
        if item.get('items') and item.get('items').get('properties'):
            _ids, _names = handle_get_all_sub_id_and_name(
                item.get('items').get('properties'),
                form=sub_form.get('items', []))
            ids += [key + '[0].' + _id for _id in _ids]
            names += [title + '[0].' + _name
                      for _name in _names]
        elif item.get('type') == 'object' and item.get('properties'):
            _ids, _names = handle_get_all_sub_id_and_name(
                item.get('properties'), form=sub_form.get('items', []))
            ids += [key + '.' + _id for _id in _ids]
            names += [title + '.' + _name
                      for _name in _names]
        elif item.get('format') == 'checkboxes':
            ids.append(key + '[0]')
            names.append(title + '[0]')
        else:
            ids.append(key)
            names.append(title)

    if root_id:
        ids = [root_id + '.' + _id for _id in ids]
    if root_name:
        names = [root_name + '.' + _name
                 for _name in names]

    return ids, names


def handle_get_all_id_in_item_type(item_type_id):
    """Get all id of item with full-path.

    :argument
        item_type_id - {str} item type id.
    :return
        ids - {list} full-path of ids.
    """
    result = []
    item_type = ItemTypes.get_by_id(id_=item_type_id, with_deleted=True)
    if item_type:
        item_type = item_type.render
        meta_system = [
            item_key for item_key in item_type.get('meta_system', {})]
        schema = item_type.get(
            'table_row_map', {}).get('schema', {}).get('properties', {})

        for key, item in schema.items():
            if key not in meta_system:
                new_key = '.metadata.{}{}'.format(
                    key, '[0]' if item.get('items') else '')
                if not item.get('properties') and not item.get('items'):
                    result.append(new_key)
                else:
                    sub_items = item.get('properties') if item.get(
                        'properties') else item.get('items').get('properties')
                    result += handle_get_all_sub_id_and_name(
                        sub_items, new_key)[0]
    return result


def handle_check_consistence_with_item_type(item_type_id, keys):
    """Check consistence between tsv and item type.

    :argument
        item_type_id - {str} item type id.
        keys - {list} data from line 2 of tsv file.
    :return
        ids - {list} ids is not consistent.
    """
    result = []
    ids = handle_get_all_id_in_item_type(item_type_id)
    clean_ids = list(map(lambda x: re.sub(r'\[\d+\]', '', x), ids))
    for _key in keys:
        if re.sub(r'\[\d+\]', '', _key) in clean_ids \
                and re.sub(r'\[\d+\]', '[0]', _key) not in ids:
            result.append(_key)

    clean_keys = list(map(lambda x: re.sub(r'\[\d+\]', '', x), keys))
    for _id in ids:
        if re.sub(r'\[\d+\]', '', _id) not in clean_keys:
            result.append(_id)

    return list(set(result))


def handle_check_duplication_item_id(ids: list):
    """Check duplication of item id in tsv file.

    :argument
        ids - {list} data from line 2 of tsv file.
    :return
        ids - {list} ids is duplication.
    """
    result = []
    for element in ids:
        if element is not '' and ids.count(element) > 1:
            result.append(element)
    return list(set(result))


def export_all(root_url):
    """Gather all the item data and export and return as a JSON or BIBTEX.

    Parameter
        path is the path if file temparory
        post_data is the data items
    :return: JSON, BIBTEX
    """
    from weko_items_ui.utils import make_stats_tsv_with_permission, \
        package_export_file

    def _itemtype_name(name):
        """Check a list of allowed characters in filenames."""
        return re.sub(r'[\/:*"<>|\s]', '_', name)

    def _write_tsv_files(item_types_data, export_path):
        """Write TSV data to files.

        @param item_types_data:
        @param export_path:
        @param list_item_role:
        @return:
        """
        permissions = dict(
            permission_show_hide=lambda a: True,
            check_created_id=lambda a: True,
            hide_meta_data_for_role=lambda a: True,
            current_language=lambda: True
        )
        for item_type_id in item_types_data:
            try:
                headers, records = make_stats_tsv_with_permission(
                    item_type_id,
                    item_types_data[item_type_id]['recids'],
                    item_types_data[item_type_id]['data'],
                    permissions)
                keys, labels, is_systems, options = headers
                item_types_data[item_type_id]['recids'].sort()
                item_types_data[item_type_id]['keys'] = keys
                item_types_data[item_type_id]['labels'] = labels
                item_types_data[item_type_id]['is_systems'] = is_systems
                item_types_data[item_type_id]['options'] = options
                item_types_data[item_type_id]['data'] = records
                item_type_data = item_types_data[item_type_id]

                tsv_full_path = '{}/{}.tsv'.format(export_path,
                                                   item_type_data.get('name'))
                with open(tsv_full_path, 'w') as file:
                    tsv_output = package_export_file(item_type_data)
                    file.write(tsv_output.getvalue())
            except Exception as ex:
                current_app.logger.error(ex)
                continue

    temp_path = tempfile.TemporaryDirectory(
        prefix=current_app.config['WEKO_ITEMS_UI_EXPORT_TMP_PREFIX'])
    try:
        export_path = temp_path.name + '/' + \
            datetime.utcnow().strftime("%Y%m%d%H%M%S")
        os.makedirs(export_path, exist_ok=True)

        # get all record id
        recids = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            status=PIDStatus.REGISTERED).all()

        record_ids = [
            recid.pid_value for recid in recids if recid.pid_value.isdigit()]
        item_types_data = {}

        for recid in record_ids:
            record = WekoRecord.get_record_by_pid(recid)
            item_type = ItemTypes.get_by_id(record.get('item_type_id'))
            item_type_id = str(record.get('item_type_id'))

            if not item_type:
                current_app.logger.error('Corrupted Item: {}'.format(recid))
                continue
            elif not item_types_data.get(item_type_id):
                item_type_name = _itemtype_name(
                    item_type.item_type_name.name)
                item_types_data[item_type_id] = {
                    'item_type_id': item_type_id,
                    'name': '{}({})'.format(
                        item_type_name,
                        item_type_id),
                    'root_url': root_url,
                    'jsonschema': 'items/jsonschema/' + item_type_id,
                    'keys': [],
                    'labels': [],
                    'recids': [],
                    'data': {},
                }

            item_types_data[item_type_id]['recids'].append(recid)
            item_types_data[item_type_id]['data'][recid] = record

        # Create export info file
        _write_tsv_files(item_types_data, export_path)

        # Create bag
        bagit.make_bag(export_path)
        shutil.make_archive(export_path, 'zip', export_path)
        with open(export_path + '.zip', 'rb') as file:
            src = FileInstance.create()
            src.set_contents(
                file, default_location=Location.get_default().uri)
        db.session.commit()

        # Delete old file
        _task_config = current_app.config['WEKO_SEARCH_UI_BULK_EXPORT_URI']
        _cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
            format(name=_task_config)
        prev_uri = get_redis_cache(_cache_key)
        if (prev_uri):
            delete_exported(prev_uri, _cache_key)
        return src.uri if src else None
    except Exception as ex:
        db.session.rollback()
        current_app.logger.error(ex)


def delete_exported(uri, cache_key):
    """Delete File instance after time in file config."""
    from simplekv.memory.redisstore import RedisStore
    try:
        with db.session.begin_nested():
            file_instance = FileInstance.get_by_uri(uri)
            file_instance.delete()
        datastore = RedisStore(redis.StrictRedis.from_url(
            current_app.config['CACHE_REDIS_URL']))
        if datastore.redis.exists(cache_key):
            datastore.delete(cache_key)
        db.session.commit()
    except Exception as ex:
        current_app.logger.error(ex)


def cancel_export_all():
    """Cancel Process Share_task Export ALL with revoke.

    Return:     True:   Cancel Successful.
                  No:     Error
    """
    cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
        format(name=WEKO_SEARCH_UI_BULK_EXPORT_TASK)
    try:
        task_id = get_redis_cache(cache_key)
        task_status = get_export_status()

        if task_status:
            revoke(task_id, terminate=True)

        return True
    except Exception as ex:
        current_app.logger.error(ex)
        return False


def get_export_status():
    """Get Share_task Export ALL status.

    Return:     True:   Otthers
               False:  Success / Failed / Revoked
    """
    cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
        format(name=WEKO_SEARCH_UI_BULK_EXPORT_TASK)
    cache_uri = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
        format(name=WEKO_SEARCH_UI_BULK_EXPORT_URI)
    export_status = False
    download_uri = None
    try:
        task_id = get_redis_cache(cache_key)
        download_uri = get_redis_cache(cache_uri)
        if (task_id):
            task = AsyncResult(task_id)
            status_cond = (task.successful() or task.failed()
                           or task.state == 'REVOKED')
            export_status = True if not status_cond else False
    except Exception as ex:
        current_app.logger.error(ex)
        export_status = False
    return export_status, download_uri


def handle_check_item_is_locked(item):
    """Check an item is being edit or deleted.

    :argument
        item - {dict} Item metadata.
    :return
        response - {dict} check status.
    """
    from weko_items_ui.utils import check_item_is_being_edit, \
        check_item_is_deleted
    item_id = str(item.get('id'))
    error_id = None

    if check_item_is_deleted(item_id):
        error_id = 'item_is_deleted'
    else:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value=item_id
        ).first()
        if check_item_is_being_edit(pid):
            error_id = 'item_is_being_edit'

    if error_id:
        raise Exception({
            'error_id': error_id
        })


def handle_remove_es_metadata(item):
    """Remove es metadata.

    :argument
        item - {dict} Item metadata.
    """
    try:
        item_id = item.get('id')
        pid = WekoRecord.get_record_by_pid(item_id).pid_recid
        pid_lastest = WekoRecord.get_record_by_pid(
            item_id + '.' + str(get_latest_version_id(item_id) - 1)).pid_recid
        deposit = WekoDeposit.get_record(pid.object_uuid)
        deposit.indexer.delete(deposit)
        deposit = WekoDeposit.get_record(pid_lastest.object_uuid)
        deposit.indexer.delete(deposit)
    except Exception as ex:
        current_app.logger.error(ex)


def check_index_access_permissions(func):
    """Check index access permission.

    Args:
        func (func): Function.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        search_type = request.args.get('search_type', WEKO_SEARCH_TYPE_DICT[
            'FULL_TEXT'])
        if search_type == WEKO_SEARCH_TYPE_DICT['INDEX']:
            cur_index_id = request.args.get('q', '0')
            if not check_index_permissions(None, cur_index_id):
                if not current_user.is_authenticated:
                    return current_app.login_manager.unauthorized()
                else:
                    abort(403)
        return func(*args, **kwargs)

    return decorated_view


def handle_check_file_metadata(list_record, data_path):
    """Check file contents, thumbnails metadata.

    :argument
        list_record -- {list} list record import.
        data_path   -- {str} paths of file content.
    :return

    """
    for record in list_record:
        errors, warnings = handle_check_file_content(record, data_path)
        _errors, _warnings = handle_check_thumbnail(record, data_path)
        errors += _errors
        warnings += _warnings

        if errors:
            record['errors'] = record['errors'] + errors \
                if record.get('errors') else errors
        if warnings:
            record['warnings'] = record['warnings'] + warnings \
                if record.get('warnings') else warnings


def handle_check_file_path(paths, data_path, is_new=False,
                           is_thumbnail=False, is_single_thumbnail=False):
    """Check file path.

    :argument
        record -- {dict} record import.
        data_path   -- {str} paths of file content.
        is_new   -- {bool} Is new?
        is_thumbnail   -- {bool} Is thumbnail?
        is_single_thumbnail   -- {bool} Is single thumbnail?
    :return
        error -- {str} Error.
        warning -- {str} Warning.
    """
    def prepare_idx_msg(idxs, msg_path_idx_type):
        if is_single_thumbnail:
            return msg_path_idx_type
        else:
            return ', '.join(
                [(msg_path_idx_type + '[{}]').format(idx) for idx in idxs])

    error = None
    warning = None
    idx_errors = []
    idx_warnings = []
    for idx, path in enumerate(paths):
        if not path:
            continue
        if not os.path.isfile(data_path + '/' + path):
            if is_new:
                idx_errors.append(str(idx))
            else:
                idx_warnings.append(str(idx))

    msg_path_idx_type = '.thumbnail_path' if is_thumbnail else '.file_path'
    if idx_errors:
        error = _('The file specified in ({}) does not exist.') \
            .format(prepare_idx_msg(idx_errors, msg_path_idx_type))
    if idx_warnings:
        warning = _('The file specified in ({}) does not exist.<br/>'
                    'The file will not be updated. '
                    'Update only the metadata with tsv contents.') \
            .format(prepare_idx_msg(idx_warnings, msg_path_idx_type))

    return error, warning


def handle_check_file_content(record, data_path):
    """Check file contents metadata.

    :argument
        record -- {dict} record import.
        data_path   -- {str} paths of file content.
    :return
        errors -- {list} List errors.
        warnings -- {list} List warnings.
    """
    errors = []
    warnings = []

    file_paths = record.get('file_path', [])
    # check consistence between file_path and filename
    filenames = get_filenames_from_metadata(record['metadata'])
    errors.extend(handle_check_filename_consistence(file_paths, filenames))

    # check if file_path exists
    error, warning = handle_check_file_path(
        file_paths, data_path, record['status'] == 'new')
    if error:
        errors.append(error)
    if warning:
        warnings.append(warning)

    return errors, warnings


def handle_check_thumbnail(record, data_path):
    """Check thumbnails metadata.

    :argument
        record -- {dict} record import.
        data_path   -- {str} paths of file content.
    :return
        errors -- {list} List errors.
        warnings -- {list} List warnings.
    """
    errors = []
    warnings = []
    is_single = False
    thumbnail_paths = record.get('thumbnail_path', [])
    if isinstance(thumbnail_paths, str):
        thumbnail_paths = [thumbnail_paths]
        is_single = True

    # check file type
    error = handle_check_thumbnail_file_type(thumbnail_paths)
    if error:
        errors.append(error)

    # check thumbnails path
    error, warning = handle_check_file_path(
        thumbnail_paths, data_path, record['status'] == 'new', True, is_single)
    if error:
        errors.append(error)
    if warning:
        warnings.append(warning)

    return errors, warnings


def get_key_by_property(record, item_map, item_property):
    """Get data by property text.

    :param item_map:
    :param record:
    :param item_property: property value in item_map
    :return: error_list or None
    """
    key = item_map.get(item_property)
    data = []
    if not key:
        current_app.logger.error(str(item_property) + ' jpcoar:mapping '
                                                      'is not correct')
        return None
    return key


def get_data_by_propertys(record, item_map, item_property):
    """Get data by property text.

    :param item_map:
    :param record:
    :param item_property: property value in item_map
    :return: error_list or None
    """
    key = item_map.get(item_property)
    data = []
    if not key:
        current_app.logger.error(str(item_property) + ' jpcoar:mapping '
                                                      'is not correct')
        return None, None
    attribute = record['_item_metadata'].get(key.split('.')[0])
    if not attribute:
        return None, key
    else:
        data_result = get_sub_item_value(
            attribute, key.split('.')[-1])
        if data_result:
            for value in data_result:
                data.append(value)
    return data, key


def get_filenames_from_metadata(metadata):
    """Check thumbnails metadata.

    :argument
        metadata -- {dict} record metadata.
    :return
        filenames -- {list} List filename data.
    """
    filenames = []
    file_meta_ids = []
    for key, val in metadata.items():
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict) and 'filename' in item:
                    file_meta_ids.append(key)
                    break

    count = 0
    for _id in file_meta_ids:
        for file in metadata[_id]:
            data = {
                'id': '.metadata.{}[{}].filename'.format(_id, count),
                'filename': file.get('filename', '')
            }
            if not file.get('filename'):
                del file['filename']
            filenames.append(data)
            count += 1

        new_file_metadata = list(filter(lambda x: x, metadata[_id]))
        if new_file_metadata:
            metadata[_id] = new_file_metadata
        else:
            del metadata[_id]

    return filenames


def handle_check_filename_consistence(file_paths, meta_filenames):
    """Check thumbnails metadata.

    :argument
        file_paths -- {list} List file_path.
        meta_filenames   -- {list} List filename from metadata.
    :return
        errors -- {list} List errors.
    """
    errors = []
    msg = _('The file name specified in {} and {} do not match.')
    for idx, path in enumerate(file_paths):
        meta_filename = meta_filenames[idx]
        if path and path.split('/')[-1] != meta_filename['filename']:
            errors.append(msg.format(
                'file_path[{}]'.format(idx), meta_filename['id']))

    return errors
