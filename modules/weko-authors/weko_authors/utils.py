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

"""Utils for weko-authors."""

import base64
import csv
import chardet
import io
import sys
import tempfile
import traceback
from time import sleep
from copy import deepcopy
from functools import reduce
from operator import getitem
from sys import stdout
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from flask import current_app
from flask_babelex import gettext as _
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.models import FileInstance, Location
from invenio_indexer.api import RecordIndexer

from weko_authors.contrib.validation import validate_by_extend_validator, \
    validate_external_author_identifier, validate_map, validate_required

from .api import WekoAuthors
from .config import WEKO_AUTHORS_FILE_MAPPING, \
    WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY, WEKO_AUTHORS_EXPORT_CACHE_URL_KEY
from .models import AuthorsPrefixSettings, AuthorsAffiliationSettings


def get_author_prefix_obj(scheme):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsPrefixSettings).filter(
            AuthorsPrefixSettings.scheme == scheme).one_or_none()
    except Exception as ex:
        current_app.logger.debug(ex)
    return None

def get_author_affiliation_obj(scheme):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsAffiliationSettings).filter(
            AuthorsAffiliationSettings.scheme == scheme).one_or_none()
    except Exception as ex:
        current_app.logger.debug(ex)
    return None


def check_email_existed(email: str):
    """Check email has existed.

    :param email: email string.
    :returns: author info.
    """
    body = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"gather_flg": 0}},
                    {"term": {"emailInfo.email.raw": email}}
                ]
            }
        }
    }

    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=body
    )

    if result['hits']['total']:
        return {
            'email': email,
            'author_id': result['hits']['hits'][0]['_source']['pk_id']
        }
    else:
        return {
            'email': email,
            'author_id': ''
        }


def get_export_status():
    """Get export status from cache."""
    return current_cache.get(WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY) or {}


def set_export_status(start_time=None, task_id=None):
    """Set export status into cache."""
    data = get_export_status() or dict()
    if start_time:
        data['start_time'] = start_time
    if task_id:
        data['task_id'] = task_id

    current_cache.set(WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY, data, timeout=0)
    return data


def delete_export_status():
    """Delete export status."""
    current_cache.delete(WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY)


def get_export_url():
    """Get exported info from cache."""
    return current_cache.get(WEKO_AUTHORS_EXPORT_CACHE_URL_KEY) or {}


def save_export_url(start_time, end_time, file_uri):
    """Save exported info into cache."""
    data = dict(
        start_time=start_time,
        end_time=end_time,
        file_uri=file_uri
    )

    current_cache.set(WEKO_AUTHORS_EXPORT_CACHE_URL_KEY, data, timeout=0)
    return data

def handle_exception(ex, attempt, retrys, interval):
    """Handle exceptions during the export process."""
    current_app.logger.error(ex)
    # 最後のリトライの場合は例外をraise
    if attempt == retrys - 1:
        return 0
    current_app.logger.info(f"Connection failed, retrying in {interval} seconds...")
    sleep(interval)

def export_authors():
    """Export all authors."""
    file_uri = None
    try:
        mappings = deepcopy(WEKO_AUTHORS_FILE_MAPPING)
        authors = WekoAuthors.get_all(with_deleted=False, with_gather=False)
        schemes = WekoAuthors.get_identifier_scheme_info()
        row_header, row_label_en, row_label_jp, row_data = \
            WekoAuthors.prepare_export_data(mappings, authors, schemes)

        # write file data to a stream
        file_io = io.StringIO()
        if current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower() == 'csv':
            writer = csv.writer(file_io, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\n')
        else:
            writer = csv.writer(file_io, delimiter='\t',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerows([row_header, row_label_en, row_label_jp, *row_data])
        reader = io.BufferedReader(io.BytesIO(
            file_io.getvalue().encode("utf-8-sig")))

        # save data into location
        cache_url = get_export_url()
        if not cache_url:
            file = FileInstance.create()
            file.set_contents(
                reader, default_location=Location.get_default().uri)
        else:
            file = FileInstance.get_by_uri(cache_url['file_uri'])
            file.writable = True
            file.set_contents(reader)

        file_uri = file.uri if file else None
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        current_app.logger.error(ex)
        traceback.print_exc(file=stdout)
    current_cache.set(
        current_app.config.get("WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY"),
        "author_db",
        timeout=0
    )
    
    return file_uri

def export_prefix(target):
    file_uri = None
    retrys = current_app.config["WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY"]
    interval = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
    target_db_name = "author_prefix_settings" if target == "id_prefix" else "author_affiliation_settings"
    row_first = [f"#{target_db_name}"]
    row_header = ["#scheme", "name", "url", "is_deleted"]
    row_label_en = ["#Scheme", "Name", "URL", "Delete Flag"]
    row_label_jp = ["#スキーム", "名前", "URL", "削除フラグ"]

    for attempt in range(retrys):
        try:
            if target == "id_prefix":
                prefix = WekoAuthors.get_id_prefix_all()
            elif target == "affiliation_id":
                prefix = WekoAuthors.get_affiliation_id_all()
            row_data = WekoAuthors.prepare_export_prefix(target, prefix)
            # write file data to a stream
            file_io = io.StringIO()
            if current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower() == 'csv':
                writer = csv.writer(file_io, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL,
                                    lineterminator='\n')
            else:
                writer = csv.writer(file_io, delimiter='\t',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows([row_first, row_header, row_label_en, row_label_jp, *row_data])
            reader = io.BufferedReader(io.BytesIO(
                file_io.getvalue().encode("utf-8-sig")))

            # save data into location
            cache_url = get_export_url()
            if not cache_url:
                file = FileInstance.create()
                file.set_contents(
                    reader, default_location=Location.get_default().uri)
            else:
                file = FileInstance.get_by_uri(cache_url['file_uri'])
                file.writable = True
                file.set_contents(reader)
            file_uri = file.uri if file else None
            db.session.commit()
            current_cache.set(
                current_app.config.get("WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY"),
                target,
                timeout=0
            )
            break
        except SQLAlchemyError as ex:
            handle_exception(ex, attempt, retrys, interval)
        except RedisError as ex:
            handle_exception(ex, attempt, retrys, interval)
        except TimeoutError as ex:
            handle_exception(ex, attempt, retrys, interval)
    return file_uri

def check_file_name(export_target):
    file_base_name = ""
    if export_target == "author_db":
        file_base_name = current_app.config.get('WEKO_AUTHORS_EXPORT_FILE_NAME')
    elif export_target == "id_prefix":
        file_base_name = current_app.config.get('WEKO_AUTHORS_ID_PREFIX_EXPORT_FILE_NAME')
    elif export_target == "affiliation_id":
        file_base_name = current_app.config.get('WEKO_AUTHORS_AFFILIATION_EXPORT_FILE_NAME')
    return file_base_name

def check_import_data(file_name: str, file_content: str):
    """Validation importing tsv/csv file.

    :argument
        file_name -- file name.
        file_content -- content file's name.
    :return
        return       -- check information.
    """
    tmp_prefix = current_app.config['WEKO_AUTHORS_IMPORT_TMP_PREFIX']
    temp_file = tempfile.NamedTemporaryFile(prefix=tmp_prefix)
    result = {}

    try:
        temp_file.write(base64.b64decode(file_content))
        temp_file.flush()

        flat_mapping_all, flat_mapping_ids = flatten_authors_mapping(
            WEKO_AUTHORS_FILE_MAPPING)
        file_format = file_name.split('.')[-1].lower()
        file_data = unpackage_and_check_import_file(
            file_format, file_name, temp_file.name, flat_mapping_ids)
        result['list_import_data'] = validate_import_data(
            file_format, file_data, flat_mapping_ids, flat_mapping_all)
    except Exception as ex:
        error = _('Internal server error')
        if isinstance(ex, UnicodeDecodeError):
            error = ex.reason
        elif ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_msg'):
            error = ex.args[0].get('error_msg')
        result['error'] = error
        current_app.logger.error('-' * 60)
        traceback.print_exc(file=sys.stdout)
        current_app.logger.error('-' * 60)

    return result

def check_import_data_for_prefix(target, file_name: str, file_content: str):
    """id_prefixかaffiliation_idのインポート用 tsv/csvファイルをバリデーションチェックする.
    :argument
        file_name -- file name.
        file_content -- content file's name.
    :return
        return       -- check information.
    """
    tmp_prefix = current_app.config['WEKO_AUTHORS_IMPORT_TMP_PREFIX']
    temp_file = tempfile.NamedTemporaryFile(prefix=tmp_prefix)
    result = {}
    print("check_import_data_for_prefix")
    try:
        temp_file.write(base64.b64decode(file_content))
        temp_file.flush()

        file_format = file_name.split('.')[-1].lower()
        file_data = unpackage_and_check_import_file_for_prefix(
            file_format, file_name, temp_file.name)
        result['list_import_data'] = validate_import_data_for_prefix(file_data, target)
    except Exception as ex:
        error = _('Internal server error')
        if isinstance(ex, UnicodeDecodeError):
            error = ex.reason
        elif ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_msg'):
            error = ex.args[0].get('error_msg')
        result['error'] = error
        current_app.logger.error('-' * 60)
        traceback.print_exc(file=sys.stdout)
        current_app.logger.error('-' * 60)

    return result

def getEncode(filepath):
    """
    getEncode [summary]

    [extended_summary]

    Args:
        filepath ([type]): [description]

    Returns:
        [type]: [description]
    """
    with open(filepath, mode='rb') as fr:
        b = fr.read()
    enc = chardet.detect(b)
    return enc.get('encoding', 'utf-8-sig')


def unpackage_and_check_import_file(file_format, file_name, temp_file, mapping_ids):
    """Unpackage and check format of import file.

    Args:
        file_format (str): File format.
        file_name (str): File uploaded name.
        temp_file (str): Temp file path.
        mapping_ids (list): List only mapping ids.

    Returns:
        list: Tsv data.

    """
    from weko_search_ui.utils import handle_check_consistence_with_mapping, \
        handle_check_duplication_item_id, parse_to_json_form
    header = []
    file_data = []
    current_app.logger.debug("temp_file:{}".format(temp_file))
    enc = getEncode(temp_file)
    with open(temp_file, 'r', newline="", encoding=enc) as file:
        if file_format == 'csv':
            file_reader = csv.reader(file, dialect='excel', delimiter=',')
        else:
            file_reader = csv.reader(file, dialect='excel', delimiter='\t')
        try:
            for num, data_row in enumerate(file_reader, start=1):
                if num == 1:
                    header = data_row
                    header[0] = header[0].replace('#', '', 1)
                    # remove BOM
                    # header[0] = header[0].replace('\ufeff', '')
                    duplication_item_ids = \
                        handle_check_duplication_item_id(header)
                    if duplication_item_ids:
                        msg = _(
                            'The following metadata keys are duplicated.'
                            '<br/>{}')
                        raise Exception({
                            'error_msg':
                                msg.format('<br/>'.join(duplication_item_ids))
                        })

                    not_consistent_list = \
                        handle_check_consistence_with_mapping(
                            mapping_ids, header)
                    if not_consistent_list:
                        msg = _('Specified item does not consistency '
                                'with DB item.<br/>{}')
                        raise Exception({
                            'error_msg': msg.format(
                                '<br/>'.join(not_consistent_list))
                        })
                elif num in [2, 3] and data_row[0].startswith('#'):
                    continue
                elif num > 3:
                    data_parse_metadata = parse_to_json_form(
                        zip(header, data_row),
                        include_empty=True
                    )

                    if not data_parse_metadata:
                        raise Exception({
                            'error_msg': _('Cannot read {} file correctly.').format(file_format.upper())
                        })

                    file_data.append(dict(**data_parse_metadata))

            if not file_data:
                raise Exception({
                    'error_msg': _('There is no data to import.')
                })
        except UnicodeDecodeError as ex:
            ex.reason = _('{} could not be read. Make sure the file'
                          + ' format is {} and that the file is'
                          + ' UTF-8 encoded.').format(file_name, file_format.upper())
            raise ex
        except Exception as ex:
            raise ex

    return file_data


def validate_import_data(file_format, file_data, mapping_ids, mapping):
    """Validate import data.

    Args:
        file_format (str): File format.
        file_data (list): Author data from tsv/csv.
        mapping_ids (list): List only mapping ids.
        mapping (list): List mapping.
    """
    authors_prefix = {}
    with db.session.no_autoflush:
        authors_prefix = AuthorsPrefixSettings.query.all()
        authors_prefix = {
            prefix.scheme: prefix.id for prefix in authors_prefix}

    list_import_id = []
    existed_authors_id, existed_external_authors_id = \
        WekoAuthors.get_author_for_validation()
    for item in file_data:
        errors = []
        warnings = []

        weko_id = item.get('pk_id')
        # check duplication WEKO ID
        if weko_id and weko_id not in list_import_id:
            list_import_id.append(weko_id)
        elif weko_id:
            errors.append(_('There is duplicated data in the {} file.').format(file_format))

        # set status
        set_record_status(file_format, existed_authors_id, item, errors, warnings)

        # get data folow by mapping
        data_by_mapping = {}
        for _key in mapping_ids:
            data_by_mapping[_key] = get_values_by_mapping(
                _key.split('.'), item)

        # Validation
        for field in mapping:
            _key = field['key']
            values = data_by_mapping[_key]
            validation = field['validation']

            # check required
            if validation.get('required'):
                errors_key = validate_required(
                    item, values, validation.get('required'))
                if errors_key:
                    errors.extend(list(map(
                        lambda k: _('{} is required item.').format(k),
                        errors_key
                    )))

            # check allow data
            if validation.get('map'):
                errors_key = validate_map(
                    values, validation.get('map'))
                if errors_key:
                    error_msg = _('{} should be set by one of {}.')
                    errors.extend(list(map(
                        lambda k: error_msg.format(k, validation.get('map')),
                        errors_key
                    )))

            # check by extend validator
            if validation.get('validator'):
                errors_msg = validate_by_extend_validator(
                    values, validation.get('validator'))
                if errors_msg:
                    errors.extend(errors_msg)

            # autofill data if empty
            if not errors and field.get('autofill'):
                autofill_data(item, values, field.get('autofill'))

            # convert mask data
            if not errors and field.get('mask'):
                convert_data_by_mask(item, values, field.get('mask'))

            if _key == 'authorIdInfo[0].idType':
                # convert scheme data
                convert_scheme_to_id(item, values, authors_prefix)
                # check external author identifier exist
                warning = validate_external_author_identifier(
                    item, values, existed_external_authors_id)
                if warning:
                    warnings.append(warning)

        if errors:
            item['errors'] = item['errors'] + errors \
                if item.get('errors') else errors
        if warnings:
            item['warnings'] = item['warnings'] + warnings \
                if item.get('warnings') else warnings

    return file_data


def unpackage_and_check_import_file_for_prefix(file_format, file_name, temp_file):
    from weko_search_ui.utils import handle_check_consistence_with_mapping, \
        handle_check_duplication_item_id, parse_to_json_form
    header = []
    file_data = []
    current_app.logger.debug("temp_file:{}".format(temp_file))
    prefix_mapping_key = current_app.config['WEKO_AUTHORS_FILE_MAPPING_FOR_PREFIX']
    enc = getEncode(temp_file)
    with open(temp_file, 'r', newline="", encoding=enc) as file:
        if file_format == 'csv':
            file_reader = csv.reader(file, dialect='excel', delimiter=',')
        else:
            file_reader = csv.reader(file, dialect='excel', delimiter='\t')
        try:
            for num, data_row in enumerate(file_reader, start=1):
                if num ==2:
                    header = data_row
                    header[0] = header[0].replace('#', '', 1)
                    duplication_ids = \
                        handle_check_duplication_item_id(header)
                    if duplication_ids:
                        msg = _(
                            'The following metadata keys are duplicated.'
                            '<br/>{}')
                        raise Exception({
                            'error_msg':
                                msg.format('<br/>'.join(duplication_ids))
                        })
                    not_consistent_list = \
                        handle_check_consistence_with_mapping_for_prefix(
                            prefix_mapping_key, header)
                    if not_consistent_list:
                        msg = _('Specified item does not consistency '
                                'with DB item.<br/>{}')
                        raise Exception({
                            'error_msg': msg.format(
                                '<br/>'.join(not_consistent_list))
                        })
                elif num in [3, 4] and data_row[0].startswith('#'):
                    continue
                elif num > 4:
                    pass
                    tmp_data ={}
                    try:
                        for num, data in enumerate(data_row, start=0):
                            tmp_data[header[num]] = data
                        print(tmp_data)
                    except Exception({
                            'error_msg': _('Cannot read {} file correctly.').format(file_format.upper())
                        }) as ex:
                        raise ex
                    file_data.append(tmp_data)
        except UnicodeDecodeError as ex:
            ex.reason = _('{} could not be read. Make sure the file'
                          + ' format is {} and that the file is'
                          + ' UTF-8 encoded.').format(file_name, file_format.upper())
            raise ex
        except Exception as ex:
            raise ex
    return file_data
            

def handle_check_consistence_with_mapping_for_prefix(keys, header):
    """Check consistence with mapping."""
    not_consistent_list = []
    for item in header:
        if item not in keys:
            not_consistent_list.append(item)
    return not_consistent_list

def validate_import_data_for_prefix(file_data, target):
    """
    tsvからのデータを以下の観点でチェックする。
    ・キーschemeが空かどうか
    ・キーnameが空かどうか
    ・urlがURLの記述でない
    ・作成か更新か削除か
        ・schemeが既に存在する場合、更新
        ・存在しないschemeの場合、作成
        ・is_deletedがDの場合、削除
    ・targetがid_prefixの時、schemeにWEKOが入力がされているか
    ・schemeで同じ値が二回出てきているか
    ・削除の際に、そのschemeが存在するかどうか
    ・削除の際に、その指定されたschemeが使用されているかどうか

    Args:
        file_data (json): unpackage_and_check_import_file_for_prefixの戻り値
        target (str): id_prefix or affiliation_id
    """
    if target == "id_prefix":
        existed_prefix = WekoAuthors.get_scheme_of_id_prefix()
        used_scheme, id_type_and_scheme = WekoAuthors.get_used_scheme_of_id_prefix()
    elif target == "affiliation_id":
        existed_prefix = WekoAuthors.get_scheme_of_affiliaiton_id()
        used_scheme, id_type_and_scheme = WekoAuthors.get_used_scheme_of_affiliation_id()

    list_import_scheme = []
    
    for item in file_data:
        errors = []
        scheme = item.get('scheme', "")
        name = item.get('name', "")
        url = item.get('url', "")
        is_deleted = item.get('is_deleted')
        # キーschemeが空かどうか
        if not scheme:
            errors.append(_("Scheme is required item."))
        # targetがid_prefixの時、schemeにWEKOが入力がされているか
        if target == "id_prefix" and scheme == "WEKO":
            errors.append(_("The scheme WEKO cannot be used."))
        # キーnameが空かどうか
        if not name:
            errors.append(_("Name is required item."))
        # urlがあるとき、urlがURLの記述でない
        if url and not url.startswith("http"):
            errors.append(_("URL is not URL format."))
        if is_deleted == "D":
            if scheme not in existed_prefix:
                errors.append(_("The specified scheme does not exist."))
            else:
                # schemeが著者DBで使用されている場合、削除しない
                if scheme in used_scheme:
                    errors.append(_("The specified scheme is used in the author ID."))
                id = [k for k, v in id_type_and_scheme.items() if v == scheme]
                item['id'] = id[0]
                item['status'] = 'deleted'
        else:
            # existed_prefixに含まれていれば更新、ないなら作成
            if scheme in existed_prefix:
                id = [k for k, v in id_type_and_scheme.items() if v == scheme]
                item['id'] = id[0]
                item['status'] = 'update'
            else:
                item['status'] = 'new'
        
        # schemeで同じ値が二回出てきているか
        if scheme in list_import_scheme:
            errors.append(_("The specified scheme is duplicated."))
        else: 
            list_import_scheme.append(scheme)
        if errors:
            item['errors'] = item['errors'] + errors \
                if item.get('errors') else errors
    return file_data
        

def get_values_by_mapping(keys, data, parent_key=None):
    """Get values folow by mapping."""
    result = []
    current_key = keys[0].replace('[0]', '')
    current_key_with_parent = parent_key + '.' + \
        current_key if parent_key else current_key
    current_data = data.get(current_key)

    if isinstance(current_data, list):
        for idx, item in enumerate(current_data):
            result.extend(get_values_by_mapping(
                keys[1:],
                item,
                current_key_with_parent + '[{}]'.format(idx)
            ))
    elif isinstance(current_data, dict):
        result.extend(get_values_by_mapping(
            keys[1:], current_data, current_key_with_parent))
    else:
        reduce_keys = [
            (int(k.replace(']', '')) if k.endswith(']') else k)
            for k in current_key_with_parent.replace('[', '.').split('.')
        ]
        result = [{
            'key': current_key_with_parent,
            'reduce_keys': reduce_keys,
            'value': current_data
        }]
    return result


def autofill_data(item, values, autofill_data):
    """Autofill data if empty."""
    for value in values:
        if not value['value']:
            reduce_keys = value['reduce_keys']
            uplevel_data = reduce(getitem, reduce_keys[:-1], item)

            # check either required
            either_required = autofill_data.get('condition', {}) \
                .get('either_required', [])
            if either_required:
                check = [cond for cond in either_required
                         if uplevel_data.get(cond)]
                autofill_val = ''
                if check:
                    autofill_val = autofill_data.get('value', '')
                uplevel_data[reduce_keys[-1]] = autofill_val


def convert_data_by_mask(item, values, mask):
    """Convert data if have mask."""
    for value in values:
        if value['value']:
            import_value = [key for key, val in mask.items()
                            if val == value['value']]
            import_value = import_value[0] if import_value else None
            reduce_keys = value['reduce_keys']
            reduce(getitem, reduce_keys[:-1],
                   item)[reduce_keys[-1]] = import_value


def convert_scheme_to_id(item, values, authors_prefix):
    """Convert scheme to id."""
    for value in values:
        if value['value']:
            reduce_keys = value['reduce_keys']
            reduce(getitem, reduce_keys[:-1], item)[reduce_keys[-1]] = \
                authors_prefix.get(value['value'], None)


def set_record_status(file_format, list_existed_author_id, item, errors, warnings):
    """Set status to import data."""
    item['status'] = 'new'
    pk_id = item.get('pk_id')
    err_msg = _("Specified WEKO ID does not exist.")
    if item.get('is_deleted', '') == 'D':
        item['status'] = 'deleted'
        if not pk_id or list_existed_author_id.get(pk_id) is None:
            errors.append(err_msg)
        elif get_count_item_link(pk_id) > 0:
            errors.append(
                _('The author is linked to items and cannot be deleted.'))
    elif pk_id:
        if list_existed_author_id.get(pk_id) is not None:
            item['status'] = 'update'
            if not list_existed_author_id.get(pk_id):
                warnings.append(_('The specified author has been deleted.'
                                  ' Update author information with {} content'
                                  ', but author remains deleted as it is.').format(file_format))
        else:
            errors.append(err_msg)


def flatten_authors_mapping(mapping, parent_key=None):
    """Flatten author mappings."""
    result_all = []
    result_keys = []
    for item in mapping:
        current_key = parent_key + '[0].' + item['json_id'] \
            if parent_key else item['json_id']
        if item.get('child'):
            child_result_all, child_result_keys = flatten_authors_mapping(
                item['child'], current_key)
            result_all.extend(child_result_all)
            result_keys.extend(child_result_keys)
        else:
            result_all.append(dict(
                key=current_key,
                label=dict(
                    en=item['label_en'],
                    jp=item['label_jp']
                ),
                mask=item.get('mask', {}),
                validation=item.get('validation', {}),
                autofill=item.get('autofill', '')
            ))
            result_keys.append(current_key)
    return result_all, result_keys


def import_author_to_system(author):
    """Import author to DB and ES.

    Args:
        author (object): Author metadata from tsv/csv.
    """
    if author:
        try:
            status = author['status']
            del author['status']

            author["is_deleted"] = True if author.get("is_deleted") else False
            if not author.get('authorIdInfo'):
                author["authorIdInfo"] = []

            if not author.get('emailInfo'):
                author['emailInfo'] = []

            for nameInfo in author.get('authorNameInfo', []):
                if "fullName" not in nameInfo:
                    fullName = nameInfo.get("familyName", "") + " " + nameInfo.get("firstName", "")
                    nameInfo["fullName"] = fullName

            if status == 'new':
                WekoAuthors.create(author)
            else:
                if status == 'deleted' \
                        and get_count_item_link(author['pk_id']) > 0:
                    raise Exception({'error_id': 'delete_author_link'})

                author["authorIdInfo"].insert(
                    0,
                    {
                        "idType": "1",
                        "authorId": author['pk_id'],
                        "authorIdShowFlg": "true"
                    }
                )
                WekoAuthors.update(author['pk_id'], author)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                'Author id: %s import error.' % author['pk_id'])
            traceback.print_exc(file=sys.stdout)
            raise ex


def get_count_item_link(pk_id):
    """Get count of item link of author."""
    count = 0
    query_q = {
        "query": {"term": {"author_link.raw": pk_id}},
        "_source": ["control_number"]
    }
    result_itemCnt = RecordIndexer().client.search(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'],
        body=query_q
    )

    if result_itemCnt \
            and 'hits' in result_itemCnt \
            and 'total' in result_itemCnt['hits'] \
            and result_itemCnt['hits']['total'] > 0:
        count = result_itemCnt['hits']['total']
    return count

def import_id_prefix_to_system(id_prefix):
    """
    tsv/csvからのid_prefixをDBにインポートする.
    Args:
        id_prefix (object): id_prefix metadata from tsv/csv.
    """
    if id_prefix:
        retrys = current_app.config["WEKO_AUTHORS_BULK_IMPORT_MAX_RETRY"]
        interval = current_app.config["WEKO_AUTHORS_BULK_IMPORT_RETRY_INTERVAL"]
        try:
            status = id_prefix.pop('status')
            for attempt in range(5):
                try:
                    if not id_prefix.get('url'):
                        id_prefix['url'] = ""
                    check = get_author_prefix_obj(id_prefix['scheme'])
                    if status == 'new':
                        if check is None:
                            AuthorsPrefixSettings.create(**id_prefix)
                    elif status == 'update':
                        if check is None or check.id == id_prefix['id']:
                            AuthorsPrefixSettings.update(**id_prefix)
                    elif status == 'deleted':
                        used_external_id_prefix,_ = WekoAuthors.get_used_scheme_of_id_prefix()
                        if id_prefix["scheme"] in used_external_id_prefix:
                            raise Exception({'error_id': 'delete_author_link'})
                        else:
                            if check is None or check.id == id_prefix['id']:
                                AuthorsPrefixSettings.delete(id_prefix['id'])
                    else:
                        raise Exception({'error_id': 'status_error'})
                    db.session.commit()
                    break
                except SQLAlchemyError as ex:
                    handle_exception(ex, attempt, retrys, interval)
                except TimeoutError as ex:
                    handle_exception(ex, attempt, retrys, interval)
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                f'Id prefix: {id_prefix["scheme"]} import error.')
            traceback.print_exc(file=sys.stdout)
            raise ex

def import_affiliation_id_to_system(affiliation_id):
    """
    tsv/csvからのaffiliation_idをDBにインポートする.
    Args:
        affiliation_id (object): affiliation_id metadata from tsv/csv.
    """
    if affiliation_id:
        retrys = current_app.config["WEKO_AUTHORS_BULK_IMPORT_MAX_RETRY"]
        interval = current_app.config["WEKO_AUTHORS_BULK_IMPORT_RETRY_INTERVAL"]
        try:
            status = affiliation_id.pop('status')
            for attempt in range(5):
                try:
                    if not affiliation_id.get('url'):
                        affiliation_id['url'] = ""
                    check = get_author_prefix_obj(affiliation_id['scheme'])
                    if status == 'new':
                        if check is None:
                            AuthorsAffiliationSettings.create(**affiliation_id)
                    elif status == 'update':
                        if check is None or check.id == affiliation_id['id']:
                            AuthorsAffiliationSettings.update(**affiliation_id)
                    elif status == 'deleted':
                        used_external_id_prefix,_ = WekoAuthors.get_used_scheme_of_affiliation_id()
                        if affiliation_id["scheme"] in used_external_id_prefix:
                            raise Exception({'error_id': 'delete_author_link'})
                        else:
                            if check is None or check.id == affiliation_id['id']:
                                AuthorsAffiliationSettings.delete(affiliation_id['id'])
                    else:
                        raise Exception({'error_id': 'status_error'})
                    db.session.commit()
                    break
                except SQLAlchemyError as ex:
                    handle_exception(ex, attempt, retrys, interval)
                except TimeoutError as ex:
                    handle_exception(ex, attempt, retrys, interval)
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                f'Affiliation Id: {affiliation_id["scheme"]} import error.')
            traceback.print_exc(file=sys.stdout)
            raise ex
