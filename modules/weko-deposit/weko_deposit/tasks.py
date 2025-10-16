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

"""Weko Deposit celery tasks."""
import os
import csv
import json
import subprocess
import time
import copy
import tempfile
from time import sleep
from io import StringIO

from celery import shared_task
from celery.utils.log import get_task_logger
from elasticsearch.exceptions import NotFoundError, ConflictError
from flask import current_app
from fs.errors import ResourceNotFoundError

from invenio_files_rest.proxies import current_files_rest
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from invenio_search import RecordsSearch
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError
from amqp.exceptions import ConnectionError
from weko_authors.models import Authors, AuthorsPrefixSettings, AuthorsAffiliationSettings
from weko_records.api import ItemsMetadata
from weko_schema_ui.models import PublishStatus
from weko_workflow.utils import delete_cache_data, update_cache_data

from .api import WekoDeposit, WekoIndexer

logger = get_task_logger(__name__)


FAIL_LABEL = "fail_items"
SUCCESS_LABEL = "success_items"
TARGET_LABEL = "target"
ORIGIN_LABEL = "origin"
TITLE_LIST = ["record_id", "author_ids", "message"]

@shared_task(ignore_result=True)
def update_items_by_authorInfo( user_id, target, origin_pkid_list=[], origin_id_list=[], update_gather_flg=False, force_change=False):
    """Update item by authorInfo."""
    current_app.logger.debug('item update task is running.')
    process_counter = {
        FAIL_LABEL: [],
        SUCCESS_LABEL: [],
        TARGET_LABEL: target,
        ORIGIN_LABEL: []
    }

    key_map = {
        "creator": {
            "ids_key": "nameIdentifiers",
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "names_key": "creatorNames",
            "name_key": "creatorName",
            "name_lang_key": "creatorNameLang",
            "name_type_key": "creatorNameType",
            "fnames_key": "familyNames",
            "fname_key": "familyName",
            "fname_lang_key": "familyNameLang",
            "gnames_key": "givenNames",
            "gname_key": "givenName",
            "gname_lang_key": "givenNameLang",
            "mails_key": "creatorMails",
            "mail_key": "creatorMail",
            "affiliations_key": "creatorAffiliations",
            "affiliation_ids_key": "affiliationNameIdentifiers",
            "affiliation_id_key": "affiliationNameIdentifier",
            "affiliation_id_uri_key": "affiliationNameIdentifierURI",
            "affiliation_id_scheme_key": "affiliationNameIdentifierScheme",
            "affiliation_names_key": "affiliationNames",
            "affiliation_name_key": "affiliationName",
            "affiliation_name_lang_key": "affiliationNameLang"
        },
        "contributor": {
            "ids_key": "nameIdentifiers",
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "names_key": "contributorNames",
            "name_key": "contributorName",
            "name_lang_key": "lang",
            "name_type_key": "nameType",
            "fnames_key": "familyNames",
            "fname_key": "familyName",
            "fname_lang_key": "familyNameLang",
            "gnames_key": "givenNames",
            "gname_key": "givenName",
            "gname_lang_key": "givenNameLang",
            "mails_key": "contributorMails",
            "mail_key": "contributorMail",
            "affiliations_key": "contributorAffiliations",
            "affiliation_ids_key": "contributorAffiliationNameIdentifiers",
            "affiliation_id_key": "contributorAffiliationNameIdentifier",
            "affiliation_id_uri_key": "contributorAffiliationURI",
            "affiliation_id_scheme_key": "contributorAffiliationScheme",
            "affiliation_names_key": "contributorAffiliationNames",
            "affiliation_name_key": "contributorAffiliationName",
            "affiliation_name_lang_key": "contributorAffiliationNameLang"
        },
        "full_name": {
            "ids_key": "nameIdentifiers",
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "names_key": "names",
            "name_key": "name",
            "name_lang_key": "nameLang",
            "name_type_key": None,
            "fnames_key": "familyNames",
            "fname_key": "familyName",
            "fname_lang_key": "familyNameLang",
            "gnames_key": "givenNames",
            "gname_key": "givenName",
            "gname_lang_key": "givenNameLang",
            "mails_key": "mails",
            "mail_key": "mail",
            "affiliations_key": "affiliations",
            "affiliation_ids_key": "nameIdentifiers",
            "affiliation_id_key": "nameIdentifier",
            "affiliation_id_uri_key": "nameIdentifierURI",
            "affiliation_id_scheme_key": "nameIdentifierScheme",
            "affiliation_names_key": "affiliationNames",
            "affiliation_name_key": "affiliationName",
            "affiliation_name_lang_key": "lang"
        }
    }
    author_prefix = _get_author_prefix()
    affiliation_id = _get_affiliation_id()

    try:
        data_from = 0
        data_size = current_app.config['WEKO_SEARCH_MAX_RESULT']
        counter = 0
        while True:
            current_app.logger.debug("process data from {}.".format(data_from))
            c, next = _process(data_size, data_from, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)
            counter += c
            data_from += data_size
            if not next:
                break
        current_app.logger.debug(
            "Total {} items have been updated.".format(counter))
        if update_gather_flg:
            process_counter[ORIGIN_LABEL] = get_origin_data(origin_pkid_list)
            update_db_es_data(origin_pkid_list, origin_id_list)
    except (DisconnectionError, TimeoutError, ConnectionError) as e:
        db.session.rollback()
        retry_count = update_items_by_authorInfo.request.retries
        countdown = current_app.config['WEKO_DEPOSIT_ITEM_UPDATE_RETRY_COUNTDOWN']
        if retry_count < current_app.config['WEKO_DEPOSIT_ITEM_UPDATE_RETRY_COUNT']:
            current_app.logger.exception('Retry due to connection error. err:{0}'.format(e))
            countdown *= current_app.config['WEKO_DEPOSIT_ITEM_UPDATE_RETRY_BACKOFF_RATE'] ** retry_count
        else:
            current_app.logger.exception('Failed to update items by author data. err:{0}'.format(e))
            process_counter[SUCCESS_LABEL] = []
            process_counter[FAIL_LABEL] = [{"record_id": "ALL", "author_ids": [], "message": str(e)}]
        update_items_by_authorInfo.retry(countdown=countdown, exc=e, max_retries=current_app.config['WEKO_DEPOSIT_ITEM_UPDATE_RETRY_COUNT'])
    except SQLAlchemyError as e:
        process_counter[SUCCESS_LABEL] = []
        process_counter[FAIL_LABEL] = [{"record_id": "ALL", "author_ids": [], "message": str(e)}]
        db.session.rollback()
        current_app.logger.exception('Failed to update items by author data. err:{0}'.format(e))
    finally:
        delete_cache_data("update_items_by_authorInfo_{}".format(user_id))
        update_cache_data(
            "update_items_status_{}".format(user_id),
            json.dumps(process_counter),
            current_app.config["WEKO_DEPOSIT_ITEM_UPDATE_STATUS_TTL"])

def _get_author_prefix():
    result = {}
    settings = AuthorsPrefixSettings.query.all()
    if settings:
        for s in settings:
            result[str(s.id)] = {
                'scheme': s.scheme,
                'url': s.url
            }
    return result

def _get_affiliation_id():
    result = {}
    settings = AuthorsAffiliationSettings.query.all()
    if settings:
        for s in settings:
            result[str(s.id)] = {
                'scheme': s.scheme,
                'url': s.url
            }
    return result


def _process(data_size, data_from, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change):
    res = False
    query_q = {
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "(publish_status: {} OR publish_status:{} OR publish_status:{})".format(
                                PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value, PublishStatus.NEW.value)
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"term": {"relation_version_is_last": True}},
                                {"bool": {"must_not": {"exists": {"field": "relation_version_is_last"}}}}
                            ]
                        }
                    },
                    {
                        "terms": {
                            "author_link.raw": origin_pkid_list
                        }
                    }]
            }
        },
        "_source": [
            "control_number"
        ],
        "size": data_size,
        "from": data_from
    }
    search = RecordsSearch(
        index=current_app.config['INDEXER_DEFAULT_INDEX'],). \
        update_from_dict(query_q).execute().to_dict()

    record_ids = []
    update_es_authorinfo = []
    for item in search['hits']['hits']:
        item_id = item['_source']['control_number']
        object_uuid, record_ids, author_link, weko_link = \
            _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change)
        if object_uuid:
            update_es_authorinfo.append({
                'id': object_uuid, 'author_link': list(author_link), 'weko_link': weko_link
            })
    db.session.commit()
    # update record to ES
    max_back_off_time = current_app.config['WEKO_DEPOSIT_MAX_BACK_OFF_TIME']
    if record_ids:
        # sleep(20)
        current_app.logger.debug("Start updated records to ES. record_ids:{}".format(record_ids))
        sleep_time = 2
        count = 1
        while True:
            try:
                query = (x[0] for x in PersistentIdentifier.query.filter(
                    PersistentIdentifier.object_uuid.in_(record_ids)
                ).values(
                    PersistentIdentifier.object_uuid
                ))
                RecordIndexer().bulk_index(query)
                RecordIndexer().process_bulk_queue(
                    es_bulk_kwargs={'raise_on_error': True})
                break
            except Exception as e:
                current_app.logger.error("Failed to update record to ES. method:process_bulk_queue err:{}".format(e))
                current_app.logger.error("retrys:{} sleep:{}s records_ids:{}".format(count, sleep_time, record_ids))
                if sleep_time > max_back_off_time:
                    raise e
                sleep(sleep_time)
                count += 1
                sleep_time *= 2
        current_app.logger.debug("Updated records to ES. record_ids:{}".format(record_ids))
    if update_es_authorinfo:
        for d in update_es_authorinfo:
            sleep_time = 2
            count = 1
            while True:
                try:
                    dep = WekoDeposit.get_record(d['id'])
                    dep.update_author_link_and_weko_link(d['author_link'], d["weko_link"])
                    break
                except Exception as e:
                    current_app.logger.error("Failed to update record to ES. method:update_author_link_and_weko_link err:{}".format(e))
                    current_app.logger.error("retrys:{} sleep{}".format(count, sleep_time))
                    if sleep_time > max_back_off_time:
                        raise e
                    sleep(sleep_time)
                    count += 1
                    sleep_time *= 2
            current_app.logger.debug("Updated records to ES. record_ids:{}".format(d['id']))

    data_total = search['hits']['total']
    if data_total > data_size + data_from:
        return len(update_es_authorinfo), True
    else:
        return len(update_es_authorinfo), False

def _update_author_data(item_id, record_ids, process_counter, target, origin_pkid_list, key_map, author_prefix, affiliation_id, force_change):
    temp_list = []
    try:
        pid = PersistentIdentifier.get('recid', item_id)
        dep = WekoDeposit.get_record(pid.object_uuid)
        author_link = set()
        author_data = {}
        current_weko_link = dep.get("weko_link", {})
        weko_link = copy.deepcopy(current_weko_link)

        # targetを用いてweko_linkを新しくする。
        if target:
            # weko_idを取得する。
            target_pk_id = target["pk_id"]
            author_id_info = target["authorIdInfo"]
            for i in author_id_info:
                # idTypeが1の場合、weko_idを取得し、weko_linkを更新する。
                if i.get('idType') == '1':
                    weko_link[target_pk_id] = i.get('authorId')
                    break
        for k, v in dep.items():
            if isinstance(v, dict) \
                and v.get('attribute_value_mlt') \
                    and isinstance(v['attribute_value_mlt'], list):
                data_list = v['attribute_value_mlt']
                prop_type = None
                for index, data in enumerate(data_list):
                    if isinstance(data, dict) \
                            and 'nameIdentifiers' in data:
                        if 'creatorNames' in data:
                            prop_type = 'creator'
                        elif 'contributorNames' in data:
                            prop_type = 'contributor'
                        elif 'names' in data:
                            prop_type = 'full_name'
                        else:
                            continue
                        origin_id = -1
                        change_flag = False
                        for id in data.get('nameIdentifiers', []):
                            if id.get('nameIdentifierScheme', '') == 'WEKO':

                                # author_link.add(id['nameIdentifier'])
                                # 1.current_weko_linkの値にdataのweko_idが含まれているかを確認する。
                                # 2.weko_idが含まれている場合、current_weko_linkでそのweko_id対応するpk_idを取得する。
                                pk_ids = [k for k, v in current_weko_link.items() if v == id.get("nameIdentifier")]
                                if pk_ids:
                                    pk_id = pk_ids[0]
                                    author_link.add(pk_id)
                                    # 3.origin_pkid_listにpk_idが含まれているかを確認する。
                                    if pk_id in origin_pkid_list:
                                        # 4.含まれている場合change_flagをTrueにする。
                                        change_flag = True
                                        record_ids.append(pid.object_uuid)
                                        break
                            else:
                                continue
                        if change_flag:
                            # targetは著者DBの情報
                            target_id, new_meta = _change_to_meta(
                                target, author_prefix, affiliation_id, key_map[prop_type], dep[k]["attribute_value_mlt"][index].get(key_map[prop_type]["names_key"], None), force_change)

                            dep[k]['attribute_value_mlt'][index].update(
                                new_meta)
                            author_data.update(
                                {k: dep[k]['attribute_value_mlt']})

        dep['author_link'] = list(author_link)
        dep["weko_link"] = weko_link

        dep.update_item_by_task()
        obj = ItemsMetadata.get_record(pid.object_uuid)
        obj.update(author_data)
        obj.commit()
        process_counter[SUCCESS_LABEL].append({"record_id": item_id, "author_ids": temp_list, "message": ""})
        return pid.object_uuid, record_ids, author_link, weko_link
    except PIDDoesNotExistError as pid_error:
        current_app.logger.error("PID {} does not exist.".format(item_id))
        process_counter[FAIL_LABEL].append({"record_id": item_id, "author_ids": temp_list, "message": "PID {} does not exist.".format(item_id)})
        return None, set(), {}, {}
    except Exception as ex:
        current_app.logger.error(ex)
        process_counter[FAIL_LABEL].append({"record_id": item_id, "author_ids": temp_list, "message": str(ex)})
        return None, set(), {}, {}

def _change_to_meta(target, author_prefix, affiliation_id, key_map, item_names_data, force_change=False):
    target_id = None
    meta = {}
    if target:
        family_names = []
        given_names = []
        full_names = []
        identifiers = []
        mails = []
        affiliation_identifiers = []
        affiliation_names = []
        affiliations = []
        for name in target.get('authorNameInfo', []):
            if not bool(name.get('nameShowFlg', "true")):
                continue
            family_names.append({
                key_map['fname_key']: name.get('familyName', ''),
                key_map['fname_lang_key']: name.get('language', '')
            })
            given_names.append({
                key_map['gname_key']: name.get('firstName', ''),
                key_map['gname_lang_key']: name.get('language', '')
            })
            full_names.append({
                key_map['name_key']: "{}, {}".format(
                    name.get('familyName', ''),
                    name.get('firstName', '')),
                key_map['name_lang_key']: name.get('language', '')
            })
        for id in target.get('authorIdInfo', []):
            if not bool(id.get('authorIdShowFlg', "true")):
                continue
            prefix_info = author_prefix.get(id.get('idType', ""), {})
            if prefix_info:
                id_info = {
                    key_map['id_scheme_key']: prefix_info['scheme'],
                    key_map['id_key']: id.get('authorId', '')
                }
                if prefix_info['url']:
                    if '##' in prefix_info['url']:
                        url = prefix_info['url'].replace(
                            '##', id.get('authorId', ''))
                    else:
                        url = prefix_info['url']
                    id_info.update({key_map['id_uri_key']: url})
                identifiers.append(id_info)

                if prefix_info['scheme'] == 'WEKO':
                    target_id = id.get('authorId', '')

        # 強制変更フラグがオフならば、ここで処理を終了する。
        # 識別子の情報のみアップデートする。
        if not force_change:
            if identifiers:
                meta.update({
                    key_map['ids_key']: identifiers
                })
            return target_id, meta

        for name in target.get('authorNameInfo', []):
            if not bool(name.get('nameShowFlg', "true")):
                continue
            family_names.append({
                key_map['fname_key']: name.get('familyName', ''),
                key_map['fname_lang_key']: name.get('language', '')
            })
            given_names.append({
                key_map['gname_key']: name.get('firstName', ''),
                key_map['gname_lang_key']: name.get('language', '')
            })
            full_names.append({
                key_map['name_key']: "{}, {}".format(
                    name.get('familyName', ''),
                    name.get('firstName', '')),
                key_map['name_lang_key']: name.get('language', '')
            })


        for email in target.get('emailInfo', []):
            mails.append({
                key_map['mail_key']: email.get('email', '')
            })

        # 所属識別子情報
        for affiliation in target.get('affiliationInfo', []):
            for identifier in affiliation.get('identifierInfo', []):
                if not bool(identifier.get('identifierShowFlg', 'true')):
                    continue
                affiliation_id_info = affiliation_id.get(identifier.get('affiliationIdType', ''), {})
                if affiliation_id_info:
                    id_info = {
                        key_map['affiliation_id_scheme_key']: affiliation_id_info['scheme'],
                        key_map['affiliation_id_key']: identifier.get('affiliationId', '')
                    }
                    if affiliation_id_info['url']:
                        if '##' in affiliation_id_info['url']:
                            url = affiliation_id_info['url'].replace(
                                '##', identifier.get('affiliationId', ''))
                        else:
                            url = affiliation_id_info['url']
                        id_info.update({key_map['affiliation_id_uri_key']: url})
                    affiliation_identifiers.append(id_info)
            for name in affiliation.get('affiliationNameInfo', []):
                if not bool(name.get('affiliationNameShowFlg', 'true')):
                    continue
                affiliation_names.append({
                    key_map['affiliation_name_key']: name.get('affiliationName', ''),
                    key_map['affiliation_name_lang_key']: name.get('affiliationNameLang', '')
                })

            affiliations.append({
                key_map['affiliation_ids_key']: affiliation_identifiers,
                key_map['affiliation_names_key']: affiliation_names
            })

        if family_names:
            meta.update({
                key_map['fnames_key']: family_names
            })
        if given_names:
            meta.update({
                key_map['gnames_key']: given_names
            })
        if full_names:
            if item_names_data:
                for idx, fn in enumerate(item_names_data):
                    if len(full_names) > idx and key_map["name_type_key"]:
                        full_names[idx][key_map["name_type_key"]] = item_names_data[idx].get(key_map["name_type_key"])
                    else:
                        break
            meta.update({
                key_map['names_key']: full_names
            })
        if identifiers:
            meta.update({
                key_map['ids_key']: identifiers
            })
        if mails:
            meta.update({
                key_map['mails_key']: mails
            })
        if affiliations:
            meta.update({
                key_map['affiliations_key']: affiliations
            })
    return target_id, meta



def get_origin_data(origin_pkid_list):
    author_data = Authors.query.filter(Authors.id.in_(origin_pkid_list)).all()
    return [a.json for a in author_data]

def update_db_es_data(origin_pkid_list, origin_id_list):
    try:
        # update DB of Author
        with db.session.begin_nested():
            for j in origin_pkid_list:
                author_data = Authors.query.filter_by(id=j).one()
                author_data.gather_flg = 1
                db.session.merge(author_data)
        db.session.commit()

        # update ES of Author
        update_author_q = {
            "query": {
                "match": {
                    "_id": "@id"
                }
            }
        }

        indexer = RecordIndexer()
        for t in origin_id_list:
            q = json.dumps(update_author_q).replace("@id", t)
            q = json.loads(q)
            res = indexer.client.search(
                index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
                body=q
            )
            for h in res.get("hits").get("hits"):
                body = {
                    'doc': {
                        'gather_flg': 1
                    }
                }
                indexer.client.update(
                    index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
                    doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
                    id=h.get("_id"),
                    body=body
                )
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()


def make_stats_file(raw_stats):
    """Make TSV/CSV report file for stats."""
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
    file_output = StringIO()
    if file_format == 'csv':
        writer = csv.writer(file_output, delimiter=",", lineterminator="\n")
    else:
        writer = csv.writer(file_output, delimiter="\t", lineterminator="\n")
    writer.writerow(["[TARGET]"])
    writer.writerow(list(raw_stats.get(TARGET_LABEL, {}).keys()))
    writer.writerow(list(raw_stats.get(TARGET_LABEL, {}).values()))
    writer.writerow("")

    writer.writerow(["[ORIGIN]"])
    for o in raw_stats.get(ORIGIN_LABEL, []):
        writer.writerow(list(o.keys()))
        writer.writerow(list(o.values()))
    writer.writerow("")

    writer.writerow(["[SUCCESS]"])
    if raw_stats.get(SUCCESS_LABEL, []):
        writer.writerow(TITLE_LIST)
        for item in raw_stats.get(SUCCESS_LABEL, []):
            term = []
            for name in TITLE_LIST:
                term.append(item.get(name))
            writer.writerow(term)
    writer.writerow("")

    writer.writerow(["[FAIL]"])
    if raw_stats.get(FAIL_LABEL, []):
        writer.writerow(TITLE_LIST)
        for item in raw_stats.get(FAIL_LABEL, []):
            term = []
            for name in TITLE_LIST:
                term.append(item.get(name))
            writer.writerow(term)

    return file_output


@shared_task(ignore_result=True)
def extract_pdf_and_update_file_contents(
    files, record_uuid, retry_count=3, retry_delay=1):
    """Extract text from pdf and update es document
    Args:
        files(dict): pdf_files uri and size,is_pdf flag. ex: {'test1.pdf': {'uri': '/var/tmp/data', 'size': 1252395,'is_pdf':True}"
        record_uuid(str): The id of the document to update.
        retry_count(int, Optional): The number of times to retry. Defaults to 3.
        retry_delay(int, Optional): The number of seconds to wait between retries. Defaults to 1.
    """
    from weko_deposit.utils import extract_text_from_pdf, extract_text_with_tika
    file_datas = {}
    for filename, file in files.items():
        data = ""
        try:
            storage = current_files_rest.storage_factory(
                fileurl=file["uri"],
                size=file["size"],
            )

            with storage.open(mode="rb") as fp:
                with tempfile.NamedTemporaryFile(delete=True) as tmp:
                    while True:
                        chunk = fp.read(1024 * 1024)
                        if not chunk:
                            break
                        tmp.write(chunk)
                    tmp.flush()
                    
                    is_pdf = file.get("is_pdf", False)
                    tmp_filename = tmp.name
                    file_size_limit = current_app.config['WEKO_DEPOSIT_FILESIZE_LIMIT']
                    if is_pdf:
                        data = extract_text_from_pdf(tmp_filename,file_size_limit)
                    else:
                        data = extract_text_with_tika(tmp_filename,file_size_limit)
        except FileNotFoundError as ex:
            current_app.logger.error(ex)
        except ResourceNotFoundError as ex:
            current_app.logger.error(ex)
        except Exception as ex:
            current_app.logger.error(ex)
        file_datas[filename] = data

    for attempt in range(retry_count):
        try:
            update_file_content(record_uuid, file_datas)
            success = True
            break
        except ConflictError:
            current_app.logger.error(
                f"Version conflict error occurred while updating file content. Retrying {attempt + 1}/{retry_count}")
            time.sleep(retry_delay)
        except NotFoundError:
            current_app.logger.error(
                f"The document targeted for content update({record_uuid}) does not exist. Retrying {attempt + 1}/{retry_count}")
            time.sleep(retry_delay)
        except Exception:
            current_app.logger.error(
                f"An error occurred({record_uuid}). Retrying {attempt + 1}/{retry_count}")
            time.sleep(retry_delay)
    if not success:
        current_app.logger.error(f"Failed to update file content after {retry_count} attempts. record_uuid: {record_uuid}")


def update_file_content(record_uuid, file_datas):
    """Update the content of the es document
    Args:
        record_uuid (str): The id of the document to update.
        file_datas (dict): A dictionary of file names and contents.

    Raises:
        ConflictError: Elasticsearch document version conflict error
        NotFoundError: No document to update error
    """
    indexer = WekoIndexer()
    indexer.get_es_index()
    res = indexer.get_metadata_by_item_id(record_uuid)
    es_data = res.get("_source",{})
    contents = es_data.get("content",[])
    for content in contents:
        if content.get("filename") not in list(file_datas.keys()):
            continue
        if content.get("attachment",{}):
            content["attachment"]["content"] = file_datas[content.get("filename")]
    es_data["content"] = contents

    indexer.client.index(
        index=indexer.es_index,
        id=str(record_uuid),
        body=es_data,
        version=res.get('_version'),
        version_type = "external_gte",
        doc_type=res.get("_type")
    )
