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
import os
import chardet
import io
import sys
import tempfile
import traceback
import json
import math
import datetime
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

from weko_workflow.utils import update_cache_data

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

def delete_export_url():
    """Delete exported url."""
    current_cache.delete(WEKO_AUTHORS_EXPORT_CACHE_URL_KEY)

def handle_exception(ex, attempt, retrys, interval, stop_point=0):
    """Handle exceptions during the export process."""
    current_app.logger.error(ex)
    # 最後のリトライの場合は例外をraise
    if attempt == retrys - 1:
        current_app.logger.info(f"Connection failed, Stop export.")
        if stop_point != 0:
            update_cache_data(
                current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"],
                stop_point,
                current_app.config["WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD"]
                )
        raise ex
    current_app.logger.info(f"Connection failed, retrying in {interval} seconds...")
    sleep(interval)
    
def export_authors():
    """Export all authors."""
    file_uri = None
    retrys = current_app.config["WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY"]
    interval = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
    size =  current_app.config.get("WEKO_AUTHORS_EXPORT_BATCH_SIZE", 1000)
    interval = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
    stop_point = current_cache.get(\
        current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"])
    mappings = []
    schemes = {}
    records_count = 0
    temp_file_path = ""

    try:
        # ある程度の処理をまとめてリトライ処理
        for attempt in range(retrys):
            try:
                # マッピングを取得
                mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING"])
                # マッピング上の複数が可能となる項目の最大値を取得
                mappings = WekoAuthors.mapping_max_item(mappings)

                # 著者識別子の対応を取得
                schemes = WekoAuthors.get_identifier_scheme_info()
                
                # 著者の数を取得（削除、統合された著者は除く）
                records_count = WekoAuthors.get_records_count(False, False)
                
                # 一時ファイルのパスを取得
                temp_file_path=current_cache.get(\
                    current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"])
                break
            except SQLAlchemyError as ex:
                handle_exception(ex, attempt, retrys, interval)
            except RedisError as ex:
                handle_exception(ex, attempt, retrys, interval)
            except TimeoutError as ex:
                handle_exception(ex, attempt, retrys, interval)
                
        # stop_pointがあればstart_pointに代入
        start_point = stop_point if stop_point else 0
        # 読み込み後削除
        current_cache.delete(\
            current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"])
        # 1000ずつ著者を取得し、データを書き込む
        for i in range(start_point, records_count-1, size):
            current_app.logger.info("Export authors start_point：",start_point)
            row_header = []
            row_label_en = []
            row_label_jp = []
            row_data = []

            # 著者情報取得のリトライ処理
            for attempt in range(retrys):
                current_app.logger.info("Export authors retry count：", attempt)
                try:
                    # 著者情報をstartからWEKO_EXPORT_BATCH_SIZE分取得
                    authors = WekoAuthors.get_by_range(i, size, False, False)
                    row_header, row_label_en, row_label_jp, row_data =\
                        WekoAuthors.prepare_export_data(mappings, authors, schemes, i, size)
                    break
                except SQLAlchemyError as ex:
                    handle_exception(ex, attempt, retrys, interval, stop_point=i)
                except RedisError as ex:
                    handle_exception(ex, attempt, retrys, interval, stop_point=i)
                except TimeoutError as ex:
                    handle_exception(ex, attempt, retrys, interval, stop_point=i)
                    
            # 一時ファイルに書き込み
            write_to_tempfile(i, row_header, row_label_en, row_label_jp, row_data)
            
        # 完成した一時ファイルをファイルインスタンスに保存
        with open(temp_file_path, 'rb') as f:
            reader = io.BufferedReader(f)
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
        # 完了時一時ファイルを削除
        os.remove(temp_file_path)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        if not current_cache.get(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"]):
            os.remove(temp_file_path)
        current_app.logger.error(ex)
        traceback.print_exc(file=stdout)

    return file_uri


def write_to_tempfile(start, row_header, row_label_en, row_label_jp, row_data):
    
    # 一時ファイルのパスを取得
    temp_file_path=current_cache.get( \
        current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"])

    # ファイルを開いてデータを書き込む
    try:
        with open(temp_file_path, 'a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # 1行目のみヘッダー、ラベルを書き込む
            if start == 0:
                writer.writerow(row_header)
                writer.writerow(row_label_en)
                writer.writerow(row_label_jp)
            writer.writerows(row_data)
    except Exception as ex:
        current_app.logger.error(ex)

def check_import_data(file_name: str):
    """Validation importing tsv/csv file.

    :argument
        file_name -- file name.
        file_content -- content file's name.
    :return
        return       -- check information.
    """
    result = {}
    temp_file_path = current_cache.get(\
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"])
    try:
        flat_mapping_all, flat_mapping_ids = flatten_authors_mapping(
            WEKO_AUTHORS_FILE_MAPPING)
        file_format = file_name.split('.')[-1].lower()
        max_part_num = unpackage_and_check_import_file(
            file_format, file_name, temp_file_path, flat_mapping_ids)
        list_import_id=[]
        temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")
        base_file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
        check_file_name = f"{base_file_name}-check"
        num_total = 0
        num_new = 0
        num_update = 0
        num_delete = 0
        num_error = 0
        for i in range(1, max_part_num+1):
            part_file_name = f'{base_file_name}-part{i}'
            part_file_path = os.path.join(temp_folder_path, part_file_name)
            with open(part_file_path, "r", encoding="utf-8-sig") as pf:
                data = json.load(pf)
                result_part = validate_import_data(
                    file_format, data, flat_mapping_ids, flat_mapping_all, list_import_id)
                num_total += len(result_part)
                num_new += len([item for item in result_part\
                    if item['status'] == 'new' and not item.get('errors')])
                num_update += len([item for item in result_part\
                    if item['status'] == 'update' and not item.get('errors')])
                num_delete += len([item for item in result_part\
                    if item['status'] == 'deleted' and not item.get('errors')])
                num_error += len([item for item in result_part\
                    if item.get('errors')])
            write_tmp_part_file(i, result_part, check_file_name)
            try:
                os.remove(part_file_path)
                current_app.logger.info(f"Deleted: {part_file_path}")
            except Exception as e:
                current_app.logger.error(f"Error deleting {part_file_path}: {e}")
        part1_check_file_name = f"{check_file_name}-part1"
        check_file_part1_path = os.path.join(temp_folder_path, part1_check_file_name)
        with open(check_file_part1_path, "r", encoding="utf-8-sig") as check_part1:
            result['list_import_data'] = json.load(check_part1)
        result["max_page"] = max_part_num
        result["counts"]={}
        result["counts"]["num_total"] = num_total
        result["counts"]["num_new"] = num_new
        result["counts"]["num_update"] = num_update
        result["counts"]["num_delete"] = num_delete
        result["counts"]["num_error"] = num_error
        
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
    try:
        os.remove(temp_file_path)
        current_app.logger.debug(f"Deleted: {temp_file_path}")
    except Exception as e:
        current_app.logger.error(f"Error deleting {temp_file_path}: {e}")

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


def unpackage_and_check_import_file(file_format, file_name, temp_file_path, mapping_ids):
    """Unpackage and check format of import file.

    Args:
        file_format (str): File format.
        file_name (str): File uploaded name.
        temp_file_path (str): Temp file path.
        mapping_ids (list): List only mapping ids.

    Returns:
        list: Tsv data.

    """
    from weko_search_ui.utils import handle_check_consistence_with_mapping, \
        handle_check_duplication_item_id, parse_to_json_form
    header = []
    file_data = []
    current_app.logger.debug("temp_file_path:{}".format(temp_file_path))
    enc = getEncode(temp_file_path)
    json_size=current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE")
    with open(temp_file_path, 'r', newline="", encoding=enc) as file:
        if file_format == 'csv':
            file_reader = csv.reader(file, dialect='excel', delimiter=',')
        else:
            file_reader = csv.reader(file, dialect='excel', delimiter='\t')
        count = 0
        try:
            for num, data_row in enumerate(file_reader, start=1):
                count += 1
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
                    if (num - 3)% json_size == 0:
                        write_tmp_part_file(math.ceil((num-3)/json_size), file_data, temp_file_path)
                        file_data = []
            if len(file_data) != 0:
                write_tmp_part_file(math.ceil((count-3)/json_size), file_data, temp_file_path)
                
            elif not file_data and (count-3) % json_size != 0:
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

    return math.ceil((count-3)/json_size)

def write_tmp_part_file(part_num, file_data, temp_file_path):
    """Write data to temp file for Import.
    Args:
        part_num(int): count of list
        file_data(list): Author data from tsv/csv.
        temp_file_path(str): path of basefile 
    """
    temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")
    base_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    part_file_name = f"{base_name}-part{part_num}"
    part_file_path = os.path.join(temp_folder_path, part_file_name)
    with open(part_file_path, 'w', encoding='utf-8-sig') as part_file:
        json.dump(file_data, part_file)

def validate_import_data(file_format, file_data, mapping_ids, mapping, list_import_id):
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


def band_check_file_for_user(max_page):
    """
    分割されているチェック結果をユーザー用に編集した後くっつけます。
    """
    
    # checkファイルパスの作成
    check_file_name = get_check_base_name()
    temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")
    check_file_download_name = "{}_{}.{}".format(
        "import_author_check_result",
        datetime.datetime.now().strftime("%Y%m%d%H%M"),
        "tsv"
    )
    check_file_path = os.path.join(temp_folder_path, check_file_download_name)
    try:
        with open(check_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(["No.", "WEKO ID", "full_name", "MailAddress", "Check Result"])
            for i in range(1, max_page+1):
                part_check_file_name = f"{check_file_name}-part{i}"
                check_file_part_path = os.path.join(temp_folder_path, part_check_file_name)
                with open(check_file_part_path, "r", encoding="utf-8-sig") as check_part_file:
                    data = json.load(check_part_file)
                batch_size = current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE")
                for index, entry in enumerate(data, start=(i-1)*batch_size+1):
                    pk_id = entry.get("pk_id", "")
                    full_name_info =""
                    for author_name_info in entry.get("authorNameInfo", [{}]):
                        family_name = author_name_info.get("familyName", "")
                        first_name = author_name_info.get("firstName", "")
                        full_name = f"{family_name},{first_name}"
                        if len(full_name)!=1:
                            if len(full_name_info)==0:
                                full_name_info += full_name
                            else:
                                full_name_info += f"\n{full_name}"
                    email_info = entry.get("emailInfo", [{}])[0]
                    email = email_info.get("email", "")
                    check_result = get_check_result(entry)

                    writer.writerow([index, pk_id, full_name_info, email, check_result])
    except Exception as ex:
        raise ex
    
    update_cache_data(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_BAND_CHECK_USER_FILE_PATH_KEY"],
        check_file_path,
        current_app.config["WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD"]
        )
    return check_file_path

def get_check_result(entry):
    """jsonのstatus,errorsをチェックし、それに合ったラベルを返します。"""
    errors = entry.get("errors", [])
    status = entry.get("status", "")
    
    if errors:
        return "Error: " + " ".join(errors)
    else:
        if status == "new":
            return _('Register')
        elif status == "update":
            return _('Update')
        elif status == "deleted":
            return _('Delete')
        else:
            return status

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

def prepare_import_data(max_page_for_import_tab):
    """
    Prepare import data.
    
    """
    
    # checkファイルパスの作成
    check_file_name = get_check_base_name()
    
    max_display = current_app.config.get("WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYS")
    temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")

    # フロント表示用の著者データ
    authors = []
    # インポートが実行される総数用の変数
    count = 0
    # フロントに表示される著者データの最大数に達したポイントを記録
    reached_point = {}
    for i in range(1, max_page_for_import_tab+1):
        part_check_file_name = f"{check_file_name}-part{i}"
        check_file_part_path = os.path.join(temp_folder_path, part_check_file_name)
        with open(check_file_part_path, "r", encoding="utf-8-sig") as check_part_file:
            data = json.load(check_part_file)
            # jsonの中で何番目のデータかをカウント
            count_for_json = 0
            for item in data:
                check_result = False if item.get("errors", []) else True
                if check_result:
                    if count < max_display:
                        item.pop("warnings", None)
                        item.pop("is_deleted", None)
                        authors.append(item)
                    elif count == max_display:
                        reached_point["part_number"] = i
                        reached_point["count"] = count_for_json
                    else:
                        pass
                    count += 1
                count_for_json += 1
    return authors, reached_point, count
                    
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

def create_result_file_for_user(json):
    """
    ユーザー用の結果ファイルを作成します。
    フロントに表示されている分とバックエンドで管理されている部分を別々に持ってきて合体させます。
    args:
        json: フロントに表示される著者データ
    """
    temp_folder_path = current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH")
    result_over_max_file_path = current_cache.get(\
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"])
    result_file_name = "{}_{}.{}".format(
        "import_author_result",
        datetime.datetime.now().strftime("%Y%m%d%H%M"),
        "tsv"
    )
    result_file_path = os.path.join(temp_folder_path, result_file_name)
    
    if not result_over_max_file_path:
        return None
    try :
        with open(result_file_path, "w", encoding="utf-8") as result_file:
            writer = csv.writer(result_file, delimiter='\t')
            # write header
            writer.writerow(["No.", "Start Date", "End Date", "WEKO ID", "full_name", "Status"])
            # まずフロントから送られてきたjsonを書き込む
            for data in json:
                number = data.get("No.", "")
                start_date = data.get("Start Date", "")
                end_date = data.get("End Date", "")
                weko_id = data.get("WEKO ID", "")
                full_name = data.get("full_name", "")
                status = data.get("Status", "")
                writer.writerow([number, start_date, end_date, weko_id, full_name, status])
            count = len(json) + 1
            with open(result_over_max_file_path, "r", encoding="utf-8") as file:
                file_reader = csv.reader(file, dialect='excel', delimiter='\t')
                for row in file_reader:
                    row[0] = count
                    writer.writerow(row)
                    count += 1
    except Exception as e:
        current_app.logger.error(e)
    update_cache_data(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"],
        result_file_path,
        current_app.config["WEKO_AUTHORS_IMPORT_TEMP_FILE_RETENTION_PERIOD"]
        )
    return result_file_path

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

def get_check_base_name():
    temp_file_path = current_cache.get(\
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"])
    base_file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    return f"{base_file_name}-check"