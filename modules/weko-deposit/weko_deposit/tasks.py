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
from time import sleep

from celery import shared_task
from celery.utils.log import get_task_logger
from flask import current_app
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from invenio_search import RecordsSearch
from sqlalchemy.exc import SQLAlchemyError
from weko_authors.models import AuthorsPrefixSettings
from weko_records.api import ItemsMetadata

from .api import WekoDeposit

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def update_items_by_authorInfo(origin_list, target):
    """Update item by authorInfo."""
    current_app.logger.debug('item update task is running.')

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

    def _change_to_meta(target, author_prefix, key_map):
        target_id = None
        meta = {}
        if target:
            family_names = []
            given_names = []
            full_names = []
            identifiers = []
            mails = []

            for name in target['authorNameInfo']:
                if not bool(name['nameShowFlg']):
                    continue
                family_names.append({
                    key_map['fname_key']: name['familyName'],
                    key_map['fname_lang_key']: name['language']
                })
                given_names.append({
                    key_map['gname_key']: name['firstName'],
                    key_map['gname_lang_key']: name['language']
                })
                full_names.append({
                    key_map['name_key']: "{}, {}".format(
                        name['familyName'],
                        name['firstName']),
                    key_map['name_lang_key']: name['language']
                })

            for id in target['authorIdInfo']:
                if not bool(id['authorIdShowFlg']):
                    continue
                prefix_info = author_prefix.get(id['idType'], {})
                if prefix_info:
                    id_info = {
                        key_map['id_scheme_key']: prefix_info['scheme'],
                        key_map['id_key']: id['authorId']
                    }
                    if prefix_info['url']:
                        if '##' in prefix_info['url']:
                            url = prefix_info['url'].replace(
                                '##', id['authorId'])
                        else:
                            url = prefix_info['url']
                        id_info.update({key_map['id_uri_key']: url})
                    identifiers.append(id_info)

                    if prefix_info['scheme'] == 'WEKO':
                        target_id = id['authorId']
            for email in target['emailInfo']:
                mails.append({
                    key_map['mail_key']: email['email']
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
        return target_id, meta

    def _update_author_data(item_id, record_ids):
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
                            for id in data['nameIdentifiers']:
                                if id['nameIdentifierScheme'] == 'WEKO':
                                    author_link.add(id['nameIdentifier'])
                                    if id['nameIdentifier'] in origin_list:
                                        origin_id = id['nameIdentifier']
                                        change_flag = True
                                        record_ids.append(pid.object_uuid)
                                        break
                                else:
                                    continue
                            if change_flag:
                                target_id, new_meta = _change_to_meta(
                                    target, author_prefix, key_map[prop_type])
                                dep[k]['attribute_value_mlt'][index].update(
                                    new_meta)
                                author_data.update(
                                    {k: dep[k]['attribute_value_mlt']})
                                if origin_id != target_id:
                                    author_link.remove(origin_id)
                                    author_link.add(target_id)

            dep['author_link'] = list(author_link)
            dep.update_item_by_task()
            obj = ItemsMetadata.get_record(pid.object_uuid)
            obj.update(author_data)
            obj.commit()
            return pid.object_uuid, author_link
        except PIDDoesNotExistError as pid_error:
            current_app.logger.error("PID {} does not exist.".format(item_id))
            return None, set()
        except Exception as ex:
            current_app.logger.error(ex)
            return None, set()

    def _process(data_size, data_from):
        res = False
        query_q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "query": "publish_status:0 AND "
                                         "relation_version_is_last:true"
                            }
                        }, {
                            "terms": {
                                "author_link": origin_list
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
            "mail_key": "creatorMail"
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
            "mail_key": "contributorMail"
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
            "mail_key": "mail"
        }
    }
    author_prefix = _get_author_prefix()

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
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger. \
            exception('Failed to update items by author data. err:{0}'.
                      format(e))
        update_items_by_authorInfo.retry(countdown=3, exc=e, max_retries=1)
