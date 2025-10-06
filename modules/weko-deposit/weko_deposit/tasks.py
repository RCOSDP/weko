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
from time import sleep
from io import StringIO
import subprocess
import time

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
from sqlalchemy.exc import SQLAlchemyError
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
def update_items_by_authorInfo(user_id, target, origin_pkid_list=[], origin_id_list=[], update_gather_flg=False):
    """Update item by authorInfo."""
    current_app.logger.debug('item update task is running.')
    process_counter = {
        FAIL_LABEL: [],
        SUCCESS_LABEL: [],
        TARGET_LABEL: target,
        ORIGIN_LABEL: []
    }

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

    def _change_to_meta(target, author_prefix, affiliation_id, key_map):
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

            for email in target.get('emailInfo', []):
                mails.append({
                    key_map['mail_key']: email.get('email', '')
                })

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

    def _update_author_data(item_id, record_ids):
        temp_list = []
        try:
            pid = PersistentIdentifier.get('recid', item_id)
            dep = WekoDeposit.get_record(pid.object_uuid)
            author_link = set()
            author_data = {}
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
                                    author_link.add(id['nameIdentifier'])
                                    if id['nameIdentifier'] in origin_pkid_list:
                                        origin_id = id['nameIdentifier']
                                        change_flag = True
                                        record_ids.append(pid.object_uuid)
                                        break
                                else:
                                    continue
                            if change_flag:
                                target_id, new_meta = _change_to_meta(
                                    target, author_prefix, affiliation_id, key_map[prop_type])
                                dep[k]['attribute_value_mlt'][index].update(
                                    new_meta)
                                author_data.update(
                                    {k: dep[k]['attribute_value_mlt']})
                                if origin_id != target_id:
                                    temp_list.append(origin_id)
                                    author_link.remove(origin_id)
                                    author_link.add(target_id)

            dep['author_link'] = list(author_link)
            dep.update_item_by_task()
            obj = ItemsMetadata.get_record(pid.object_uuid)
            obj.update(author_data)
            obj.commit()
            process_counter[SUCCESS_LABEL].append({"record_id": item_id, "author_ids": temp_list, "message": ""})
            return pid.object_uuid, author_link
        except PIDDoesNotExistError as pid_error:
            current_app.logger.error("PID {} does not exist.".format(item_id))
            process_counter[FAIL_LABEL].append({"record_id": item_id, "author_ids": temp_list, "message": "PID {} does not exist.".format(item_id)})
            return None, set()
        except Exception as ex:
            current_app.logger.error(ex)
            process_counter[FAIL_LABEL].append({"record_id": item_id, "author_ids": temp_list, "message": str(ex)})
            return None, set()

    def _process(data_size, data_from):
        res = False
        query_q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "query": "publish_status: {} AND relation_version_is_last:true".format(
                                    PublishStatus.PUBLIC.value)
                            }
                        }, {
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
            object_uuid, author_link = _update_author_data(item_id, record_ids)
            if object_uuid:
                update_es_authorinfo.append({
                    'id': object_uuid, 'author_link': list(author_link)})
        db.session.commit()
        # update record to ES
        if record_ids:
            sleep(20)
            query = (x[0] for x in PersistentIdentifier.query.filter(
                PersistentIdentifier.object_uuid.in_(record_ids)
            ).values(
                PersistentIdentifier.object_uuid
            ))
            RecordIndexer().bulk_index(query)
            RecordIndexer().process_bulk_queue(
                es_bulk_kwargs={'raise_on_error': True})
        if update_es_authorinfo:
            sleep(20)
            for d in update_es_authorinfo:
                dep = WekoDeposit.get_record(d['id'])
                dep.update_author_link(d['author_link'])

        data_total = search['hits']['total']
        if data_total > data_size + data_from:
            return len(update_es_authorinfo), True
        else:
            return len(update_es_authorinfo), False

    key_map = {
        "creator": {
            "ids_key": "nameIdentifiers",
            "id_scheme_key": "nameIdentifierScheme",
            "id_key": "nameIdentifier",
            "id_uri_key": "nameIdentifierURI",
            "names_key": "creatorNames",
            "name_key": "creatorName",
            "name_lang_key": "creatorNameLang",
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
            c, next = _process(data_size, data_from)
            counter += c
            data_from += data_size
            if not next:
                break
        current_app.logger.debug(
            "Total {} items have been updated.".format(counter))
        if update_gather_flg:
            process_counter[ORIGIN_LABEL] = get_origin_data(origin_pkid_list)
            update_db_es_data(origin_pkid_list, origin_id_list)
            delete_cache_data("update_items_by_authorInfo_{}".format(user_id))
            update_cache_data(
                "update_items_status_{}".format(user_id),
                json.dumps(process_counter),
                current_app.config["WEKO_DEPOSIT_ITEM_UPDATE_STATUS_TTL"])
    except SQLAlchemyError as e:
        process_counter[SUCCESS_LABEL] = []
        process_counter[FAIL_LABEL] = [{"record_id": "ALL", "author_ids": [], "message": str(e)}]
        delete_cache_data("update_items_by_authorInfo_{}".format(user_id))
        update_cache_data(
            "update_items_status_{}".format(user_id),
            json.dumps(process_counter),
            current_app.config["WEKO_DEPOSIT_ITEM_UPDATE_STATUS_TTL"])
        db.session.rollback()
        current_app.logger. \
            exception('Failed to update items by author data. err:{0}'.
                      format(e))
        update_items_by_authorInfo.retry(countdown=3, exc=e, max_retries=1)


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
def extract_pdf_and_update_file_contents(files, record_uuid, retry_count=3, retry_delay=1):
    """Extract text from pdf and update es document

    Args:
        files(dict): pdf_files uri and size. ex: {'test1.pdf': {'uri': '/var/tmp/tmp5beo2byv/e2/5a/e1af-d89b-4ce0-bd01-a78833acbe1e/data', 'size': 1252395}"
        record_uuid(str): The id of the document to update.
        retry_count(int, Optional): The number of times to retry. Defaults to 3.
        retry_delay(int, Optional): The number of seconds to wait between retries. Defaults to 1.
    """
    tika_jar_path = os.environ.get("TIKA_JAR_FILE_PATH")
    if not tika_jar_path or os.path.isfile(tika_jar_path) is False:
        raise Exception("not exist tika jar file.")
    file_datas = {}
    for filename, file in files.items():
        data = ""
        try:
            storage = current_files_rest.storage_factory(
                fileurl=file["uri"],
                size=file["size"],
            )

            with storage.open(mode="rb") as fp:
                buffer = fp.read(current_app.config['WEKO_DEPOSIT_FILESIZE_LIMIT'])
                args = ["java", "-jar", tika_jar_path, "-t"]
                result = subprocess.run(
                    args,
                    input=buffer,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if result.returncode != 0:
                    raise Exception("raise in tika: {}".format(result.stderr.decode("utf-8")))
                data = "".join(result.stdout.decode("utf-8").splitlines())
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
            break
        except ConflictError:
            current_app.logger.error(f"Version conflict error occurred while updating file content. Retrying {attempt + 1}/{retry_count}")
            time.sleep(retry_delay)
        except NotFoundError:
            current_app.logger.error(f"The document targeted for content update({record_uuid}) does not exist. Retrying {attempt + 1}/{retry_count}")
            time.sleep(retry_delay)
        except Exception:
            current_app.logger.error(f"An error occurred({record_uuid}). Retrying {attempt + 1}/{retry_count}")
            time.sleep(retry_delay)

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
    update_body = {"doc":{"content":contents}}
    indexer.client.update(
        index=indexer.es_index,
        doc_type=indexer.es_doc_type,
        id=str(record_uuid),
        body=update_body
    )


@shared_task(ignore_result=True)
def extract_pdf_and_update_file_contents_with_index_api(
    files, record_uuid, retry_count=3, retry_delay=1):
    """Extract text from pdf and update es document
    Args:
        files(dict): pdf_files uri and size. ex: {'test1.pdf': {'uri': '/var/tmp/tmp5beo2byv/e2/5a/e1af-d89b-4ce0-bd01-a78833acbe1e/data', 'size': 1252395}"
        record_uuid(str): The id of the document to update.
        retry_count(int, Optional): The number of times to retry. Defaults to 3.
        retry_delay(int, Optional): The number of seconds to wait between retries. Defaults to 1.
    """
    tika_jar_path = os.environ.get("TIKA_JAR_FILE_PATH")
    if not tika_jar_path or os.path.isfile(tika_jar_path) is False:
        raise Exception("not exist tika jar file.")
    file_datas = {}
    for filename, file in files.items():
        data = ""
        try:
            storage = current_files_rest.storage_factory(
                fileurl=file["uri"],
                size=file["size"],
            )

            with storage.open(mode="rb") as fp:
                buffer = fp.read(current_app.config['WEKO_DEPOSIT_FILESIZE_LIMIT'])
                args = ["java", "-jar", tika_jar_path, "-t"]
                result = subprocess.run(
                    args,
                    input=buffer,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False
                )
                if result.returncode != 0:
                    raise Exception(f"raise in tika: {result.stderr.decode('utf-8')}")
                data = "".join(result.stdout.decode("utf-8").splitlines())
        except FileNotFoundError as ex:
            current_app.logger.error(ex)
        except ResourceNotFoundError as ex:
            current_app.logger.error(ex)
        except Exception as ex:
            current_app.logger.error(ex)
        file_datas[filename] = data

    for attempt in range(retry_count):
        try:
            update_file_content_with_index_api(record_uuid, file_datas)
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


def update_file_content_with_index_api(record_uuid, file_datas):
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
