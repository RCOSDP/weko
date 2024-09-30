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
import csv
import json
from time import sleep
from io import StringIO
from elasticsearch import ElasticsearchException

from celery import shared_task
from celery.utils.log import get_task_logger
from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import RecordsSearch
from sqlalchemy.exc import SQLAlchemyError
from weko_authors.models import Authors, \
     AuthorsPrefixSettings, AuthorsAffiliationSettings
from weko_records.api import ItemsMetadata
from weko_schema_ui.models import PublishStatus
from weko_workflow.utils import delete_cache_data, update_cache_data

from .api import WekoDeposit
from .logger import weko_logger
from .errors import WekoDepositError

logger = get_task_logger(__name__)


FAIL_LABEL = "fail_items"
SUCCESS_LABEL = "success_items"
TARGET_LABEL = "target"
ORIGIN_LABEL = "origin"
TITLE_LIST = ["record_id", "author_ids", "message"]

@shared_task(ignore_result=True)
def update_items_by_authorInfo(user_id, target, origin_pkid_list=[],
                               origin_id_list=[], update_gather_flg=False):
    """Update item by authorInfo.

    Args:
        user_id (int): User ID.
        target (dict): Target data that requires to contain `authorNameInfo`, \
            `authorIdInfo`, `emailInfo` and `affiliationInfo`.
        origin_pkid_list (list): Origin PKID list.
        origin_id_list (list): Origin ID list.
        update_gather_flg (bool): Update gather flag.
    """
    process_counter = {
        FAIL_LABEL: [],
        SUCCESS_LABEL: [],
        TARGET_LABEL: target,
        ORIGIN_LABEL: []
    }

    def _get_author_prefix():
        """Get author prefix.

        Get author prefix from weko-authors.

        Returns:
            list: list of author prefix dict.
                Each dict contains `scheme`, `url`.
        """
        result = {}
        settings = AuthorsPrefixSettings.query.all()
        if settings:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="settings is not empty")

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, s in enumerate(settings):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=s)
                result[str(s.id)] = {
                    'scheme': s.scheme,
                    'url': s.url
                }
            weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def _get_affiliation_id():
        """Get affiliation id.

        Get affiliation id from weko-authors.

        Returns:
            list: list of affiliation dict.
                each dict contains `scheme`, `url`.
        """
        result = {}
        settings = AuthorsAffiliationSettings.query.all()
        if settings:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="settings is not empty")

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, s in enumerate(settings):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=s)
                result[str(s.id)] = {
                    'scheme': s.scheme,
                    'url': s.url
                }
            weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def _change_to_meta(target, author_prefix, affiliation_id, key_map):
        """Change to metadata.

        Change target author metadata and get new metadata.

        Args:
            target (dict): Target data.
            author_prefix (dict): Author prefix.
            affiliation_id (dict): Affiliation ID.
            key_map (dict): Key map.

        Returns:
            tuple: Tuple of `target_id` and `metadate`.
                `target_id` is author id. `metadata` is new changed metadata.
        """
        target_id = None
        meta = {}
        if target:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="target is not empty")
            family_names = []
            given_names = []
            full_names = []
            identifiers = []
            mails = []
            affiliation_identifiers = []
            affiliation_names = []
            affiliations = []

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, name in enumerate(target.get('authorNameInfo', [])):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=name)
                if not bool(name.get('nameShowFlg', "true")):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch="nameShowFlg is false")
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
            weko_logger(key='WEKO_COMMON_FOR_END')

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, id in enumerate(target.get('authorIdInfo', [])):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=id)
                if not bool(id.get('authorIdShowFlg', "true")):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch="authorIdShowFlg is false")
                    continue

                prefix_info = author_prefix.get(id.get('idType', ""), {})
                if prefix_info:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch="prefix_info is not empty")
                    id_info = {
                        key_map['id_scheme_key']: prefix_info['scheme'],
                        key_map['id_key']: id.get('authorId', '')
                    }
                    if prefix_info['url']:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch="prefix_info['url'] is not empty")
                        if '##' in prefix_info['url']:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch="## in prefix_info['url']")
                            url = prefix_info['url'].replace(
                                '##', id.get('authorId', ''))
                        else:
                            weko_logger(key='WEKO_COMMON_IF_ENTER',
                                        branch="## not in prefix_info['url']")
                            url = prefix_info['url']
                        id_info.update({key_map['id_uri_key']: url})
                    identifiers.append(id_info)

                    if prefix_info['scheme'] == 'WEKO':
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch="prefix_info['scheme'] == 'WEKO'")
                        target_id = id.get('authorId', '')

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, email in enumerate(target.get('emailInfo', [])):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=email)
                mails.append({
                    key_map['mail_key']: email.get('email', '')
                })
            weko_logger(key='WEKO_COMMON_FOR_END')

            weko_logger(key='WEKO_COMMON_FOR_START')
            for affiliation in target.get('affiliationInfo', []):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=affiliation)
                for identifier in affiliation.get('identifierInfo', []):
                    if not bool(identifier.get('identifierShowFlg', 'true')):
                        continue
                    affiliation_id_info = affiliation_id. \
                                          get(identifier.get('affiliationIdType', ''), {})
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
            weko_logger(key='WEKO_COMMON_FOR_END')

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

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=(target_id, meta))
        return target_id, meta

    def _update_author_data(item_id, record_ids):
        """Update author data.


        Args:
            item_id (int): Item ID.
            record_ids (list): Record ID list.

        Returns:
            tuple: Tuple of `object_uuid` and `author_link`.
            `object_uuid` is object uuid. `author_link` is author link.
        """
        temp_list = []
        try:
            pid = PersistentIdentifier.get('recid', item_id)
            dep = WekoDeposit.get_record(pid.object_uuid)
            author_link = set()
            author_data = {}

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (k, v) in enumerate(dep.items()):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=k)

                if isinstance(v, dict) \
                    and v.get('attribute_value_mlt') \
                        and isinstance(v['attribute_value_mlt'], list):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="value is dict and attribute_value_mlt is list")

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
            weko_logger(key='WEKO_COMMON_FOR_END')

            dep['author_link'] = list(author_link)
            dep.update_item_by_task()
            obj = ItemsMetadata.get_record(pid.object_uuid)
            obj.update(author_data)
            obj.commit()
            process_counter[SUCCESS_LABEL].append(
                {"record_id": item_id, "author_ids": temp_list, "message": ""})

            weko_logger(key='WEKO_COMMON_RETURN_VALUE',
                        value=(pid.object_uuid, author_link))
            return pid.object_uuid, author_link
        except PIDDoesNotExistError as ex:
            weko_logger(key='WEKO_DEPOSIT_PID_STATUS_NOT_REGISTERED',
                        pid=item_id, ex=ex)
            process_counter[FAIL_LABEL].append({
                "record_id": item_id,
                "author_ids": temp_list,
                "message": f"PID {item_id} does not exist."})
            result = None, set()
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
            return result
        except SQLAlchemyError as ex:
            weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
            process_counter[FAIL_LABEL].append({
                "record_id": item_id,
                "author_ids": temp_list,
                "message": f"Some errors in the DB while query record: "\
                    "{pid.object_uuid}."
                })
            result = None, set()
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
            return result
        except Exception as ex:
            weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            process_counter[FAIL_LABEL].append({
                "record_id": item_id,
                "author_ids": temp_list,
                "message": str(ex)})
            result = None, set()
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
            return result

    def _process(data_size, data_from):
        """process.


        Args:
            data_size (int): Data Size.
            data_from (int): Data From.

        Returns:
            int | bool: length of `update_es_authorinfo`.
        """

        res = False
        query_q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "query": "publish_status: {} AND relation_version_is_last:true".
                                    format(PublishStatus.PUBLIC.value)
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
            "from": data_from,
            "track_total_hit": True
        }
        search = RecordsSearch(
            index=current_app.config['INDEXER_DEFAULT_INDEX'],). \
                  update_from_dict(query_q).execute().to_dict()

        record_ids = []
        update_es_authorinfo = []
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, item in enumerate(search['hits']['hits']):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=item)

            item_id = item['_source']['control_number']
            object_uuid, author_link = _update_author_data(item_id, record_ids)
            if object_uuid:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch="object_uuid is not empty")
                update_es_authorinfo.append({
                    'id': object_uuid, 'author_link': list(author_link)})
        weko_logger(key='WEKO_COMMON_FOR_END')
        db.session.commit()
        # update record to ES
        if record_ids:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="record_ids is not empty")
            sleep(20)
            query = [
                x[0] for x 
                in PersistentIdentifier.query
                    .filter(PersistentIdentifier.object_uuid.in_(record_ids))
                    .values(PersistentIdentifier.object_uuid)
            ]
            RecordIndexer().bulk_index(query)
            RecordIndexer().process_bulk_queue(
                es_bulk_kwargs={'raise_on_error': True})
        if update_es_authorinfo:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="update_es_authorinfo is not empty")
            sleep(20)
            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, d in enumerate(update_es_authorinfo):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=d)

                dep = WekoDeposit.get_record(d['id'])
                dep.update_author_link(d['author_link'])
            weko_logger(key='WEKO_COMMON_FOR_END')

        data_total = search['hits']['total']['value']
        if data_total > data_size + data_from:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"data_total > {data_size + data_from}")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=len(update_es_authorinfo))
            return len(update_es_authorinfo), True
        else:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch=f"data_total <= {data_size + data_from}")
            weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=len(update_es_authorinfo))
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
        weko_logger(key='WEKO_COMMON_WHILE_START')
        while True:
            weko_logger(key='WEKO_COMMON_WHILE_LOOP_ITERATION',
                        count="", element=True)
            c, next = _process(data_size, data_from)
            counter += c
            data_from += data_size
            if not next:
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch="next is false")
                break
        weko_logger(key='WEKO_COMMON_WHILE_END')
        if update_gather_flg:
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="update_gather_flg is not empty")
            process_counter[ORIGIN_LABEL] = get_origin_data(origin_pkid_list)
            update_db_es_data(origin_pkid_list, origin_id_list)
            delete_cache_data("update_items_by_authorInfo_{}".format(user_id))
            update_cache_data(
                "update_items_status_{}".format(user_id),
                json.dumps(process_counter),
                current_app.config["WEKO_DEPOSIT_ITEM_UPDATE_STATUS_TTL"])
    except SQLAlchemyError as ex:
        process_counter[SUCCESS_LABEL] = []
        process_counter[FAIL_LABEL] = [{"record_id": "ALL", 
                                        "author_ids": [], "message": str(ex)}]
        delete_cache_data("update_items_by_authorInfo_{}".format(user_id))
        update_cache_data(
            "update_items_status_{}".format(user_id),
            json.dumps(process_counter),
            current_app.config["WEKO_DEPOSIT_ITEM_UPDATE_STATUS_TTL"])
        db.session.rollback()
        weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
        update_items_by_authorInfo.retry(countdown=3, exc=ex, max_retries=1)
    except Exception as ex:
        process_counter[SUCCESS_LABEL] = []
        process_counter[FAIL_LABEL] = [{"record_id": "ALL", 
                                        "author_ids": [], "message": str(ex)}]
        delete_cache_data("update_items_by_authorInfo_{}".format(user_id))
        update_cache_data(
            "update_items_status_{}".format(user_id),
            json.dumps(process_counter),
            current_app.config["WEKO_DEPOSIT_ITEM_UPDATE_STATUS_TTL"])
        db.session.rollback()
        weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
        update_items_by_authorInfo.retry(countdown=3, exc=ex, max_retries=1)


def get_origin_data(origin_pkid_list):
    """Get origin data.


    Args:
        origin_pkid_list (list): Origin pkId list.

    Returns:
        Returns:
            json: json of author_data.
    """
    author_data = Authors.query.filter(Authors.id.in_(origin_pkid_list)).all()
    return [a.json for a in author_data]

def update_db_es_data(origin_pkid_list, origin_id_list):
    """Update DB data.


    Args:
        origin_pkid_list (list): Origin pkId list.
        origin_id_list (list): Origin Id list.

    Returns:
        Returns:
            json: json of author_data.
    Raises:
        Common Error: unexpected error.
    """
    try:
        # update DB of Author
        with db.session.begin_nested():
            weko_logger(key='WEKO_COMMON_FOR_START')
            for j in origin_pkid_list:
                author_data = Authors.query.filter_by(id=j).one()
                author_data.gather_flg = 1
                db.session.merge(author_data)
            weko_logger(key='WEKO_COMMON_FOR_END')
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
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, t in enumerate(origin_id_list):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=t)
            q = json.dumps(update_author_q).replace("@id", t)
            q = json.loads(q)
            res = indexer.client.search(
                index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
                body=q
            )
            for i, h in enumerate(res.get("hits").get("hits")):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=h)
                body = {
                    'doc': {
                        'gather_flg': 1
                    }
                }
                indexer.client.update(
                    index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
                    id=h.get("_id"),
                    body=body
                )
        weko_logger(key='WEKO_COMMON_FOR_END')
    except SQLAlchemyError as ex:
        weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
        db.session.rollback()
    except ElasticsearchException as ex:
        weko_logger(key='WEKO_COMMON_ERROR_ELASTICSEARCH', ex=ex)
        db.session.rollback()
    except Exception as ex:
        weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
        db.session.rollback()


def make_stats_file(raw_stats):
    """Make TSV/CSV report file for stats.


    Args:
        raw_stats(int): Raw Stats.

    Returns:
        Returns:
            string: file_output.
    """
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
    file_output = StringIO()
    if file_format == 'csv':
        weko_logger(key='WEKO_COMMON_IF_ENTER',
                    branch="file format is csv")
        writer = csv.writer(file_output, delimiter=",", lineterminator="\n")
    else:
        weko_logger(key='WEKO_COMMON_IF_ENTER',
                    branch="file format is not csv")
        writer = csv.writer(file_output, delimiter="\t", lineterminator="\n")
    writer.writerow(["[TARGET]"])
    writer.writerow(list(raw_stats.get(TARGET_LABEL, {}).keys()))
    writer.writerow(list(raw_stats.get(TARGET_LABEL, {}).values()))
    writer.writerow("")

    writer.writerow(["[ORIGIN]"])
    weko_logger(key='WEKO_COMMON_FOR_START')
    for i, o in enumerate(raw_stats.get(ORIGIN_LABEL, [])):
        weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                    count=i, element=o)
        writer.writerow(list(o.keys()))
        writer.writerow(list(o.values()))
    weko_logger(key='WEKO_COMMON_FOR_END')
    writer.writerow("")

    writer.writerow(["[SUCCESS]"])
    if raw_stats.get(SUCCESS_LABEL, []):
        weko_logger(key='WEKO_COMMON_IF_ENTER',
                    branch="raw stats is not empty")
        writer.writerow(TITLE_LIST)
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, item in enumerate(raw_stats.get(SUCCESS_LABEL, [])):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=item)
            term = []
            for i, name in enumerate(TITLE_LIST):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=name)
                term.append(item.get(name))
            writer.writerow(term)
        weko_logger(key='WEKO_COMMON_FOR_END')
    writer.writerow("")

    writer.writerow(["[FAIL]"])
    if raw_stats.get(FAIL_LABEL, []):
        weko_logger(key='WEKO_COMMON_IF_ENTER',
                    branch="raw stats is not empty")
        writer.writerow(TITLE_LIST)
        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, item in enumerate(raw_stats.get(FAIL_LABEL, [])):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=item)
            term = []
            for i, name in enumerate(TITLE_LIST):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=name)
                term.append(item.get(name))
            writer.writerow(term)
        weko_logger(key='WEKO_COMMON_FOR_END')
    return file_output
