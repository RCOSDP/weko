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

"""Weko Authors API."""
import json
from copy import deepcopy
import uuid

from flask import current_app, json
from flask_security import current_user
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from sqlalchemy.sql.functions import func
from sqlalchemy.exc import SQLAlchemyError
from time import sleep
from invenio_communities.models import Community
import click
from invenio_search import current_search_client
from elasticsearch.helpers import bulk
from elasticsearch.helpers import BulkIndexError
from elasticsearch.exceptions import ConnectionTimeout, ConnectionError
import traceback

from .models import (
    Authors, AuthorsPrefixSettings, AuthorsAffiliationSettings,
    AuthorCommunityRelations
)


class WekoAuthors(object):
    """Weko Authors API for import/export."""

    @classmethod
    def create(cls, data):
        """Create new author."""
        session = db.session
        config_index = current_app.config['WEKO_AUTHORS_ES_INDEX_NAME']
        config_doc_type = current_app.config['WEKO_AUTHORS_ES_DOC_TYPE']

        new_id = Authors.get_sequence(session)
        data["pk_id"] = str(new_id)
        data["gather_flg"] = 0
        community_ids = data.pop("communityIds", [])

        es_id = str(uuid.uuid4())
        es_data = json.loads(json.dumps(data))
        es_data["communityIds"] = community_ids
        try:
            with session.begin_nested():
                data['id'] = es_id
                author = Authors(id=new_id, json=data)
                session.add(author)
                session.flush()
                author.add_communities(community_ids)

        except Exception as ex:
            session.rollback()
            raise
        else:
            RecordIndexer().client.index(
                index=config_index,
                doc_type=config_doc_type,
                id=es_id,
                body=es_data
            )

    @classmethod
    def update(cls, author_id, data, force_change=False):
        """Update author."""
        def update_es_data(data, es_id):
            """Update author data in ES."""
            es_author = RecordIndexer().client.search(
                index=config_index,
                doc_type=config_doc_type,
                body={
                    "query": {
                        'term': {
                            'pk_id': {'value': author_id}
                        }
                    },
                    "size": 1
                }
            )
            exist_flg = False
            if es_author['hits']['total'] > 0:
                if es_author['hits']['hits'][0].get('_id') == es_id:
                    exist_flg = True

            if exist_flg:
                RecordIndexer().client.update(
                    index=config_index,
                    doc_type=config_doc_type,
                    id=es_id,
                    body={'doc': data}
                )
                return False
            else:
                RecordIndexer().client.index(
                    index=config_index,
                    doc_type=config_doc_type,
                    id=es_id,
                    body=data
                )
                return True

        es_id = None
        config_index = current_app.config['WEKO_AUTHORS_ES_INDEX_NAME']
        config_doc_type = current_app.config['WEKO_AUTHORS_ES_DOC_TYPE']

        from weko_logging.activity_logger import UserActivityLogger
        try:
            with db.session.begin_nested():
                author = Authors.query.filter_by(id=author_id).one()
                if data.get('is_deleted'):
                    author.is_deleted = data.get('is_deleted', False)
                else:
                    data['is_deleted'] = author.is_deleted
                community_ids = data.pop("communityIds", [])
                author.update_communities(community_ids)
                es_id = author.json["id"] if author.json.get("id") else str(uuid.uuid4())
                es_data = json.loads(json.dumps(data))
                es_data["communityIds"] = community_ids
                data['id'] = es_id
                author.json = data
                db.session.merge(author)

            UserActivityLogger.info(
                operation="AUTHOR_UPDATE", target_key=author_id
            )
        except Exception as ex:
            db.session.rollback()
            UserActivityLogger.error(
                operation="AUTHOR_UPDATE", target_key=author_id)
            raise
        else:
            update_es_data(es_data, es_id)
        from weko_deposit.tasks import update_items_by_authorInfo
        if not current_user:
            user_id = None
        else:
            user_id = current_user.get_id()

        update_items_by_authorInfo.delay(
            user_id, data, [author_id], [data["id"]], force_change=force_change
        )

    @classmethod
    def get_all(cls, with_deleted=True, with_gather=True):
        """Get all authors."""
        filters = []
        with db.session.no_autoflush:
            if not with_deleted:
                filters.append(Authors.is_deleted.is_(False))
            if not with_gather:
                filters.append(Authors.gather_flg == 0)
            query = Authors.query.filter(*filters)
            query = query.order_by(Authors.id)
            query.count()

            return query.all()

    @classmethod
    def get_by_range(cls,  start_point, sum, with_deleted=True, with_gather=True, community_ids=None):
        """Get authors by range."""
        filters = []
        try:
            with db.session.no_autoflush:
                if not with_deleted:
                    filters.append(Authors.is_deleted.is_(False))
                if not with_gather:
                    filters.append(Authors.gather_flg == 0)
                query = Authors.query.filter(*filters)
                if community_ids is not None:
                    query = query.join(AuthorCommunityRelations, Authors.id == AuthorCommunityRelations.author_id)
                    query = query.filter(AuthorCommunityRelations.community_id.in_(community_ids))
                query = query.order_by(Authors.id)
                query = query.offset(start_point).limit(sum)
                return query.all()
        except Exception as ex:
            current_app.logger.error(ex)
            raise

    @classmethod
    def get_records_count(cls, with_deleted=True, with_gather=True, community_ids=None):
        """Get authors's count."""
        filters = []
        try:
            with db.session.no_autoflush:
                if not with_deleted:
                    filters.append(Authors.is_deleted.is_(False))
                if not with_gather:
                    filters.append(Authors.gather_flg == 0)
                query = Authors.query.filter(*filters)
                if community_ids is not None:
                    query = query.join(AuthorCommunityRelations, Authors.id == AuthorCommunityRelations.author_id)
                    query = query.filter(AuthorCommunityRelations.community_id.in_(community_ids))
                query = query.order_by(Authors.id)
                return query.count()
        except Exception as ex:
            current_app.logger.error(ex)
            raise


    @classmethod
    def get_author_for_validation(cls):
        """Get new author id."""
        existed_authors_id = {}
        existed_external_authors_id = {}
        for author in cls.get_all():
            not_deleted_and_gather = not author.is_deleted and author.gather_flg == 0
            existed_authors_id[str(author.id)] = not_deleted_and_gather
            metadata = author.json
            if not not_deleted_and_gather:
                continue
            for authorIdInfo in metadata.get('authorIdInfo', {}):
                idType = authorIdInfo.get('idType')
                if idType:
                    author_ids = existed_external_authors_id.get(idType, {})
                    weko_ids = author_ids.get(authorIdInfo.get('authorId'), [])
                    weko_ids.append(str(author.id))
                    author_ids[authorIdInfo.get('authorId')] = weko_ids
                    existed_external_authors_id[idType] = author_ids

        return existed_authors_id, existed_external_authors_id

    @classmethod
    def get_pk_id_by_weko_id(cls, weko_id):
        """
        Get pk_id by weko_id.
        """
        query = {
            "_source": ["pk_id", "authorIdInfo"],
            "query": {
                "bool": {
                    "must": [
                        {"term": {"authorIdInfo.authorId": weko_id}},
                        {"term": {"gather_flg": {"value": 0}}}
                    ],
                    "must_not": [
                        {"term": {"is_deleted": True}}
                    ]
                }
            }
        }

        # Search
        indexer = RecordIndexer()
        result = indexer.client.search(
            index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
            body=query
        )

        for res in result['hits']['hits']:
            author_id_info_from_es = res['_source']['authorIdInfo']
            for info in author_id_info_from_es:
                if info.get('idType') == '1':
                    author_id = info.get('authorId')
                    if author_id == weko_id:
                        pk_id = res['_source']['pk_id']
                        return pk_id
        return -1

    @classmethod
    def get_weko_id_by_pk_id(cls, pk_id):
        """Get weko_id from pk_id.

        Args:
            pk_id (str): pk_id

        Returns:
            weko_id :str
        """
        try:
            with db.session.begin_nested():
                author = Authors.query.filter_by(id=pk_id).one_or_none()
                if not author:
                    return None
                json = author.json
                for author_id_info in json["authorIdInfo"]:
                    if author_id_info["idType"] == "1":
                        weko_id = author_id_info["authorId"]
                        break
            return weko_id
        except Exception as ex:
            current_app.logger.error("Failed to get weko_id by pk_id")
            raise

    @classmethod
    def get_used_scheme_of_id_prefix(cls):
        """get used scheme of id prefix."""
        id_prefixes = cls.get_id_prefix_all()
        idtype_and_scheme ={}
        if id_prefixes:
            for id_prefix in id_prefixes:
                idtype_and_scheme[id_prefix.id] = id_prefix.scheme
        used_external_id_prefix = []
        for author in cls.get_all():
            metadata = author.json
            for authorIdInfo in metadata.get('authorIdInfo', {}):
                idType = authorIdInfo.get('idType')
                if (
                    idType and idType != '1'
                    and idtype_and_scheme.get(int(idType)) not in used_external_id_prefix
                ):
                    used_external_id_prefix.append(
                        idtype_and_scheme.get(int(idType))
                    )
        return used_external_id_prefix, idtype_and_scheme

    @classmethod
    def get_used_scheme_of_affiliation_id(cls):
        """get used scheme of affiliation id."""
        affiliaiton_ids = cls.get_affiliation_id_all()
        idtype_and_scheme ={}
        if affiliaiton_ids:
            for affiliaiton_id in affiliaiton_ids:
                idtype_and_scheme[affiliaiton_id.id] = affiliaiton_id.scheme
        used_external_id = []
        for author in cls.get_all():
            metadata = author.json
            for affiliationInfo in metadata.get('affiliationInfo', []):
                for identifierInfo in affiliationInfo.get('identifierInfo', []):
                    idType = identifierInfo.get('affiliationIdType')
                    if (idType
                        and idtype_and_scheme.get(int(idType)) not in used_external_id
                    ):
                        used_external_id.append(idtype_and_scheme.get(int(idType)))
        return used_external_id, idtype_and_scheme



    @classmethod
    def get_id_prefix_all(cls, community_ids=None):
        """Get all id_prefix."""
        with db.session.no_autoflush:
            query = AuthorsPrefixSettings.query
            if community_ids is not None:
                query = query.filter(
                    AuthorsPrefixSettings.communities.any(
                        Community.id.in_(community_ids)
                    )
                )
            query = query.order_by(AuthorsPrefixSettings.id)

            return query.all()

    @classmethod
    def get_scheme_of_id_prefix(cls):
        """Get all _id_prefix scheme."""
        result = []
        id_prefixes = cls.get_id_prefix_all()
        if id_prefixes:
            for id_prefix in id_prefixes:
                result.append(id_prefix.scheme)
        return result

    @classmethod
    def get_identifier_scheme_info(cls):
        """Get all Author Identifier Scheme informations."""
        result = {}
        with db.session.no_autoflush:
            schemes = AuthorsPrefixSettings.query.order_by(
                AuthorsPrefixSettings.id).all()
            if schemes:
                for scheme in schemes:
                    result[str(scheme.id)] = dict(
                        scheme=scheme.scheme, url=scheme.url)
        return result

    @classmethod
    def get_affiliation_id_all(cls, community_ids=None):
        """Get all affiliation_id."""
        with db.session.no_autoflush:
            query = AuthorsAffiliationSettings.query
            if community_ids is not None:
                query = query.filter(
                    AuthorsAffiliationSettings.communities.any(
                        Community.id.in_(community_ids)
                    )
                )
            query = query.order_by(AuthorsAffiliationSettings.id)

            return query.all()

    @classmethod
    def get_scheme_of_affiliaiton_id(cls):
        """Get all affiliation_id scheme."""
        result = []
        affiliaiton_ids = cls.get_affiliation_id_all()
        if affiliaiton_ids:
            for affiliation_id in affiliaiton_ids:
                result.append(affiliation_id.scheme)
        return result

    @classmethod
    def get_affiliation_identifier_scheme_info(cls):
        result = {}
        with db.session.no_autoflush:
            schemes = AuthorsAffiliationSettings.query.order_by(
                AuthorsAffiliationSettings.id).all()
            if schemes:
                for scheme in schemes:
                    result[str(scheme.id)] = dict(
                        scheme=scheme.scheme, url=scheme.url)
        return result

    @classmethod
    def mapping_max_item(cls, mappings, affiliation_mappings, community_mappings, records_count, retrys=0):
        """Mapping max item of multiple case."""
        try:
            size = current_app.config["WEKO_AUTHORS_EXPORT_BATCH_SIZE"]
            if not mappings:
                mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING"])
            if not affiliation_mappings:
                affiliation_mappings = deepcopy(
                    current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION"]
                )
            if not community_mappings:
                community_mappings = deepcopy(
                    current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_COMMUNITY"]
                )
            if not records_count:
                records_count = cls.get_records_count(False, False)
            # Get the total number of authors who are not deleted and not merged
            affiliation_mappings["max"] = []

            # Get authors by AUTHOR_EXPORT_BATCH_SIZE and calculate max
            for i in range(0, records_count, size):
                authors = cls.get_by_range(i, size, False, False)
                # Normal mapping processing
                for mapping in mappings:
                    if mapping.get('child'):
                        if not authors:
                            mapping['max'] = max(mapping.get('max', 1), 1)
                        else:
                            mapping['max'] = max(
                                mapping.get('max', 1),
                                max(list(map(
                                    lambda x: len(x.json.get(mapping['json_id'], [])),
                                    authors
                                )))
                            )
                            if mapping['max'] == 0:
                                mapping['max'] = 1

                # Affiliation info mapping processing
                mapping_max = affiliation_mappings["max"]
                # Get the maximum value of affiliation info in the author DB
                for author in authors:
                    json_data = author.json
                    # Under affiliation_mappings, create the following.
                    # This is created for each column of affiliationInfo.
                    # max:[
                    #       {
                    #         "identifierInfo" : length of affiliationInfo[i].identifierInfo,
                    #         "affiliationNameInfo" : length of affiliationInfo[i].affiliationNameInfo,
                    #         "affiliationPeriodInfo" : length of affiliationInfo[i].affiliationPeriodInfo
                    #       },
                    #     ]
                    for index, affiliation in enumerate(json_data.get(affiliation_mappings["json_id"], [])):
                        if len(mapping_max) < index+1 :
                            mapping_max.append({
                                "identifierInfo" : 1,
                                "affiliationNameInfo" : 1,
                                "affiliationPeriodInfo" : 1,
                            })
                        for child in affiliation_mappings["child"]:
                            child_length = len(affiliation.get(child["json_id"], []))
                            if child_length > mapping_max[index][child["json_id"]]:
                                mapping_max[index][child["json_id"]] = child_length

                community_mappings['max'] = max(
                    community_mappings.get('max', 1),
                    max((len(x.communities) for x in authors), default=0)
                )

            # Finally, subtract the WEKOID part from the maximum value
            for mapping in mappings:
                if mapping['json_id'] == 'authorIdInfo':
                    if mapping['max'] > 1:
                        mapping['max'] -= 1

        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            _num_retry = current_app.config["WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY"]
            sleep_time = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
            if retrys < _num_retry:
                retrys += 1
                current_app.logger.info("mapping_max_item retry count: {}".format(retrys))
                db.session.rollback()
                sleep(sleep_time)
                result = cls.mapping_max_item(
                    mappings=None, affiliation_mappings=None, community_mappings=None,
                    records_count=records_count, retrys=retrys
                )
                return result
            else:
                raise
        except Exception as ex:
            current_app.logger.error(ex)
            raise
        return mappings, affiliation_mappings, community_mappings

    @classmethod
    def prepare_export_data(cls, mappings, affiliation_mappings, community_mappings, authors, schemes, aff_schemes, start, size):
        """Prepare export data of all authors."""
        row_header = []
        row_label_en = []
        row_label_jp = []
        row_data = []

        if not mappings or not affiliation_mappings or not community_mappings:
            mappings, affiliation_mappings, community_mappings = WekoAuthors.mapping_max_item(
                deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING"]),
                deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION"]),
                deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_COMMUNITY"]),
                WekoAuthors.get_records_count(False, False)
            )
        if not authors:
            authors = cls.get_by_range(start, size, False, False)
        if not schemes:
            schemes = cls.get_identifier_scheme_info()
        if not aff_schemes:
            aff_schemes = cls.get_affiliation_identifier_scheme_info()
        # calc max item of multiple case and prepare header, label
        for mapping in mappings:
            if mapping.get('child'):
                for i in range(0, mapping['max']):
                    for child in mapping.get('child'):
                        row_header.append('{}[{}].{}'.format(
                            mapping['json_id'], i, child['json_id']))
                        row_label_en.append(
                            '{}[{}]'.format(child['label_en'], i))
                        row_label_jp.append(
                            '{}[{}]'.format(child['label_jp'], i))
            else:
                row_header.append(mapping['json_id'])
                row_label_en.append(mapping['label_en'])
                row_label_jp.append(mapping['label_jp'])

        # 所属情報のマッピングの処理
        aff_mapping_max = affiliation_mappings["max"]
        # tsv用に修正
        for index, m_max in enumerate(aff_mapping_max):
            for child in affiliation_mappings.get('child'):
                child_json_id = child["json_id"]
                for i in range(m_max[child_json_id]):
                    for c in child["child"]:
                        # for child in mapping.get:
                        row_header.append('{}[{}].{}[{}].{}'.format(
                            affiliation_mappings["json_id"], index, child_json_id, i, c['json_id']))
                        row_label_en.append(
                            '{}[{}][{}]'.format(c['label_en'], index, i))
                        row_label_jp.append(
                            '{}[{}][{}]'.format(c['label_jp'], index, i))

        # Community information mapping
        for i in range(0, community_mappings.get("max", 1)):
            row_header.append('{}[{}]'.format(community_mappings["json_id"], i))
            row_label_en.append('{}[{}]'.format(community_mappings["label_en"], i))
            row_label_jp.append('{}[{}]'.format(community_mappings["label_jp"], i))

        row_header[0] = '#' + row_header[0]
        row_label_en[0] = '#' + row_label_en[0]
        row_label_jp[0] = '#' + row_label_jp[0]

        # handle data rows
        for author in authors:
            json_data = author.json
            row = []
            for mapping in mappings:
                if mapping.get('child'):
                    data = json_data.get(mapping['json_id'], [])
                    idx_start = 0
                    idx_size = mapping['max']
                    # ignore WEKO id
                    if mapping['json_id'] == 'authorIdInfo':
                        idx_start = 1
                        idx_size += 1

                    for i in range(idx_start, idx_size):
                        for child in mapping.get('child'):
                            if i >= len(data):
                                row.append(None)
                            elif 'mask' in child:
                                row.append(
                                    child['mask'].get(
                                        str(data[i].get(
                                            child['json_id'])).lower(),
                                        None
                                    )
                                )
                            else:
                                val = data[i].get(child['json_id'])
                                if child['json_id'] == 'idType':
                                    scheme = schemes.get(str(val))
                                    row.append(
                                        scheme['scheme'] if scheme else val)
                                else:
                                    row.append(val)
                else:
                    if 'mask' in mapping:
                        row.append(
                            mapping['mask'].get(
                                str(json_data.get(
                                    mapping['json_id'])).lower(),
                                None
                            )
                        )
                    elif mapping["json_id"] == "weko_id":
                        id_info = json_data["authorIdInfo"][0]
                        if id_info["idType"] == "1":
                            row.append(id_info["authorId"])
                        else:
                            row.append(None)
                    else:
                        row.append(json_data.get(mapping['json_id']))

            # Process mapping for each affiliationInfo
            aff_data = json_data.get(affiliation_mappings['json_id'], [])
            affiliation_idx_start = 0
            affiliation_idx_size = len(aff_mapping_max)
            # Repeat for the maximum number of affiliations
            for i in range(affiliation_idx_start, affiliation_idx_size):
                for child in affiliation_mappings.get('child'):
                    aff_child_idx_start = 0
                    aff_child_idx_size = aff_mapping_max[i][child["json_id"]]
                    for j in range(aff_child_idx_start, aff_child_idx_size):
                        for c in child.get("child"):
                            if i >= len(aff_data):
                                row.append(None)
                                continue
                            aff_d = aff_data[i].get(child["json_id"], [])
                            if j >= len(aff_d):
                                row.append(None)
                                continue
                            if "mask" in c:
                                row.append(
                                    c['mask'].get(
                                        str(aff_d[j].get(
                                            c["json_id"])).lower(),
                                        None
                                    )
                                )
                            else:
                                val = aff_d[j].get(c["json_id"])
                                if c["json_id"] == "affiliationIdType":
                                    aff_scheme = aff_schemes.get(val)
                                    row.append(
                                        aff_scheme["scheme"] if aff_scheme else val
                                    )
                                else:
                                    row.append(val)

            # Process mapping for each community
            com_ids = [c.id for c in author.communities]
            com_ids.extend([None] * (community_mappings.get("max", 1) - len(com_ids)))
            row.extend(com_ids)

            row_data.append(row)

        return row_header, row_label_en, row_label_jp, row_data

    @classmethod
    def prepare_export_prefix(cls, target_prefix, prefixes, community_length):
        """Prepare export data of id_prefix, affiliation_id."""
        row_data = []

        for prefix in prefixes:
            # Exclude WEKO's own prefix for author identifier prefixes
            if target_prefix == "id_prefix" and prefix.scheme == "WEKO":
                continue

            ids = [c.id for c in prefix.communities]
            ids.extend([None] * (community_length - len(ids)))
            row = [prefix.scheme, prefix.name, prefix.url, None] + ids
            row_data.append(row)

        return row_data


class AuthorIndexer():
    def __init__(self, search_client=None):
        self.client = search_client or current_search_client

    def author_to_index(self):
        index = current_app.config['WEKO_AUTHORS_ES_INDEX_NAME']
        doc_type = current_app.config['WEKO_AUTHORS_ES_DOC_TYPE']
        return index, doc_type

    def bulk_process_authors(self,es_bulk_kwargs, uuids = [],start_date=None,end_date=None,with_deleted=True):
        success = 0
        fail = 0
        unprocesses = 0
        req_timeout = current_app.config['INDEXER_BULK_REQUEST_TIMEOUT']
        self.count = 0
        try:
            _success, _fail = bulk(
                self.client,
                self.generate_actions(uuids, start_date, end_date, with_deleted),
                request_timeout=req_timeout,
                **es_bulk_kwargs
            )
            success += _success
            if isinstance(_fail, list):
                _fail_len = len(_fail)
                for error in _fail:
                    click.secho("{}, {}".format(error['index']['_id'],error['index']['error']['type']),fg='red')
            else:
                _fail_len = _fail
            fail += _fail_len
            unprocesses += self.count - _success - _fail_len
        except SQLAlchemyError as e:
            current_app.logger.error(e)
            current_app.logger.error(traceback.format_exc())
            db.session.rollback()
        except BulkIndexError as e:
            _fail = len(e.errors)
            _success = self.count - _fail
            _unprocessed = len(uuids) - self.count

            fail += _fail
            success += _success
            unprocesses += _unprocessed
            for error in e.errors:
                click.secho("{}, {}".format(error['index']['_id'],error['index']['error']['type']),fg='red')
        except ConnectionError as ce:
            click.secho("Connection error occurred: {}".format(ce),fg='red')
        except ConnectionTimeout as ce:
            click.secho("Error: {}".format(ce),fg="red")
            click.secho("INDEXER_BULK_REQUEST_TIMEOUT: {} sec".format(req_timeout),fg="red")
            click.secho("Please change value of INDEXER_BULK_REQUEST_TIMEOUT and retry it.",fg="red")
            click.secho("processing: {}".format(self.count),fg="red")
            click.secho("latest processing id: {}".format(self.latest_item_id),fg="red")
        except Exception as e:
            current_app.logger.error(e)
            current_app.logger.error(traceback.format_exc())
        count = (success,fail,unprocesses)
        click.secho("count(success, error, unprocessed): {}".format(count),fg='green')

        return count


    def generate_actions(self,uuids=[],start_date=None, end_date=None,with_deleted=True):
        index, doc_type = self.author_to_index()
        if len(uuids) > 0:
            authors = []
            for uuid in uuids:
                filters.append(Authors.id==uuid)
                query = Authors.query.filter(Authors.id==uuid)
                if not with_deleted:
                    query = query.filter(Authors.is_deleted.is_(False))
                author = query.one_or_none()
                if author:
                    authors.append(author)
        else:
            filters  =[]
            if not with_deleted:
                filters.append(Authors.is_deleted.is_(False))
            if start_date:
                filters.append(Authors.updated >= start_date)
            if end_date:
                filters.append(Authors.updated < end_date)
            query = Authors.query.filter(*filters)
            authors = query.all()
        if len(authors) == 0:
            click.echo("Error: No authors were found for processing, so the operation was stopped.",fg="red")
        for author in authors:

            body = self._prepare_author(author)
            action = {
                "_op_type": "index",
                "_index": index,
                "_type": doc_type,
                "_id": str(author.id),
                "_source": body
            }
            self.count += 1
            click.secho(f"Indexing author id: {author.id}, Count:{self.count}", fg='green')
            yield action

    def _prepare_author(self, author):
        return author.json
