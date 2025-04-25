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
import re
import sys
import tempfile
import traceback
import re
import copy
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

from flask import current_app, jsonify
from flask_babelex import gettext as _
from invenio_cache import current_cache
from invenio_db import db
from invenio_indexer.api import RecordIndexer

from weko_authors.contrib.validation import validate_by_extend_validator, \
    validate_external_author_identifier, validate_map, validate_required, \
        check_weko_id_is_exits_for_import

from .api import WekoAuthors
from .models import AuthorsPrefixSettings, AuthorsAffiliationSettings, Authors

def update_cache_data(key: str, value: str, timeout=None):
    """Create or Update cache data.

    :param key: Cache key.
    :param value: Cache value.
    :param timeout: Cache expired.
    """
    if timeout is not None:
        current_cache.set(key, value, timeout=timeout)
    else:
        current_cache.set(key, value)

def get_author_prefix_obj(scheme):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsPrefixSettings).filter(
            AuthorsPrefixSettings.scheme == scheme).one_or_none()
    except Exception as ex:
        current_app.logger.debug(ex)
    return None

def get_author_prefix_obj_by_id(id):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsPrefixSettings).filter(
            AuthorsPrefixSettings.id == id).one_or_none()
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

def get_author_affiliation_obj_by_id(id):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsAffiliationSettings).filter(
            AuthorsAffiliationSettings.id == id).one_or_none()
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

def validate_weko_id(weko_id, pk_id = None):
    """Validate WEKO ID."""
    if not bool(re.fullmatch(r'[0-9]+', weko_id)):
        return False, "not half digit"
    # jsonify(msg=_('The author ID must be the half digit.')), 500

    try:
        result = check_weko_id_is_exists(weko_id, pk_id)
    except Exception as ex:
        current_app.logger.error(ex)
        raise ex
    # 存在するならエラーを返す
    if result == True:
        return False, "already exists"
    # jsonify(msg=_('The value is already in use as WEKO ID.')), 500
    return True, None

def check_weko_id_is_exists(weko_id, pk_id = None):
    """
    weko_idが既に存在するかチェック
    author_idが同じ場合はスキップする
    ※weko_idはauthorIdInfo.Idtypeが1であるAuthorIdの値のことです。

    args:
        weko_id: weko_id
    return:
        True: weko_idが存在する
        False: weko_idが存在しない
    """
    # 同じweko_idが存在するかチェック
    query = {
        "_source": ["pk_id", "authorIdInfo"],  # authorIdInfoフィールドのみを取得
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "authorIdInfo.authorId": weko_id
                        }
                    },
                    {"term": {"gather_flg": {"value": 0}}}
                ],
                "must_not": [
                    {"term": {"is_deleted": True}}
                ]
            }
        }
    }

    # 検索
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        body=query
    )

    # 同じweko_idが存在する場合はエラー
    for res in result['hits']['hits']:
        # 同じauthor_idの場合はスキップ
        if pk_id and pk_id == res['_source']['pk_id']:
            continue
        author_id_info_from_es = res['_source']['authorIdInfo']
        for info in author_id_info_from_es:
            if info.get('idType') == '1':
                author_id = info.get('authorId')
                if author_id == weko_id:
                    return True
    return False


def check_period_date(data):
    """
        dataのperiodを確認します。
        args:
            data: dict, 著者DBのjsonカラムのデータ
        return:
            True or False: 期間が正しいかどうか
            String: エラーの種別
    """
    from datetime import datetime
    if data.get("affiliationInfo"):
        for affiliation in data.get("affiliationInfo"):
            if affiliation.get("affiliationPeriodInfo"):
                for periodinfo in affiliation.get("affiliationPeriodInfo"):
                    if periodinfo.get("periodStart") or periodinfo.get("periodEnd"):
                        if periodinfo.get("periodStart"):
                            date_str = periodinfo.get("periodStart")
                            try:
                                datetime.strptime(date_str, "%Y-%m-%d")
                            except ValueError:
                                return False, "not date format"
                        if periodinfo.get("periodEnd"):
                            date_str = periodinfo.get("periodEnd")
                            try:
                                datetime.strptime(date_str, "%Y-%m-%d")
                            except ValueError:
                                return False, "not date format"
                        if periodinfo.get("periodStart") and periodinfo.get("periodEnd"):
                            period_start = datetime.strptime(periodinfo.get("periodStart"), "%Y-%m-%d")
                            period_end = datetime.strptime(periodinfo.get("periodEnd"), "%Y-%m-%d")
                            if period_start > period_end:
                                return False, "start is after end"
    return True, None

def get_export_status():
    """Get export status from cache."""
    return current_cache.get(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY")) or {}


def set_export_status(start_time=None, task_id=None):
    """Set export status into cache."""
    data = get_export_status() or dict()
    if start_time:
        data['start_time'] = start_time
    if task_id:
        data['task_id'] = task_id

    current_cache.set(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY"), data, timeout=0)
    return data


def delete_export_status():
    """Delete export status."""
    current_cache.delete(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY"))


def get_export_url():
    """Get exported info from cache."""
    return current_cache.get(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY")) or {}


def save_export_url(start_time, end_time, file_uri):
    """Save exported info into cache."""
    data = dict(
        start_time=start_time,
        end_time=end_time,
        file_uri=file_uri
    )

    current_cache.set(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY"), data, timeout=0)
    return data

def delete_export_url():
    """Delete exported url."""
    current_cache.delete(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY"))

def handle_exception(ex, attempt, retrys, interval, stop_point=0):
    """
    エラーをログで流し、スリープとリトライ回数の管理を行います.
    args:
        ex(Exception): Exception object
        attempt(int): Number of attempts
        retrys(int): Number of retries
        interval(int): Retry interval
        stop_point(int): Stop point

    """
    current_app.logger.error(ex)
    # 最後のリトライの場合は例外をraise
    if attempt == retrys - 1:
        current_app.logger.info(f"Connection failed, Stop export.")
        if stop_point != 0:
            update_cache_data(
                current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"],
                stop_point,
                current_app.config["WEKO_AUTHORS_CACHE_TTL"]
                )
        raise ex
    current_app.logger.info(f"Connection failed, retrying in {interval} seconds...")
    sleep(interval)

def export_authors():
    """Export all authors."""
    from invenio_files_rest.models import FileInstance, Location
    file_uri = None
    retrys = current_app.config["WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY"]
    interval = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
    size =  current_app.config.get("WEKO_AUTHORS_EXPORT_BATCH_SIZE", 1000)
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
                affiliation_mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION"])

                # 著者の数を取得（削除、統合された著者は除く）
                records_count = WekoAuthors.get_records_count(False, False)
                # マッピング上の複数が可能となる項目の最大値を取得
                mappings, affiliation_mappings = \
                    WekoAuthors.mapping_max_item(mappings, affiliation_mappings, records_count)

                # 著者識別子の対応を取得
                schemes = WekoAuthors.get_identifier_scheme_info()

                # 所属機関識別子の対応を取得
                aff_schemes = WekoAuthors.get_affiliation_identifier_scheme_info()

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
        for i in range(start_point, records_count, size):
            current_app.logger.info(f"Export authors start_point：{start_point}")
            row_header = []
            row_label_en = []
            row_label_jp = []
            row_data = []

            # 著者情報取得のリトライ処理
            for attempt in range(retrys):
                current_app.logger.info(f"Export authors retry count：{attempt}")
                try:
                    # 著者情報をstartからWEKO_EXPORT_BATCH_SIZE分取得
                    authors = WekoAuthors.get_by_range(i, size, False, False)
                    row_header, row_label_en, row_label_jp, row_data =\
                        WekoAuthors.prepare_export_data(mappings, affiliation_mappings, authors, schemes, aff_schemes, i, size)
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
    current_cache.set(
        current_app.config.get("WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY"),
        "author_db",
        timeout=0
    )

    return file_uri

def export_prefix(target):
    """
    id_prefixまたはaffiliation_idをエクスポートする
    args:
        target(str): エクスポート対象
    return:
        file_uri(str): ファイルURI
    """
    from invenio_files_rest.models import FileInstance, Location
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
    """
    ファイル名を取得する
    args:
        export_target(str): エクスポート対象
    return:
        file_base_name(str): ファイル名
    """
    file_base_name = ""
    if export_target == "author_db":
        file_base_name = current_app.config.get('WEKO_AUTHORS_EXPORT_FILE_NAME')
    elif export_target == "id_prefix":
        file_base_name = current_app.config.get('WEKO_AUTHORS_ID_PREFIX_EXPORT_FILE_NAME')
    elif export_target == "affiliation_id":
        file_base_name = current_app.config.get('WEKO_AUTHORS_AFFILIATION_EXPORT_FILE_NAME')
    return file_base_name

def write_to_tempfile(start, row_header, row_label_en, row_label_jp, row_data):
    """
    一時ファイルにデータを書き込む
    args:
        start(int): データの開始位置
        row_header(array): ヘッダー
        row_label_en(array): ラベル(英語)
        row_label_jp(array): ラベル(日本語)
        row_data(array): データ
    """
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
        file_name(str) -- file name.
    :return
        return       -- check information.
    """
    result = {}
    temp_file_path = current_cache.get(\
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"])
    try:
        affiliation_mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION"])
        mapping = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING"])
        mapping.append(affiliation_mappings)
        flat_mapping_all, flat_mapping_ids = flatten_authors_mapping(
            mapping)
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

def check_import_data_for_prefix(target, file_name: str, file_content: str):
    """id_prefixかaffiliation_idのインポート用 tsv/csvファイルをバリデーションチェックする.
    :argument
        file_name(str) -- file name.
        file_content(b64) -- content file.
    :return
        return       -- check information.
    """
    tmp_prefix = current_app.config['WEKO_AUTHORS_IMPORT_TMP_PREFIX']
    temp_file = tempfile.NamedTemporaryFile(prefix=tmp_prefix)
    result = {}

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

def clean_deep(data):
    """
    dataをクリーニングします。
    例えば{'fullname': 'Jane Doe',
        'warnings': None,
        'email': {"test":"","test2":"test2"},
        'test': [{"test":""},{"test2":"test2"}]}
    のようなデータを
    {'fullname': 'Jane Doe', 'email': {"test2":"test2"},
    'test': [{"test2":"test2"}]}に変換します。
    args:
        data (dict): data to clean
    return:
        data (dict): cleaned data
    """
    if isinstance(data, dict):
        return {k: clean_deep(v) for k, v in data.items() if v is not None and v != ''}
    elif isinstance(data, list):
        cleaned_list = [clean_deep(v) for v in data if v is not None and v != '']
        return [item for item in cleaned_list if item != {}]
    else:
        return data

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
                    data_parse_metadata = clean_deep(parse_to_json_form(
                        zip(header, data_row),
                        include_empty=True
                    ))

                    if not data_parse_metadata:
                        raise Exception({
                            'error_msg': _('Cannot read {} file correctly.').format(file_format.upper())
                        })

                    file_data.append(dict(**data_parse_metadata))
                    # file_dataがjson_sizeと同じになったら一時ファイルに書き込む
                    if len(file_data) == json_size:
                        write_tmp_part_file(math.ceil((num-3)/json_size), file_data, temp_file_path)
                        file_data = []
            # 書き込まれていないfile_dataを書き込む
            if len(file_data) != 0:
                write_tmp_part_file(math.ceil((count-3)/json_size), file_data, temp_file_path)
            # ファイルの行数が3行未満の場合エラー
            elif not file_data and count <= 3:
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
        list_import_id (list): List import id.
    return:
        list: Author data after validation.
    """
    authors_prefix = {}
    affilaition_id_prefix = {}
    with db.session.no_autoflush:
        authors_prefix = AuthorsPrefixSettings.query.all()
        authors_prefix = {
            prefix.scheme: prefix.id for prefix in authors_prefix}
        affilaition_id_prefix = AuthorsAffiliationSettings.query.all()
        affilaition_id_prefix = {
            prefix.scheme: prefix.id for prefix in affilaition_id_prefix}

    existed_authors_id, existed_external_authors_id = \
        WekoAuthors.get_author_for_validation()
    for item in file_data:
        errors = []
        warnings = []

        pk_id = item.get('pk_id')
        weko_id = item.get("weko_id")
        current_weko_id = WekoAuthors.get_weko_id_by_pk_id(pk_id)
        item["current_weko_id"] = current_weko_id
        errors_msg = check_weko_id_is_exits_for_import(pk_id, weko_id, existed_external_authors_id)
        if errors_msg:
            errors.extend(errors_msg)

        # check duplication WEKO ID
        if pk_id and pk_id not in list_import_id:
            list_import_id.append(pk_id)
        elif pk_id:
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
                    item, values, validation.get('validator'))
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
            if _key == "affiliationInfo[0].identifierInfo[0].affiliationIdType":
                convert_scheme_to_id(item, values, affilaition_id_prefix)

        if errors:
            item['errors'] = item['errors'] + errors \
                if item.get('errors') else errors
        if warnings:
            item['warnings'] = item['warnings'] + warnings \
                if item.get('warnings') else warnings

    return file_data


def unpackage_and_check_import_file_for_prefix(file_format, file_name, temp_file):
    """Unpackage and check format of import file for prefix.

    Args:
        file_format (str): File format.
        file_name (str): File uploaded name.
        temp_file (str): Temp file path.

    Returns:
        list: Tsv data.
    """
    from weko_search_ui.utils import handle_check_duplication_item_id
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
                    except Exception:
                        ex = Exception({
                            'error_msg': _('Cannot read {} file correctly.').format(file_format.upper())
                        })
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
            writer.writerow(["No.", "Current WEKO ID", "New WEKO ID", "full_name", "MailAddress", "Check Result"])
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

                    current_weko_id = entry.get("current_weko_id", "")
                    new_weko_id = entry.get("weko_id", "")
                    email = ""
                    if entry.get("emailInfo", [{}]):
                        email_info = entry.get("emailInfo", [{}])[0]
                        email = email_info.get("email", "")
                    check_result = get_check_result(entry)

                    writer.writerow([index, current_weko_id, new_weko_id, full_name_info, email, check_result])
    except Exception as ex:
        raise ex

    update_cache_data(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_BAND_CHECK_USER_FILE_PATH_KEY"],
        check_file_path,
        current_app.config["WEKO_AUTHORS_CACHE_TTL"]
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
                str(authors_prefix.get(value['value'], None))


def set_record_status(file_format, list_existed_author_id, item, errors, warnings):
    """Set status to import data."""
    item['status'] = 'new'
    pk_id = item.get('pk_id')
    err_msg = _("Specified Author ID does not exist.")
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
                        authors.append(item)
                    elif count == max_display:
                        reached_point["part_number"] = i
                        reached_point["count"] = count_for_json
                    else:
                        pass
                    count += 1
                count_for_json += 1
    return authors, reached_point, count

def import_author_to_system(author, status, weko_id, force_change_mode):
    """Import author to DB and ES.

    Args:
        author (object): Author metadata from tsv/csv.
    """
    from weko_logging.activity_logger import UserActivityLogger
    if author:
        try:
            check_weko_id = check_weko_id_is_exists(weko_id, author.get('pk_id'))

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
                if check_weko_id:
                    raise Exception({'error_id': "WekoID is duplicated"})
                author["authorIdInfo"].insert(
                    0,
                    {
                        "idType": "1",
                        "authorId": weko_id,
                        "authorIdShowFlg": "true"
                    }
                )
                WekoAuthors.create(author)
            else:
                if status == 'deleted' \
                        and get_count_item_link(author['pk_id']) > 0:
                    raise Exception({'error_id': 'delete_author_link'})

                if check_weko_id:
                    raise Exception({'error_id': "WekoID is duplicated"})
                author["authorIdInfo"].insert(
                    0,
                    {
                        "idType": "1",
                        "authorId": weko_id,
                        "authorIdShowFlg": "true"
                    }
                )
                WekoAuthors.update(author['pk_id'], author, force_change_mode)
            db.session.commit()
            if status == "new":
                UserActivityLogger.info(operation="AUTHOR_CREATE")
            else:
                UserActivityLogger.info(
                    operation="AUTHOR_UPDATE",
                    target_key=author['pk_id'])
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                'Author id: %s import error.' % author['pk_id'])
            traceback.print_exc(file=sys.stdout)
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            if status != "new" and author.get("pk_id"):
                UserActivityLogger.error(
                    operation="AUTHOR_UPDATE",
                    target_key=author['pk_id'],
                    remarks=tb_info[0]
                )
            else:
                UserActivityLogger.error(
                    operation="AUTHOR_CREATE",
                    remarks=tb_info[0]
                )
            raise ex

def create_result_file_for_user(json):
    """
    ユーザー用の結果ファイルを作成します。
    フロントに表示されている分とバックエンドで管理されている部分を別々に持ってきて合体させます。
    args:
        json (dict): フロントに表示される著者データ
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
            writer.writerow(["No.", "Start Date", "End Date", "Previous WEKO ID", "New WEKO ID", "full_name", "Status"])
            # まずフロントから送られてきたjsonを書き込む
            for data in json:
                number = data.get("No.", "")
                start_date = data.get("Start Date", "")
                end_date = data.get("End Date", "")
                prev_weko_id = data.get("Previous WEKO ID", "")
                new_weko_id = data.get("New WEKO ID", "")
                full_name = data.get("full_name", "")
                status = data.get("Status", "")
                writer.writerow([number, start_date, end_date, prev_weko_id, new_weko_id, full_name, status])
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
        current_app.config["WEKO_AUTHORS_CACHE_TTL"]
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


def count_authors():
    """Count authors from Elasticsearch."""
    should = [
        {'bool': {'must': [{'term': {'is_deleted': {'value': 'false'}}}]}},
        {'bool': {'must_not': {'exists': {'field': 'is_deleted'}}}}
    ]
    match = [{'term': {'gather_flg': 0}}, {'bool': {'should': should}}]

    query = {'bool': {'must': match}}

    indexer = RecordIndexer()
    result = indexer.client.count(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body={'query': query}
    )

    return result

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
            for attempt in range(retrys):
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
            for attempt in range(retrys):
                try:
                    if not affiliation_id.get('url'):
                        affiliation_id['url'] = ""
                    check = get_author_affiliation_obj(affiliation_id['scheme'])
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

def update_data_for_weko_link(data, weko_link):
    """
        authorsテーブルを元にweko_linkを更新し、
        違いがある場合は、dataをauthorsテーブルのweko_idを元に更新します。
        args:
            data: dict メタデータ、特にworkflowactivityのtemp_dataカラムのもの
            weko_link: list weko_link

    """
    old_weko_link = weko_link
    weko_link = copy.deepcopy(old_weko_link)
    # weko_linkを新しくする。
    for pk_id in weko_link.keys():
        author = Authors.get_author_by_id(pk_id)
        if author:
            # weko_idを取得する。
            author_id_info = author["authorIdInfo"]
            for i in author_id_info:
                # idTypeが1の場合、weko_idを取得し、weko_linkを更新する。
                if i.get('idType') == '1':
                    weko_link[pk_id] = i.get('authorId')
                    break
    # weko_linkが変更された場合、メタデータを更新する。
    if weko_link != old_weko_link:
        for x_key, x_value in data.items():
            if not isinstance(x_value, list):
                continue
            for y_index, y in enumerate(x_value, start=0):
                if not isinstance(y, dict):
                    continue
                for y_key, y_value in y.items():
                    if not y_key == "nameIdentifiers":
                        continue
                    for z_index, z in enumerate(y_value, start=0):
                        if z.get("nameIdentifierScheme","") == "WEKO":
                            if z.get("nameIdentifier") in old_weko_link.values():
                                # weko_linkから値がweko_idと一致するpk_idを取得する。
                                pk_id = [k for k, v in old_weko_link.items() if v == z.get("nameIdentifier")][0]
                                data[x_key][y_index][y_key][z_index]["nameIdentifier"] = weko_link.get(pk_id)

def get_check_base_name():
    temp_file_path = current_cache.get(\
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"])
    base_file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    return f"{base_file_name}-check"
