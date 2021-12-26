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

"""Weko Deposit API."""
import copy
import inspect
import sys
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import NoReturn, Union

import redis
from dictdiffer import dot_lookup
from dictdiffer.merge import Merger, UnresolvedConflictsException
from elasticsearch.exceptions import TransportError
from elasticsearch.helpers import bulk
from flask import abort, current_app, has_request_context, json, request, \
    session
from flask_security import current_user
from invenio_db import db
from invenio_deposit.api import Deposit, index, preserve
from invenio_deposit.errors import MergeConflict
from invenio_files_rest.models import Bucket, MultipartObject, ObjectVersion, \
    Part
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer
from invenio_oaiserver.models import OAISet
from invenio_pidrelations.contrib.records import RecordDraft
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.serializers.utils import serialize_relations
from invenio_pidstore.errors import PIDDoesNotExistError, PIDInvalidAction
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_files.api import FileObject, Record
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest.errors import PIDResolveRESTError
from simplekv.memory.redisstore import RedisStore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified
from weko_admin.models import AdminSettings
from weko_index_tree.api import Indexes
from weko_records.api import FeedbackMailList, ItemLink, ItemsMetadata, \
    ItemTypes
from weko_records.models import ItemMetadata, ItemReference
from weko_records.utils import get_all_items, get_attribute_value_all_items, \
    get_options_and_order_list, json_loader, remove_weko2_special_character, \
    set_timestamp
from weko_user_profiles.models import UserProfile

from .config import WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_KEY, \
    WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_SYS_KEY, WEKO_DEPOSIT_SYS_CREATOR_KEY
from .pidstore import get_latest_version_id, get_record_without_version, \
    weko_deposit_fetcher, weko_deposit_minter
from .signals import item_created

PRESERVE_FIELDS = (
    '_deposit',
    '_buckets',
    '_files',
    '_internal',
    '_oai',
    'relations',
    'owners',
    'recid',
    'conceptrecid',
    'conceptdoi',
)


class WekoFileObject(FileObject):
    """Extend FileObject for detail page."""

    def __init__(self, obj, data):
        """Bind to current bucket."""
        self.obj = obj
        self.data = data
        self.info()
        self.preview_able = self.file_preview_able()

    def info(self):
        """Info."""
        super(WekoFileObject, self).dumps()
        self.data.update(self.obj.file.json)
        if hasattr(self, 'filename'):
            # If the record has not been set into an index, then the attr
            # 'filename' will not exist
            index = self['filename'].rfind('.')
            self['filename'] = self['filename'][:index]
        return self.data

    def file_preview_able(self):
        """Check whether file can be previewed or not."""
        file_type = ''
        file_size = self.data['size']
        for k, v in current_app.config['WEKO_ITEMS_UI_MS_MIME_TYPE'].items():
            if self.data.get('format') in v:
                file_type = k
                break
        if file_type in current_app.config[
                'WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'].keys():
            # Convert MB to Bytes in decimal
            file_size_limit = current_app.config[
                'WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'][
                file_type] * 1000000
            if file_size > file_size_limit:
                return False
        return True


class WekoIndexer(RecordIndexer):
    """Provide an interface for indexing records in Elasticsearch."""

    def get_es_index(self):
        """Elastic search settings."""
        self.es_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
        self.es_doc_type = current_app.config['INDEXER_DEFAULT_DOCTYPE']
        self.file_doc_type = current_app.config['INDEXER_FILE_DOC_TYPE']

    def upload_metadata(self, jrc, item_id, revision_id, skip_files=False):
        """Upload the item data to ElasticSearch.

        :param jrc:
        :param item_id: item id.
        """
        es_info = dict(id=str(item_id),
                       index=self.es_index,
                       doc_type=self.es_doc_type)
        body = dict(version=revision_id + 1,
                    version_type=self._version_type,
                    body=jrc)

        # Only pass through pipeline if file exists
        if 'content' in jrc and not skip_files:
            body['pipeline'] = 'item-file-pipeline'
        if self.client.exists(**es_info):
            del body['version']
            del body['version_type']

        # hfix merge
        # current_app.logger.debug(full_body)
        # self.client.index(**full_body)

        self.client.index(**{**es_info, **body})

    def delete_file_index(self, body, parent_id):
        """Delete file index in Elastic search.

        :param body:
        :param parent_id: Parent item id.
        """
        for lst in body:
            try:
                self.client.delete(id=str(lst),
                                   index=self.es_index,
                                   doc_type=self.file_doc_type,
                                   routing=parent_id)
            except BaseException:
                pass

    def update_publish_status(self, record):
        """Update publish status."""
        self.get_es_index()
        pst = 'publish_status'
        body = {'doc': {pst: record.get(pst)}}
        return self.client.update(
            index=self.es_index,
            doc_type=self.es_doc_type,
            id=str(record.id),
            body=body
        )

    def update_relation_version_is_last(self, version):
        """Update relation version is_last."""
        self.get_es_index()
        pst = 'relation_version_is_last'
        body = {'doc': {pst: version.get('is_last')}}
        return self.client.update(
            index=self.es_index,
            doc_type=self.es_doc_type,
            id=str(version.get('id')),
            body=body
        )

    def update_path(self, record, update_revision=True,
                    update_oai=False, is_deleted=False):
        """Update path.

        Args:
            record ([type]): [description]
            update_revision (bool, optional): [description]. Defaults to True.
            update_oai (bool, optional): [description]. Defaults to False.
            is_deleted (bool, optional): [description]. Defaults to False.

        Returns:
            [type]: [description]

        """
        self.get_es_index()
        path = 'path'
        _oai = '_oai'
        sets = 'sets'
        body = {}
        if not update_oai:
            body = {
                'doc': {
                    path: record.get(path),
                    '_updated': datetime.utcnow().replace(
                        tzinfo=timezone.utc).isoformat()
                }
            }
        else:
            body = {
                'doc': {
                    _oai: {
                        sets: record.get(_oai, {}).get(sets, []),
                    } if record.get(_oai) else {},
                    '_item_metadata': {
                        _oai: {
                            sets: record.get(_oai, {}).get(sets, []),
                        } if record.get(_oai) else {},
                        path: record.get(path)
                    },
                    path: record.get(path) if not is_deleted else [],
                    '_updated': datetime.utcnow().replace(
                        tzinfo=timezone.utc).isoformat()
                }
            }

        if update_revision:
            return self.client.update(
                index=self.es_index,
                doc_type=self.es_doc_type,
                id=str(record.id),
                version=record.revision_id,
                body=body
            )
        else:
            return self.client.update(
                index=self.es_index,
                doc_type=self.es_doc_type,
                id=str(record.id),
                body=body
            )

    def index(self, record):
        """Index a record.

        :param record: Record instance.
        """
        self.get_es_index()

    def delete(self, record):
        """Delete a record.

        Not utilized.

        :param record: Record instance.
        """
        self.get_es_index()

        self.client.delete(id=str(record.id),
                           index=self.es_index,
                           doc_type=self.es_doc_type)

    def delete_by_id(self, uuid):
        """Delete a record by id.

        :param uuid: Record ID.
        """
        try:
            self.get_es_index()
            self.client.delete(id=str(uuid),
                               index=self.es_index,
                               doc_type=self.es_doc_type)
        except Exception as ex:
            current_app.logger.error(ex)

    def get_count_by_index_id(self, tree_path):
        """Get count by index id.

        :param tree_path: Tree_path instance.
        """
        search_query = {
            'query': {
                'term': {
                    'path.tree': tree_path
                }
            }
        }
        self.get_es_index()
        search_result = self.client.count(index=self.es_index,
                                          doc_type=self.es_doc_type,
                                          body=search_query)
        return search_result.get('count')

    def get_pid_by_es_scroll(self, path):
        """Get pid by es scroll.

        :param path:
        :return: _scroll_id
        """
        search_query = {
            "query": {
                "match": {
                    "path.tree": path
                }
            },
            "_source": "_id",
            "size": 3000
        }

        def get_result(result):
            if result:
                hit = result['hits']['hits']
                if hit:
                    return [h.get('_id') for h in hit]
                else:
                    return None
            else:
                return None

        ind, doc_type = self.record_to_index({})
        search_result = self.client.search(index=ind, doc_type=doc_type,
                                           body=search_query, scroll='1m')
        if search_result:
            res = get_result(search_result)
            scroll_id = search_result['_scroll_id']
            if res:
                yield res
                while res:
                    res = self.client.scroll(scroll_id=scroll_id, scroll='1m')
                    yield res

            self.client.clear_scroll(scroll_id=scroll_id)

    def get_metadata_by_item_id(self, item_id):
        """Get metadata of item by id from ES.

        :param item_id: Item ID (UUID).
        :return: Metadata.
        """
        self.get_es_index()
        return self.client.get(index=self.es_index,
                               doc_type=self.es_doc_type,
                               id=str(item_id))

    def update_feedback_mail_list(self, feedback_mail):
        """Update feedback mail info.

        :param feedback_mail: mail list in json format.
        :return: _feedback_mail_id.
        """
        self.get_es_index()
        pst = 'feedback_mail_list'
        body = {'doc': {pst: feedback_mail.get('mail_list')}}
        return self.client.update(
            index=self.es_index,
            doc_type=self.es_doc_type,
            id=str(feedback_mail.get('id')),
            body=body
        )

    def update_author_link(self, author_link):
        """Update author_link info."""
        self.get_es_index()
        pst = 'author_link'
        body = {'doc': {pst: author_link.get('author_link')}}
        return self.client.update(
            index=self.es_index,
            doc_type=self.es_doc_type,
            id=str(author_link.get('id')),
            body=body
        )

    def update_jpcoar_identifier(self, dc, item_id):
        """Update JPCOAR meta data item."""
        self.get_es_index()
        body = {'doc': {'_item_metadata': dc}}
        return self.client.update(
            index=self.es_index,
            doc_type=self.es_doc_type,
            id=str(item_id),
            body=body
        )

    def __build_bulk_es_data(self, updated_data):
        """Build ElasticSearch data.

        :param updated_data: Records data.
        """
        for record in updated_data:
            es_data = dict(
                _id=str(record.get('_id')),
                _index=self.es_index,
                _type=self.es_doc_type,
                _source=record.get('_source'),
            )
            yield es_data

    def bulk_update(self, updated_data):
        """Bulk update.

        :param updated_data: Updated data.
        """
        self.get_es_index()
        es_data = self.__build_bulk_es_data(updated_data)
        if es_data:
            success, failed = bulk(self.client, es_data)
            if len(failed) > 0:
                for error in failed:
                    current_app.logger.error(error)


class WekoDeposit(Deposit):
    """Define API for changing deposit state."""

    indexer = WekoIndexer()

    deposit_fetcher = staticmethod(weko_deposit_fetcher)

    deposit_minter = staticmethod(weko_deposit_minter)

    data = None
    jrc = None
    is_edit = False

    @property
    def item_metadata(self):
        """Return the Item metadata."""
        return ItemsMetadata.get_record(self.id).dumps()

    def is_published(self):
        """Check if deposit is published."""
        return self['_deposit'].get('pid') is not None

    @preserve(fields=('_deposit', '$schema'))
    def merge_with_published(self):
        """Merge changes with latest published version."""
        pid, first = self.fetch_published()
        lca = first.revisions[self['_deposit']['pid']['revision_id']]
        # ignore _deposit and $schema field
        args = [lca.dumps(), first.dumps(), self.dumps()]
        for arg in args:
            if '$schema' in arg:
                del arg['$schema']
            if '_deposit' in arg:
                del arg['_deposit']
            if 'control_number' in arg:
                del arg['control_number']
        args.append({})
        m = Merger(*args)
        try:
            m.run()
        except UnresolvedConflictsException:
            raise MergeConflict()
        return self._patch(m.unified_patches, lca)

    @staticmethod
    def _patch(diff_result, destination, in_place=False):
        """Patch the diff result to the destination dictionary.

        :param diff_result: Changes returned by ``diff``.
        :param destination: Structure to apply the changes to.
        :param in_place: By default, destination dictionary is deep copied
                         before applying the patch, and the copy is returned.
                         Setting ``in_place=True`` means that patch will apply
                         the changes directly to and return the destination
                         structure.
        """
        (ADD, REMOVE, CHANGE) = (
            'add', 'remove', 'change')
        if not in_place:
            destination = copy.deepcopy(destination)

        def add(node, changes):
            for key, value in changes:
                dest = dot_lookup(destination, node)
                if isinstance(dest, list):
                    dest.insert(key, value)
                elif isinstance(dest, set):
                    dest |= value
                else:
                    dest[key] = value

        def change(node, changes):
            dest = dot_lookup(destination, node, parent=True)
            if isinstance(node, str):
                last_node = node.split('.')[-1]
            else:
                last_node = node[-1]
            if isinstance(dest, list):
                last_node = int(last_node)
            _, value = changes
            dest[last_node] = value

        def remove(node, changes):
            for key, value in changes:
                dest = dot_lookup(destination, node)
                if isinstance(dest, set):
                    dest -= value
                else:
                    if isinstance(dest, list) and isinstance(key, int) and len(
                            dest) > key:
                        del dest[key]
                    elif isinstance(dest, dict) and dest.get(key):
                        del dest[key]

        patchers = {
            REMOVE: remove,
            ADD: add,
            CHANGE: change
        }

        for action, node, changes in diff_result:
            patchers[action](node, changes)

        return destination

    def _publish_new(self, id_=None):
        """Override the publish new to avoid creating multiple pids."""
        id_ = id_ or uuid.uuid4()
        record_pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', object_uuid=self.id).first()

        self['_deposit']['pid'] = {
            'type': record_pid.pid_type,
            'value': record_pid.pid_value,
            'revision_id': 0,
        }

        data = dict(self.dumps())
        data['$schema'] = self.record_schema

        with self._process_files(id_, data):
            record = self.published_record_class.create(data, id_=id_)

        return record

    def _update_version_id(self, metas, bucket_id):
        """
        Update 'version_id' of file_metadatas.

        parameter:
            metas: Record Metadata.
            bucket_id: Bucket UUID.
        return:
            response
        """
        _filename_prop = 'filename'

        files_versions = ObjectVersion.get_by_bucket(bucket=bucket_id,
                                                     with_deleted=True).all()
        files_versions = {x.key: x.version_id for x in files_versions}
        file_meta = []

        for item in metas:
            if not isinstance(metas[item], dict) or \
                    not metas[item].get('attribute_value_mlt'):
                continue
            itemmeta = metas[item]['attribute_value_mlt']
            if itemmeta and isinstance(itemmeta, list) \
                and isinstance(itemmeta[0], dict) \
                    and itemmeta[0].get(_filename_prop):
                file_meta.extend(itemmeta)
            elif isinstance(itemmeta, dict) \
                    and itemmeta.get(_filename_prop):
                file_meta.extend([itemmeta])

        if not file_meta:
            return False

        for item in file_meta:
            item['version_id'] = str(files_versions.get(
                item.get(_filename_prop), ''))

        return True

    def publish(self, pid=None, id_=None):
        """Publish the deposit."""
        deposit = None
        try:
            deposit = self.publish_without_commit(pid, id_)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return deposit

    def publish_without_commit(self, pid=None, id_=None):
        """Publish the deposit without commit."""
        if not self.data:
            self.data = self.get('_deposit', {})
        if 'control_number' in self:
            self.pop('control_number')
        if '$schema' not in self:
            self['$schema'] = current_app.extensions['invenio-jsonschemas']. \
                path_to_url(current_app.config['DEPOSIT_DEFAULT_JSONSCHEMA'])
        self.is_edit = True

        deposit = super(WekoDeposit, self).publish(pid, id_)
        # update relation version current to ES
        recid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            object_uuid=self.id
        ).one_or_none()
        relations = serialize_relations(recid)
        if relations and 'version' in relations:
            relations_ver = relations['version'][0]
            relations_ver['id'] = recid.object_uuid
            relations_ver['is_last'] = relations_ver.get('index') == 0
            self.indexer.update_relation_version_is_last(relations_ver)

        return deposit

    @classmethod
    def create(cls, data, id_=None, recid=None):
        """Create a deposit.

        Adds bucket creation immediately on deposit creation.
        """
        if '$schema' in data:
            data.pop('$schema')

        bucket = Bucket.create(
            quota_size=current_app.config['WEKO_BUCKET_QUOTA_SIZE'],
            max_file_size=current_app.config['WEKO_MAX_FILE_SIZE'],
        )
        data['_buckets'] = {'deposit': str(bucket.id)}

        # save user_name & display name.
        if current_user and current_user.is_authenticated:
            user = UserProfile.get_by_userid(current_user.get_id())
            if '_deposit' in data:
                data['_deposit']['owners_ext'] = {
                    'username': user._username if user else '',
                    'displayname': user._displayname if user else '',
                    'email': current_user.email
                }

        try:
            if recid:
                deposit = super(WekoDeposit, cls).create(
                    data,
                    id_=id_,
                    recid=recid
                )
            else:
                deposit = super(WekoDeposit, cls).create(data, id_=id_)

            record_id = 0
            if data.get('_deposit'):
                record_id = str(data['_deposit']['id'])
            parent_pid = PersistentIdentifier.create(
                'parent',
                'parent:{0}'.format(record_id),
                object_type='rec',
                object_uuid=deposit.id,
                status=PIDStatus.REGISTERED
            )
            db.session.commit()
        except BaseException as ex:
            raise ex

        RecordsBuckets.create(record=deposit.model, bucket=bucket)

        recid = PersistentIdentifier.get('recid', record_id)
        depid = PersistentIdentifier.get('depid', record_id)
        PIDVersioning(parent=parent_pid).insert_draft_child(child=recid)
        RecordDraft.link(recid, depid)
        # Update this object_uuid for item_id of activity.
        if session and 'activity_info' in session:
            activity = session['activity_info']
            from weko_workflow.api import WorkActivity
            workactivity = WorkActivity()
            workactivity.upt_activity_item(activity, str(recid.object_uuid))
        return deposit

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def update(self, *args, **kwargs):
        """Update only drafts."""
        self['_deposit']['status'] = 'draft'
        if len(args) > 1:
            dc, deleted_items = self.convert_item_metadata(args[0], args[1])
        else:
            dc, deleted_items = self.convert_item_metadata(args[0])
        super(WekoDeposit, self).update(dc)
        if deleted_items:
            for key in deleted_items:
                if key in self:
                    self.pop(key)

        #        if 'pid' in self['_deposit']:
        #            self['_deposit']['pid']['revision_id'] += 1
        try:
            if has_request_context():
                if current_user:
                    user_id = current_user.get_id()
                else:
                    user_id = -1
                item_created.send(
                    current_app._get_current_object(),
                    user_id=user_id,
                    item_id=self.pid,
                    item_title=self.data['title']
                )
        except BaseException:
            import traceback
            current_app.logger.error(traceback.format_exc())
            abort(500, 'MAPPING_ERROR')

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def clear(self, *args, **kwargs):
        """Clear only drafts."""
        if self['_deposit']['status'] != 'draft':
            return
        super(WekoDeposit, self).clear(*args, **kwargs)

    @index(delete=True)
    def delete(self, force=True, pid=None):
        """Delete deposit.

        Status required: ``'draft'``.

        :param force: Force deposit delete.  (Default: ``True``)
        :param pid: Force pid object.  (Default: ``None``)
        :returns: A new Deposit object.
        """
        # Delete the recid
        recid = PersistentIdentifier.get(
            pid_type='recid', pid_value=self.pid.pid_value)

        if recid.status == PIDStatus.RESERVED:
            db.session.delete(recid)

        # if this item has been deleted
        self.delete_es_index_attempt(recid)

        # Completely remove bucket
        bucket = self.files.bucket
        with db.session.begin_nested():
            # Remove Record-Bucket link
            RecordsBuckets.query.filter_by(record_id=self.id).delete()
            mp_q = MultipartObject.query_by_bucket(bucket)
            # Remove multipart objects
            Part.query.filter(
                Part.upload_id.in_(mp_q.with_entities(
                    MultipartObject.upload_id).subquery())
            ).delete(synchronize_session='fetch')
            mp_q.delete(synchronize_session='fetch')
        bucket.locked = False
        bucket.remove()

        return super(Deposit, self).delete()

    def commit(self, *args, **kwargs):
        """Store changes on current instance in database and index it."""
        super(WekoDeposit, self).commit(*args, **kwargs)
        record = RecordMetadata.query.get(self.pid.object_uuid)
        if self.data and len(self.data):
            # save item metadata
            self.save_or_update_item_metadata()

            if self.jrc and len(self.jrc):
                if record and record.json and '_oai' in record.json:
                    self.jrc['_oai'] = record.json.get('_oai')
                if 'path' in self.jrc and '_oai' in self.jrc \
                        and ('sets' not in self.jrc['_oai']
                             or not self.jrc['_oai']['sets']):
                    setspec_list = self.jrc['path'] or []
                    #setspec_list = OAISet.query.filter_by(
                    #    id=self.jrc['path']).one_or_none()
                    if setspec_list:
                        #self.jrc['_oai'].update(dict(sets=setspec_list.spec))
                        self.jrc['_oai'].update(dict(sets=setspec_list))
                # upload item metadata to Elasticsearch
                set_timestamp(self.jrc, self.created, self.updated)

                # Get file contents
                self.get_content_files()

                try:
                    # Upload file content to Elasticsearch
                    self.indexer.upload_metadata(self.jrc,
                                                 self.pid.object_uuid,
                                                 self.revision_id)
                except TransportError as err:
                    err_passing_config = current_app.config.get(
                        'WEKO_DEPOSIT_ES_PARSING_ERROR_PROCESS_ENABLE')
                    parse_err = current_app.config.get(
                        'WEKO_DEPOSIT_ES_PARSING_ERROR_KEYWORD')
                    if err_passing_config and \
                            parse_err in err.info["error"]["reason"]:
                        self.delete_content_files()
                        self.indexer.upload_metadata(self.jrc,
                                                     self.pid.object_uuid,
                                                     self.revision_id,
                                                     True)
                        record_id = self['_deposit']['id']
                        message = 'Failed to parse file from item {}'
                        current_app.logger.warn(message.format(record_id))
                    else:
                        raise err

                # Remove large base64 files for release memory
                if self.jrc.get('content'):
                    for content in self.jrc['content']:
                        if content.get('file'):
                            del content['file']

        # fix schema url
        if record and record.json and '$schema' in record.json:
            record.json.pop('$schema')
            if record.json.get('_buckets'):
                self._update_version_id(record.json,
                                        record.json['_buckets']['deposit'])
            flag_modified(record, 'json')
            db.session.merge(record)

    def newversion(self, pid=None, is_draft=False):
        """Create a new version deposit."""
        deposit = None
        try:
            if not self.is_published():
                raise PIDInvalidAction()

            # Check that there is not a newer draft version for this record
            # and this is the latest version
            versioning = PIDVersioning(child=pid)
            record = WekoDeposit.get_record(pid.object_uuid)

            assert PIDStatus.REGISTERED == pid.status
            if not record or not versioning.exists or versioning.draft_child:
                return None

            data = record.dumps()
            owners = data['_deposit']['owners']
            keys_to_remove = ('_deposit', 'doi', '_oai',
                              '_files', '_buckets', '$schema')
            for k in keys_to_remove:
                data.pop(k, None)

            draft_id = '{0}.{1}'.format(
                pid.pid_value,
                0 if is_draft else get_latest_version_id(pid.pid_value))

            # NOTE: We call the superclass `create()` method, because
            # we don't want a new empty bucket, but
            # an unlocked snapshot of the old record's bucket.
            deposit = super(
                WekoDeposit,
                self).create(data, recid=draft_id)
            # Injecting owners is required in case of creating new
            # version this outside of request context

            deposit['_deposit']['owners'] = owners

            recid = PersistentIdentifier.get(
                'recid', str(data['_deposit']['id']))
            depid = PersistentIdentifier.get(
                'depid', str(data['_deposit']['id']))

            PIDVersioning(
                parent=versioning.parent).insert_draft_child(
                child=recid)
            RecordDraft.link(recid, depid)

            if is_draft:
                with db.session.begin_nested():
                    # Set relation type of draft record is 3: Draft
                    parent_pid = PIDVersioning(child=recid).parent
                    relation = PIDRelation.query. \
                        filter_by(parent=parent_pid,
                                  child=recid).one_or_none()
                    relation.relation_type = 3
                db.session.merge(relation)

            snapshot = record.files.bucket. \
                snapshot(lock=False)
            snapshot.locked = False
            deposit['_buckets'] = {'deposit': str(snapshot.id)}
            RecordsBuckets.create(record=deposit.model,
                                  bucket=snapshot)

            index = {'index': self.get('path', []),
                     'actions': self.get('publish_status')}
            if 'activity_info' in session:
                del session['activity_info']
            if is_draft:
                from weko_workflow.utils import convert_record_to_item_metadata
                item_metadata = convert_record_to_item_metadata(record)
            else:
                item_metadata = ItemsMetadata.get_record(
                    pid.object_uuid).dumps()
            item_metadata.pop('id', None)
            args = [index, item_metadata]
            deposit.update(*args)
            deposit.commit()
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return deposit

    def get_content_files(self):
        """Get content file metadata."""
        from weko_workflow.utils import get_url_root
        contents = []
        fmd = self.get_file_data()
        if fmd:
            for file in self.files:
                if isinstance(fmd, list):
                    for lst in fmd:
                        filename = lst.get('filename')
                        if file.obj.key == filename:
                            lst.update({'mimetype': file.obj.mimetype})
                            lst.update(
                                {'version_id': str(file.obj.version_id)})

                            # update file url
                            url_metadata = lst.get('url', {})
                            url_metadata['url'] = '{}record/{}/files/{}' \
                                .format(get_url_root(),
                                        self['recid'], filename)
                            lst.update({'url': url_metadata})

                            # update file_files's json
                            file.obj.file.update_json(lst)

                            # upload file metadata to Elasticsearch
                            try:
                                file_size_max = current_app.config[
                                    'WEKO_MAX_FILE_SIZE_FOR_ES']
                                mimetypes = current_app.config[
                                    'WEKO_MIMETYPE_WHITELIST_FOR_ES']
                                content = lst.copy()
                                file_content = ""
                                if file.obj.file.size <= file_size_max and \
                                        file.obj.mimetype in mimetypes:
                                    file_content = file.obj.file.read_file(lst)
                                content.update({"file": file_content})
                                contents.append(content)

                            except Exception as e:
                                import traceback
                                current_app.logger.error(
                                    traceback.format_exc())
                                abort(500, '{}'.format(str(e)))
                            break
            self.jrc.update({'content': contents})

    def get_file_data(self):
        """Get file data."""
        file_data = []
        data = self.data or self.item_metadata
        for key in data:
            if isinstance(data.get(key), list):
                for item in data.get(key):
                    if (isinstance(item, dict) or isinstance(item, list)) \
                            and 'filename' in item:
                        file_data.extend(data.get(key))
                        break
        return file_data

    def save_or_update_item_metadata(self):
        """Save or update item metadata.

        Save when register a new item type, Update when edit an item
        type.
        """
        deposit_owners = self.get('_deposit', {}).get('owners')
        owner = str(deposit_owners[0] if deposit_owners else 1)
        if owner:
            dc_owner = self.data.get("owner", None)
            if not dc_owner:
                self.data.update(dict(owner=owner))

        if ItemMetadata.query.filter_by(id=self.id).first():
            obj = ItemsMetadata.get_record(self.id)
            obj.update(self.data)
            if self.data.get('deleted_items'):
                for key in self.data.get('deleted_items'):
                    if key in obj:
                        obj.pop(key)
            obj.commit()
        else:
            if self.data.get('deleted_items'):
                self.data.pop('deleted_items')
            ItemsMetadata.create(self.data, id_=self.pid.object_uuid,
                                 item_type_id=self.get('item_type_id'))

    def delete_old_file_index(self):
        """Delete old file index before file upload when edit an item."""
        if self.is_edit:
            lst = ObjectVersion.get_by_bucket(
                self.files.bucket, True).filter_by(is_head=False).all()
            klst = []
            for obj in lst:
                if obj.file_id:
                    klst.append(obj.file_id)
            if klst:
                self.indexer.delete_file_index(klst, self.pid.object_uuid)

    def convert_item_metadata(self, index_obj, data=None):
        """Convert Item Metadat.

        1. Convert Item Metadata
        2. Inject index tree id to dict
        3. Set Publish Status
        :param index_obj:
        :return: dc
        """
        # if this item has been deleted
        self.delete_es_index_attempt(self.pid)

        try:
            if not data:
                datastore = RedisStore(redis.StrictRedis.from_url(
                    current_app.config['CACHE_REDIS_URL']))
                cache_key = current_app.config[
                    'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(
                    pid_value=self.pid.pid_value)
                # Check exist item cache before delete
                if datastore.redis.exists(cache_key):
                    data_str = datastore.get(cache_key)
                    if not index_obj.get('is_save_path'):
                        datastore.delete(cache_key)
                    data = json.loads(data_str.decode('utf-8'))
        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            abort(500, 'Failed to register item!')
        # Get index path
        index_lst = index_obj.get('index', [])
        # Prepare index id list if the current index_lst is a path list
        if index_lst:
            index_id_lst = []
            for _index in index_lst:
                indexes = str(_index).split('/')
                index_id_lst.append(indexes[len(indexes) - 1])
            index_lst = index_id_lst

        plst = Indexes.get_path_list(index_lst)

        if not plst or len(index_lst) != len(plst):
            raise PIDResolveRESTError(
                description='Any tree index has been deleted')

        # Convert item meta data
        try:
            deposit_owners = self.get('_deposit', {}).get('owners')
            owner_id = str(deposit_owners[0] if deposit_owners else 1)
            dc, jrc, is_edit = json_loader(data, self.pid, owner_id=owner_id)
            dc['publish_date'] = data.get('pubdate')
            dc['title'] = [data.get('title')]
            dc['relation_version_is_last'] = True
            self.data = data
            self.jrc = jrc
            self.is_edit = is_edit
            self._convert_jpcoar_data_to_es()
        except RuntimeError:
            raise
        except BaseException:
            import traceback
            current_app.logger.error(traceback.format_exc())
            abort(500, 'MAPPING_ERROR')

        # Save Index Path on ES
        jrc.update(dict(path=index_lst))
        # current_app.logger.debug(jrc)
        # add at 20181121 start
        sub_sort = {}
        for pth in index_lst:
            # es setting
            sub_sort[pth[-13:]] = ""
        dc.update(dict(path=index_lst))
        pubs = '1'
        actions = index_obj.get('actions')
        if actions == 'publish' or actions == '0':
            pubs = '0'
        elif 'id' in data:
            recid = PersistentIdentifier.query.filter_by(
                pid_type='recid', pid_value=data['id']).first()
            rec = RecordMetadata.query.filter_by(id=recid.object_uuid).first()
            pubs = rec.json['publish_status']

        ps = dict(publish_status=pubs)
        jrc.update(ps)
        dc.update(ps)
        return dc, data.get('deleted_items')

    def _convert_description_to_object(self):
        """Convert description to object."""
        description_key = "description"
        if isinstance(self.jrc, dict) and self.jrc.get(description_key):
            _description = self.jrc.get(description_key)
            _new_description = []
            if isinstance(_description, list):
                for data in _description:
                    if isinstance(data, str):
                        _new_description.append({"value": data})
                    else:
                        _new_description.append(data)
            if _new_description:
                self.jrc[description_key] = _new_description

    def _convert_jpcoar_data_to_es(self):
        """Convert data jpcoar to es."""
        # Convert description to object.
        self._convert_description_to_object()

        # Convert data for geo location.
        self._convert_data_for_geo_location()

    def _convert_data_for_geo_location(self):
        """Convert geo location to object."""
        def _convert_geo_location(value):
            _point = []
            if isinstance(value.get("pointLongitude"), list) and isinstance(
                    value.get("pointLatitude"), list):
                lat_len = len(value.get("pointLatitude"))
                for _idx, _value in enumerate(value.get("pointLongitude")):
                    _point.append({
                        "lat": value.get("pointLatitude")[
                            _idx] if _idx < lat_len else "",
                        "lon": _value
                    })
            return _point

        def _convert_geo_location_box():
            point_box = {}
            jpcoar_north_east_point = {
                "pointLatitude": v.get("northBoundLatitude"),
                "pointLongitude": v.get("eastBoundLongitude"),
            }
            jpcoar_south_west_point = {
                "pointLatitude": v.get("southBoundLatitude"),
                "pointLongitude": v.get("westBoundLongitude"),
            }
            es_north_east_point = _convert_geo_location(
                jpcoar_north_east_point)
            es_south_west_point = _convert_geo_location(
                jpcoar_south_west_point)
            if es_north_east_point:
                point_box['northEastPoint'] = es_north_east_point
            if es_south_west_point:
                point_box['southWestPoint'] = es_south_west_point
            return point_box

        geo_location_key = "geoLocation"
        if isinstance(self.jrc, dict) and self.jrc.get(geo_location_key):
            geo_location = self.jrc.get(geo_location_key)
            new_data = {}
            for k, v in geo_location.items():
                if "geoLocationPlace" == k:
                    new_data[k] = v
                elif "geoLocationPoint" == k:
                    point = _convert_geo_location(v)
                    if point:
                        new_data[k] = point
                elif "geoLocationBox" == k:
                    point = _convert_geo_location_box()
                    if point:
                        new_data[k] = point
            if new_data:
                self.jrc[geo_location_key] = new_data

    @classmethod
    def delete_by_index_tree_id(cls, index_id: str, ignore_items: list = []):
        """Delete by index tree id."""
        if index_id:
            index_id = str(index_id)
        obj_ids = next((cls.indexer.get_pid_by_es_scroll(index_id)), [])
        try:
            for obj_uuid in obj_ids:
                r = RecordMetadata.query.filter_by(id=obj_uuid).first()
                if r.json['recid'].split('.')[0] in ignore_items:
                    continue
                try:
                    r.json['path'].remove(index_id)
                    flag_modified(r, 'json')
                except BaseException as bex:
                    current_app.logger.error(bex)
                if r.json and not r.json['path']:
                    from weko_records_ui.utils import soft_delete
                    soft_delete(obj_uuid)
                else:
                    dep = WekoDeposit(r.json, r)
                    dep.indexer.update_path(dep, update_revision=False)
            db.session.commit()
        except Exception as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise ex

    def update_pid_by_index_tree_id(self, path):
        """Update pid by index tree id.

        :param path:
        :return: True: process success False: process failed
        """
        p = PersistentIdentifier
        try:
            dt = datetime.utcnow()
            with db.session.begin_nested():
                for result in self.indexer.get_pid_by_es_scroll(path):
                    db.session.query(p). \
                        filter(p.object_uuid.in_(result),
                               p.object_type == 'rec'). \
                        update({p.status: 'D', p.updated: dt},
                               synchronize_session=False)
                    result.clear()
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def update_item_by_task(self, *args, **kwargs):
        """Update item by task."""
        return super(Deposit, self).commit(*args, **kwargs)

    def delete_es_index_attempt(self, pid):
        """Delete es index attempt."""
        # if this item has been deleted
        if pid.status == PIDStatus.DELETED:
            # attempt to delete index on es
            try:
                self.indexer.delete(self)
            except BaseException:
                pass
            raise PIDResolveRESTError(description='This item has been deleted')

    def update_author_link(self, author_link):
        """Index feedback mail list."""
        item_id = self.id
        if author_link:
            author_link_info = {
                "id": item_id,
                "author_link": author_link
            }
            self.indexer.update_author_link(author_link_info)

    def update_feedback_mail(self):
        """Index feedback mail list."""
        item_id = self.id
        mail_list = FeedbackMailList.get_mail_list_by_item_id(item_id)
        if mail_list:
            feedback_mail = {
                "id": item_id,
                "mail_list": mail_list
            }
            self.indexer.update_feedback_mail_list(feedback_mail)

    def remove_feedback_mail(self):
        """Remove feedback mail list."""
        feedback_mail = {
            "id": self.id,
            "mail_list": []
        }
        self.indexer.update_feedback_mail_list(feedback_mail)

    def clean_unuse_file_contents(self, item_id, pre_object_versions,
                                  new_object_versions, is_import=False):
        """Remove file not used after replaced in keep version mode."""
        from weko_workflow.utils import update_cache_data
        pre_file_ids = [obv.file_id for obv in pre_object_versions]
        new_file_ids = [obv.file_id for obv in new_object_versions]
        diff_list = list(set(pre_file_ids) - set(new_file_ids))
        unuse_file_ids = [data[0] for data in
                          ObjectVersion.num_version_link_to_files(diff_list)
                          if data[1] <= 1]
        list_unuse_uri = []
        for obv in pre_object_versions:
            if obv.file_id in unuse_file_ids:
                obv.remove()
                obv.file.delete()
                if is_import:
                    list_unuse_uri.append(obv.file.uri)
                else:
                    obv.file.storage().delete()
        if list_unuse_uri:
            cache_key = current_app \
                .config['WEKO_SEARCH_UI_IMPORT_UNUSE_FILES_URI'] \
                .format(item_id)
            update_cache_data(cache_key, list_unuse_uri, 0)

    def merge_data_to_record_without_version(self, pid, keep_version=False,
                                             is_import=False):
        """Update changes to current record by record from PID."""
        with db.session.begin_nested():
            # update item_metadata
            index = {'index': self.get('path', []),
                     'actions': self.get('publish_status')}
            item_metadata = ItemsMetadata.get_record(pid.object_uuid).dumps()
            item_id = item_metadata.get('id')
            item_metadata.pop('id', None)
            item_metadata.pop('control_number', None)

            # Clone bucket
            _deposit = WekoDeposit.get_record(pid.object_uuid)
            # Get draft bucket's data
            sync_bucket = RecordsBuckets.query.filter_by(
                record_id=self.id).first()
            sync_bucket.bucket.locked = False
            snapshot = Bucket.get(
                _deposit.files.bucket.id).snapshot(lock=False)
            bucket = Bucket.get(sync_bucket.bucket_id)
            if keep_version:
                self.clean_unuse_file_contents(item_id, bucket.objects,
                                               snapshot.objects, is_import)
            snapshot.locked = False
            sync_bucket.bucket = snapshot
            bucket.locked = False

            if not RecordsBuckets.query.filter_by(
                    bucket_id=bucket.id).all():
                bucket.remove()

            bucket = {
                "_buckets": {
                    "deposit": str(snapshot.id)
                }
            }

            args = [index, item_metadata]
            self.update(*args)
            # Update '_buckets'
            super(WekoDeposit, self).update(bucket)
            self.commit()
            # update records_metadata
            flag_modified(self.model, 'json')
            db.session.add(self.model)
            db.session.add(sync_bucket)

        return self.__class__(self.model.json, model=self.model)

    def prepare_draft_item(self, recid):
        """
        Create draft version of main record.

        parameter:
            recid: recid
        return:
            response
        """
        draft_deposit = self.newversion(recid, is_draft=True)

        return draft_deposit

    def delete_content_files(self):
        """Delete 'file' from content file metadata."""
        if self.jrc.get('content'):
            for content in self.jrc['content']:
                if content.get('file'):
                    del content['file']


class WekoRecord(Record):
    """Extend Record obj for record ui."""

    file_cls = WekoFileObject
    record_fetcher = staticmethod(weko_deposit_fetcher)

    @property
    def pid(self):
        """Return an instance of record PID."""
        pid = self.record_fetcher(self.id, self)
        obj = PersistentIdentifier.get(pid.pid_type, pid.pid_value)
        return obj

    @property
    def pid_recid(self):
        """Return an instance of record PID."""
        pid = self.record_fetcher(self.id, self)
        obj = PersistentIdentifier.get('recid', pid.pid_value)
        return obj

    @property
    def hide_file(self):
        """Whether the file property is hidden.

        Note: This function just works fine if file property has value.
        """
        hide_file = False
        item_type_id = self.get('item_type_id')
        solst, meta_options = get_options_and_order_list(item_type_id)
        for lst in solst:
            key = lst[0]
            val = self.get(key)
            option = meta_options.get(key, {}).get('option')
            # Just get 'File'
            if not (val and option) or val.get('attribute_type') != "file":
                continue
            if option.get("hidden"):
                hide_file = True
            break
        return hide_file

    @property
    def navi(self):
        """Return the path name."""
        navs = Indexes.get_path_name(self.get('path', []))

        community = request.args.get('community', None)
        if not community:
            return navs

        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(community)
        comm_navs = [item for item in navs if str(
            comm.index.id) in item.path.split('/')]
        return comm_navs

    @property
    def item_type_info(self):
        """Return the information of item type."""
        item_type = ItemTypes.get_by_id(self.get('item_type_id'))
        return '{}({})'.format(item_type.item_type_name.name, item_type.tag)

    @property
    def items_show_list(self):
        """Return the item show list."""
        items = []
        settings = AdminSettings.get('items_display_settings')
        hide_email_flag = not settings.items_display_email
        solst, meta_options = get_options_and_order_list(
            self.get('item_type_id'))
        item_type = ItemTypes.get_by_id(self.get('item_type_id'))
        meta_list = item_type.render.get('meta_list', []) if item_type else {}

        for lst in solst:
            key = lst[0]

            val = self.get(key)
            option = meta_options.get(key, {}).get('option')
            if not val or not option:
                continue

            hidden = option.get("hidden")
            if hidden:
                continue

            mlt = val.get('attribute_value_mlt')
            if mlt is not None:
                mlt = copy.deepcopy(mlt)
                self.__remove_special_character_of_weko2(mlt)
                nval = dict()
                nval['attribute_name'] = val.get('attribute_name')
                nval['attribute_name_i18n'] = lst[2] or val.get(
                    'attribute_name')
                nval['attribute_type'] = val.get('attribute_type')

                if nval['attribute_name'] == 'Reference' \
                        or nval['attribute_type'] == 'file':
                    file_metadata = copy.deepcopy(mlt)
                    if nval['attribute_type'] == 'file':
                        file_metadata = self. \
                            __remove_file_metadata_do_not_publish(
                                file_metadata)
                    nval['attribute_value_mlt'] = \
                        get_all_items(
                            file_metadata, copy.deepcopy(solst), True)
                else:
                    is_author = nval['attribute_type'] == 'creator'
                    is_thumbnail = any(
                        'subitem_thumbnail' in data for data in mlt)
                    sys_bibliographic = _FormatSysBibliographicInformation(
                        copy.deepcopy(mlt),
                        copy.deepcopy(solst)
                    )
                    if is_author:
                        creators = self._get_creator(mlt, hide_email_flag)
                        nval['attribute_value_mlt'] = creators
                    elif is_thumbnail:
                        nval['is_thumbnail'] = True
                    elif sys_bibliographic.is_bibliographic():
                        nval['attribute_value_mlt'] = \
                            sys_bibliographic.get_bibliographic_list(False)
                    else:
                        if meta_list.get(key, {}).get('input_type') == 'text':
                            for iter in mlt:
                                if iter.get('interim'):
                                    iter['interim'] = iter[
                                        'interim'].replace("\n", " ")
                        nval['attribute_value_mlt'] = \
                            get_attribute_value_all_items(
                                key,
                                copy.deepcopy(mlt),
                                copy.deepcopy(solst),
                                is_author,
                                hide_email_flag,
                                True,
                                option.get("oneline", False))
                items.append(nval)
            else:
                val['attribute_name_i18n'] = lst[2] or val.get(
                    'attribute_name')

                if meta_list.get(key, {}).get('input_type') == 'text':
                    if 'attribute_value' in val:
                        val['attribute_value'] = val['attribute_value'].replace(
                            "\n", " ")
                items.append(val)

        return items

    @property
    def display_file_info(self):
        """Display file information.

        :return:
        """
        item_type_id = self.get('item_type_id')
        solst, meta_options = get_options_and_order_list(item_type_id)
        items = []
        for lst in solst:
            key = lst[0]
            val = self.get(key)
            option = meta_options.get(key, {}).get('option')
            if not val or not option:
                continue
            # Just get data of 'File' and 'Pubdate'.
            if val.get('attribute_type') != "file" and key != 'pubdate':
                continue
            # Check option hide.
            if option.get("hidden"):
                continue
            mlt = val.get('attribute_value_mlt')
            if mlt is not None:
                # Processing get files.
                mlt = copy.deepcopy(mlt)
                # Get file with current version id.
                file_metadata_temp = []
                exclude_attr = [
                    'displaytype', 'accessrole', 'licensetype', 'licensefree']
                filename = request.args.get("filename", None)
                file_order = int(request.args.get("file_order", -1))
                for idx, f in enumerate(mlt):
                    if (f.get('filename') == filename and file_order == -1) \
                            or file_order == idx:
                        # Exclude attributes which is not use.
                        for ea in exclude_attr:
                            if f.get(ea, None):
                                del f[ea]
                        file_metadata_temp.append(f)
                file_metadata = file_metadata_temp
                nval = dict()
                nval['attribute_name'] = val.get('attribute_name')
                nval['attribute_name_i18n'] = lst[2] or val.get(
                    'attribute_name')
                nval['attribute_type'] = val.get('attribute_type')
                # Format structure to display.
                nval['attribute_value_mlt'] = \
                    get_attribute_value_all_items(key, file_metadata,
                                                  copy.deepcopy(solst))
                items.append(nval)
            else:
                # Processing get pubdate.
                attr_name = val.get('attribute_value', '')
                val['attribute_name_i18n'] = lst[2] or attr_name
                val['attribute_value_mlt'] = [[[[{
                    val['attribute_name_i18n']: attr_name}]]]]
                items.append(val)
        return items

    def __remove_special_character_of_weko2(self, metadata):
        """Remove special character of WEKO2.

        :param metadata:
        """
        if isinstance(metadata, dict):
            for k, val in metadata.items():
                if isinstance(val, str):
                    metadata[k] = remove_weko2_special_character(val)
                else:
                    self.__remove_special_character_of_weko2(val)
        elif isinstance(metadata, list):
            for idx, val in enumerate(metadata):
                if isinstance(val, str):
                    metadata[idx] = remove_weko2_special_character(val)
                else:
                    self.__remove_special_character_of_weko2(val)

    @staticmethod
    def _get_creator(meta_data, hide_email_flag):
        creators = []
        if meta_data:
            for creator_data in meta_data:
                creator_dict = _FormatSysCreator(creator_data).format_creator()
                identifiers = WEKO_DEPOSIT_SYS_CREATOR_KEY['identifiers']
                creator_mails = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_mails']
                if identifiers in creator_data:
                    creator_dict[identifiers] = creator_data[identifiers]
                if creator_mails in creator_data and not hide_email_flag:
                    creator_dict[creator_mails] = creator_data[creator_mails]
                creators.append(creator_dict)
        return creators

    def __remove_file_metadata_do_not_publish(self, file_metadata_list):
        """Remove file metadata do not publish.

        :param file_metadata_list: File metadata list.
        :return: New file metadata list.
        """
        new_file_metadata_list = []
        user_id_list = self.get('_deposit', {}).get('owners', [])
        for file in file_metadata_list:
            is_permissed_user = self.__check_user_permission(user_id_list)
            is_open_no = self.is_do_not_publish(file)
            if self.is_input_open_access_date(file):
                if not self.is_future_open_date(self,
                                                file) or is_permissed_user:
                    new_file_metadata_list.append(file)
                else:
                    continue
            elif not (is_open_no and not is_permissed_user):
                new_file_metadata_list.append(file)
        return new_file_metadata_list

    @staticmethod
    def __check_user_permission(user_id_list):
        """Check user permission.

        :return: True if the login user is allowed to display file metadata.
        """
        is_ok = False
        # Check guest user
        if not current_user.is_authenticated:
            return is_ok
        # Check registered user
        elif current_user and current_user.id in user_id_list:
            is_ok = True
        # Check super users
        else:
            super_users = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] + \
                current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
            for role in list(current_user.roles or []):
                if role.name in super_users:
                    is_ok = True
                    break
        return is_ok

    @staticmethod
    def is_input_open_access_date(file_metadata):
        """Check access of file is 'Input Open Access Date'.

        :return: True is 'Input Open Access Date'.
        """
        access_role = file_metadata.get('accessrole', '')
        return access_role == 'open_date'

    @staticmethod
    def is_do_not_publish(file_metadata):
        """Check access of file is 'Do not Publish'.

        :return: True is 'Do not Publish'.
        """
        access_role = file_metadata.get('accessrole', '')
        return access_role == 'open_no'

    @staticmethod
    def get_open_date_value(file_metadata):
        """Get value of 'Open Date' in file.

        :return: value of open date.
        """
        date = file_metadata.get('date', [{}])
        date_value = date[0].get('dateValue')
        return date_value

    @staticmethod
    def is_future_open_date(self, file_metadata):
        """Check .

        :return: .
        """
        # Get current date.
        today = datetime.now().date()
        # Get 'open_date' and convert to datetime.date.
        date_value = self.get_open_date_value(file_metadata)
        _format = '%Y-%m-%d'
        dt = datetime.strptime(date_value, _format)
        # Compare open_date with current date.
        is_future = dt.date() > today
        return is_future

    @property
    def pid_doi(self):
        """Return pid_value of doi identifier."""
        return self._get_pid('doi')

    @property
    def pid_cnri(self):
        """Return pid_value of doi identifier."""
        return self._get_pid('hdl')

    @property
    def pid_parent(self):
        """Return pid_value of doi identifier."""
        pid_ver = PIDVersioning(child=self.pid_recid)
        if pid_ver:
            # Get pid parent of draft record
            if ".0" in self.pid_recid.pid_value:
                pid_ver.relation_type = 3
                return pid_ver.parents.one_or_none()
            return pid_ver.parents.one_or_none()
        return None

    @classmethod
    def get_record_by_pid(cls, pid):
        """Get record by pid."""
        pid = PersistentIdentifier.get('depid', pid)
        return cls.get_record(id_=pid.object_uuid)

    @classmethod
    def get_record_by_uuid(cls, uuid):
        """Get record by uuid."""
        record = cls.get_record(id_=uuid)
        return record

    @classmethod
    def get_record_cvs(cls, uuid):
        """Get record cvs."""
        record = cls.get_record(id_=uuid)
        return Indexes.get_coverpage_state(record.get('path'))

    def _get_pid(self, pid_type):
        """Return pid_value from persistent identifier."""
        pid_without_ver = get_record_without_version(self.pid_recid)
        if not pid_without_ver:
            return None
        try:
            return PersistentIdentifier.query.filter_by(
                pid_type=pid_type,
                object_uuid=pid_without_ver.object_uuid,
                status=PIDStatus.REGISTERED
            ).order_by(
                db.desc(PersistentIdentifier.created)
            ).first()
        except PIDDoesNotExistError as pid_not_exist:
            current_app.logger.error(pid_not_exist)
        return None

    def update_item_link(self, pid_value):
        """Update current Item Reference base of IR of pid_value input."""
        item_link = ItemLink(self.pid.pid_value)
        items = ItemReference.get_src_references(pid_value).all()
        relation_data = []

        for item in items:
            _item = dict(item_id=item.dst_item_pid,
                         sele_id=item.reference_type)
            relation_data.append(_item)

        if relation_data:
            item_link.update(relation_data)

    def get_file_data(self):
        """Get file data."""
        item_type_id = self.get('item_type_id')
        solst, _ = get_options_and_order_list(item_type_id)
        items = []
        for lst in solst:
            key = lst[0]
            val = self.get(key)
            if not val:
                continue
            # Just get data of 'File'.
            if val.get('attribute_type') != "file":
                continue
            mlt = val.get('attribute_value_mlt')
            if mlt is not None:
                items.extend(mlt)
        return items


class _FormatSysCreator:
    """Format system creator for detail page."""

    def __init__(self, creator):
        """Initialize Format system creator for detail page.

        :param creator:Creator data
        :param languages: language list
        """
        self.creator = creator
        self.current_language = current_i18n.language
        self.no_language_key = "NoLanguage"
        self._get_creator_languages_order()

    def _get_creator_languages_order(self):
        """Get creator languages order.

        @return:
        """
        # Prioriry languages: creator, family, given, alternative, affiliation
        lang_key = OrderedDict()
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_names']] = \
            WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_lang']
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['family_names']] = \
            WEKO_DEPOSIT_SYS_CREATOR_KEY['family_lang']
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['given_names']] = \
            WEKO_DEPOSIT_SYS_CREATOR_KEY['given_lang']
        lang_key[WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names']] = \
            WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_lang']

        # Get languages for all same structure languages key
        languages = []
        [languages.append(data.get(v)) for k, v in lang_key.items()
         for data in self.creator.get(k, []) if data.get(v) not in languages]

        # Get languages affiliation
        for creator_affiliation in self.creator.get(
                WEKO_DEPOSIT_SYS_CREATOR_KEY['creatorAffiliations'], []):
            for affiliation_name in creator_affiliation.get(
                    WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names'], []):
                if affiliation_name.get(
                    WEKO_DEPOSIT_SYS_CREATOR_KEY[
                        'affiliation_lang']) not in languages:
                    languages.append(affiliation_name.get(
                        WEKO_DEPOSIT_SYS_CREATOR_KEY['affiliation_lang']))
        self.languages = languages

    def _format_creator_to_show_detail(self, language: str, parent_key: str,
                                       lst: list) -> NoReturn:
        """Get creator name to show on item detail.

        :param language: language
        :param parent_key: parent key
        :param lst: creator name list
        """
        name_key = ''
        lang_key = ''
        if parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_names']:
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_lang']
        elif parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['family_names']:
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_lang']
        elif parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['given_names']:
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_lang']
        elif parent_key == WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names']:
            name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_name']
            lang_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_lang']
        if parent_key in self.creator:
            lst_value = self.creator[parent_key]
            if len(lst_value) > 0:
                for i in range(len(lst_value)):
                    if lst_value[i] and lst_value[i].get(lang_key) == language:
                        if name_key in lst_value[i]:
                            lst.append(lst_value[i][name_key])
                            break

    def _get_creator_to_show_popup(self, creators: Union[list, dict],
                                   language: any,
                                   creator_list: list,
                                   creator_list_temp: list = None) -> NoReturn:
        """Format creator to show on popup.

        :param creators: Creators information.
        :param language: Language.
        :param creator_list: Creator list.
        :param creator_list_temp: Creator temporary list.
        """
        def _run_format_affiliation(affiliation_max, affiliation_min,
                                    languages,
                                    creator_lists,
                                    creator_list_temps):
            """Format affiliation creator.

            :param affiliation_max: Affiliation max.
            :param affiliation_min: Affiliation min.
            :param languages: Language.
            :param creator_lists: Creator lists.
            :param creator_list_temps: Creator lists temps.

            """
            for index in range(len(affiliation_max)):
                if index < len(affiliation_min):
                    affiliation_max[index].update(
                        affiliation_min[index])
                    self._get_creator_to_show_popup(
                        [affiliation_max[index]],
                        languages, creator_lists,
                        creator_list_temps)
                else:
                    self._get_creator_to_show_popup(
                        [affiliation_max[index]],
                        languages, creator_lists,
                        creator_list_temps)

        def format_affiliation(affiliation_data):
            """Format affiliation creator.

            :param affiliation_data: Affiliation data.
            """
            for creator in affiliation_data:
                affiliation_name_format = creator.get('affiliationNames', [])
                affiliation_name_identifiers_format = creator.get(
                    'affiliationNameIdentifiers', [])
                if len(affiliation_name_format) >= len(
                        affiliation_name_identifiers_format):
                    affiliation_max = affiliation_name_format
                    affiliation_min = affiliation_name_identifiers_format
                else:
                    affiliation_max = affiliation_name_identifiers_format
                    affiliation_min = affiliation_name_format

                _run_format_affiliation(affiliation_max, affiliation_min,
                                        language,
                                        creator_list,
                                        creator_list_temp)

        if isinstance(creators, dict):
            creator_list_temp = []
            for key, value in creators.items():
                if (key in [WEKO_DEPOSIT_SYS_CREATOR_KEY['identifiers'],
                            WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_mails']]):
                    continue
                if key == WEKO_DEPOSIT_SYS_CREATOR_KEY['creatorAffiliations']:
                    format_affiliation(value)
                else:
                    self._get_creator_to_show_popup(value, language,
                                                    creator_list,
                                                    creator_list_temp)
            if creator_list_temp:
                if language:
                    creator_list.append({language: creator_list_temp})
                else:
                    creator_list.append(
                        {self.no_language_key: creator_list_temp})
        else:
            for creator_data in creators:
                self._get_creator_based_on_language(creator_data,
                                                    creator_list_temp,
                                                    language)

    @staticmethod
    def _get_creator_based_on_language(creator_data: dict,
                                       creator_list_temp: list,
                                       language: str) -> NoReturn:
        """Get creator based on language.

        :param creator_data: creator data.
        :param creator_list_temp: creator temporary list.
        :param language: language code.
        """
        count = 0
        for k, v in creator_data.items():
            if 'Lang' in k:
                if not language:
                    count = count + 1
                elif v == language:
                    creator_list_temp.append(creator_data)
        if count == 0 and not language:
            creator_list_temp.append(creator_data)

    def format_creator(self) -> dict:
        """Format creator data to display on detail screen.

        :return: <dict> The creators are formatted.
        """
        creator_lst = []
        rtn_value = {}
        creator_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_names']
        family_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_names']
        given_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_names']
        alternative_names = WEKO_DEPOSIT_SYS_CREATOR_KEY['alternative_names']
        list_parent_key = [creator_names, family_names, given_names,
                           alternative_names]

        # Get default creator name to show on detail screen.
        self._get_default_creator_name(list_parent_key,
                                       creator_lst)

        rtn_value['name'] = creator_lst
        creator_list_tmp = []
        creator_list = []

        # Get creators are displayed on creator pop up.
        self._get_creator_to_display_on_popup(creator_list_tmp)
        for creator_data in creator_list_tmp:
            if isinstance(creator_data, dict):
                creator_temp = {}
                for k, v in creator_data.items():
                    if isinstance(v, list):
                        merged_data = {}
                        self._merge_creator_data(v, merged_data)
                        creator_temp[k] = merged_data
                creator_list.append(creator_temp)

        # Format creators
        formatted_creator_list = []
        self._format_creator_on_creator_popup(creator_list,
                                              formatted_creator_list)

        rtn_value.update({'order_lang': formatted_creator_list})

        return rtn_value

    def _format_creator_on_creator_popup(self, creators: Union[dict, list],
                                         des_creator: Union[
                                             dict, list]) -> NoReturn:
        """Format creator on creator popup.

        :param creators:
        :param des_creator:
        """
        if isinstance(creators, list):
            for creator_data in creators:
                creator_tmp = {}
                self._format_creator_on_creator_popup(creator_data,
                                                      creator_tmp)
                des_creator.append(creator_tmp)
        elif isinstance(creators, dict):
            alternative_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
                'alternative_name']
            for key, value in creators.items():
                des_creator[key] = {}
                if key != self.no_language_key and isinstance(value, dict):
                    self._format_creator_name(value, des_creator[key])
                    des_creator[key][alternative_name_key] = value.get(
                        alternative_name_key, [])
                else:
                    des_creator[key] = value.copy()
                self._format_creator_affiliation(value.copy(),
                                                 des_creator[key])

    @staticmethod
    def _format_creator_name(creator_data: dict,
                             des_creator: dict) -> NoReturn:
        """Format creator name.

        :param creator_data: Creator value.
        :param des_creator: Creator des
        """
        creator_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['creator_name']
        family_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['family_name']
        given_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['given_name']
        creator_name = creator_data.get(creator_name_key)
        family_name = creator_data.get(family_name_key)
        given_name = creator_data.get(given_name_key)
        if creator_name:
            des_creator[creator_name_key] = creator_name
        else:
            if not family_name:
                des_creator[creator_name_key] = given_name
            elif not given_name:
                des_creator[creator_name_key] = family_name
            else:
                lst = []
                for idx, item in enumerate(family_name):
                    _creator_name = item
                    if len(given_name) > idx:
                        _creator_name += " " + given_name[idx]
                    lst.append(_creator_name)
                des_creator[creator_name_key] = lst

    @staticmethod
    def _format_creator_affiliation(creator_data: dict,
                                    des_creator: dict) -> NoReturn:
        """Format creator affiliation.

        :param creator_data: Creator data
        :param des_creator: Creator des.
        """
        def _get_max_list_length() -> int:
            """Get max length of list.

            :return: The max length of list.
            """
            max_data = max(
                [len(identifier_schema), len(affiliation_name),
                 len(identifier), len(identifier_uri)])
            return max_data

        identifier_schema_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
            'affiliation_name_identifier_scheme']
        affiliation_name_key = WEKO_DEPOSIT_SYS_CREATOR_KEY['affiliation_name']
        identifier_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
            'affiliation_name_identifier']
        identifier_uri_key = WEKO_DEPOSIT_SYS_CREATOR_KEY[
            'affiliation_name_identifier_URI']
        identifier_schema = creator_data.get(identifier_schema_key, [])
        affiliation_name = creator_data.get(affiliation_name_key, [])
        identifier = creator_data.get(identifier_key, [])
        identifier_uri = creator_data.get(identifier_uri_key, [])
        list_length = _get_max_list_length()
        idx = 0
        identifier_name_list = []
        identifier_list = []
        while idx < list_length:
            tmp_data = ""
            if len(identifier_schema) > idx:
                tmp_data += identifier_schema[idx]
            if len(affiliation_name) > idx:
                tmp_data += " " + affiliation_name[idx]
            identifier_name_list.append(tmp_data)

            identifier_tmp = {
                "identifier": "",
                "uri": "",
            }
            if len(identifier) > idx:
                identifier_tmp['identifier'] = identifier[idx]
            if len(identifier_uri) > idx:
                identifier_tmp['uri'] = identifier_uri[idx]
            identifier_list.append(identifier_tmp)
            idx += 1

        des_creator[affiliation_name_key] = identifier_name_list
        des_creator[identifier_key] = identifier_list

    def _get_creator_to_display_on_popup(self, creator_list: list):
        """Get creator to display on popup.

        :param creator_list: Creator list.
        """
        for lang in self.languages:
            self._get_creator_to_show_popup(self.creator, lang,
                                            creator_list)

    def _merge_creator_data(self, creator_data: Union[list, dict],
                            merged_data: dict) -> NoReturn:
        """Merge creator data.

        :param creator_data: Creator data.
        :param merged_data: Merged data.
        """
        def merge_data(key, value):
            if isinstance(merged_data.get(key), list):
                merged_data[key].append(value)
            else:
                merged_data[key] = [value]

        if isinstance(creator_data, list):
            for data in creator_data:
                self._merge_creator_data(data, merged_data)
        elif isinstance(creator_data, dict):
            for k, v in creator_data.items():
                if isinstance(v, str):
                    merge_data(k, v)

    def _get_default_creator_name(self, list_parent_key: list,
                                  creator_names: list) -> NoReturn:
        """Get default creator name.

        :param list_parent_key: parent list key.
        :param creator_names: Creators name.
        """
        def _get_creator(_language):
            for parent_key in list_parent_key:
                self._format_creator_to_show_detail(_language,
                                                    parent_key, creator_names)
                if creator_names:
                    return

        _get_creator(self.current_language)
        # if current language has no creator
        if not creator_names:
            for lang in self.languages:
                _get_creator(lang)
                if creator_names:
                    break


class _FormatSysBibliographicInformation:
    """Format system Bibliographic Information for detail page."""

    def __init__(self, bibliographic_meta_data_lst, props_lst):
        """Initialize format system Bibliographic Information for detail page.

        :param bibliographic_meta_data_lst: bibliographic meta data list
        :param props_lst: Property list
        """
        self.bibliographic_meta_data_lst = bibliographic_meta_data_lst
        self.props_lst = props_lst

    def is_bibliographic(self):
        """Check bibliographic information."""
        def check_key(_meta_data):
            for key in WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_SYS_KEY:
                if key in _meta_data:
                    return True
            return False

        meta_data = self.bibliographic_meta_data_lst
        if isinstance(meta_data, dict):
            return check_key(meta_data)
        elif isinstance(meta_data, list) and len(meta_data) > 0 and isinstance(
                meta_data[0], dict):
            return check_key(meta_data[0])

        return False

    def get_bibliographic_list(self, is_get_list):
        """Get bibliographic information list.

        :return: bibliographic list
        """
        bibliographic_list = []
        for bibliographic in self.bibliographic_meta_data_lst:
            title_data, magazine, length = self._get_bibliographic(
                bibliographic, is_get_list)
            bibliographic_list.append({
                'title_attribute_name': title_data,
                'magazine_attribute_name': magazine,
                'length': length
            })
        return bibliographic_list

    def _get_bibliographic(self, bibliographic, is_get_list):
        """Get bibliographic information data.

        :param bibliographic:
        :return: title_data, magazine, length
        """
        title_data = []
        language = 'ja'
        if bibliographic.get('bibliographic_titles'):
            if is_get_list:
                current_lang = current_i18n.language
                if not current_lang:
                    current_lang = 'en'
                title_data, language = self._get_source_title_show_list(
                    bibliographic.get('bibliographic_titles'), current_lang)
            else:
                title_data = self._get_source_title(
                    bibliographic.get('bibliographic_titles'))
        if is_get_list:
            bibliographic_info, length = self._get_bibliographic_show_list(
                bibliographic, language)
        else:
            bibliographic_info, length = self._get_bibliographic_information(
                bibliographic)
        return title_data, bibliographic_info, length

    def _get_property_name(self, key):
        """Get property name.

        :param key: Property key
        :return: Property Name.
        """
        for lst in self.props_lst:
            if key == lst[0].split('.')[-1]:
                return lst[2]
        return key

    @staticmethod
    def _get_translation_key(key, lang):
        """Get translation key.

        :param key: Property key
        :param lang: : Language
        :return: Translation key.
        """
        bibliographic_translation = current_app.config.get(
            'WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS')
        if key in bibliographic_translation:
            return bibliographic_translation.get(key, {}).get(lang, '')

    def _get_bibliographic_information(self, bibliographic):
        """Get magazine information data.

        :param bibliographic:
        :return:
        """
        bibliographic_info_list = []
        for key in WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_KEY:
            if key == 'p.':
                page = self._get_page_tart_and_page_end(
                    bibliographic.get('bibliographicPageStart'),
                    bibliographic.get('bibliographicPageEnd'))
                if page != '':
                    bibliographic_info_list.append({key: page})
            elif key == 'bibliographicIssueDates':
                dates = self._get_issue_date(
                    bibliographic.get(key))
                if dates:
                    bibliographic_info_list.append(
                        {self._get_property_name(key): " ".join(
                            str(x) for x in dates)})
            elif bibliographic.get(key):
                bibliographic_info_list.append(
                    {self._get_property_name(key): bibliographic.get(key)})
        length = len(bibliographic_info_list) if len(
            bibliographic_info_list) else 0
        return bibliographic_info_list, length

    def _get_bibliographic_show_list(self, bibliographic, language):
        """Get magazine information data.

        :param bibliographic:
        :return:
        """
        bibliographic_info_list = []
        for key in WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_KEY:
            if key == 'p.':
                page = self._get_page_tart_and_page_end(
                    bibliographic.get('bibliographicPageStart'),
                    bibliographic.get('bibliographicPageEnd'))
                if page != '':
                    bibliographic_info_list.append({key: page})
            elif key == 'bibliographicIssueDates':
                dates = self._get_issue_date(
                    bibliographic.get(key))
                if dates:
                    bibliographic_info_list.append(
                        {self._get_translation_key(key, language): " ".join(
                            str(x) for x in dates)})
            elif bibliographic.get(key):
                bibliographic_info_list.append({
                    self._get_translation_key(key, language): bibliographic.get(
                        key)
                })
        length = len(bibliographic_info_list) if len(
            bibliographic_info_list) else 0
        return bibliographic_info_list, length

    @staticmethod
    def _get_source_title(source_titles):
        """Get source title.

        :param source_titles:
        :return:
        """
        title_data = []
        for source_title in source_titles:
            title = source_title['bibliographic_titleLang'] + ' : ' if \
                source_title.get('bibliographic_titleLang') else ''
            title += source_title[
                'bibliographic_title'] if source_title.get(
                'bibliographic_title') else ''
            title_data.append(title)
        return title_data

    @staticmethod
    def _get_source_title_show_list(source_titles, current_lang):
        """Get source title in show list.

        :param current_lang:
        :param source_titles:
        :return:
        """
        value_en = None
        value_latn = None
        title_data_lang = []
        title_data_none_lang = []
        for source_title in source_titles:
            key = source_title.get('bibliographic_titleLang')
            value = source_title.get('bibliographic_title')
            if not value:
                continue
            elif current_lang == key:
                return value, key
            else:
                if key:
                    if key == 'en':
                        value_en = value
                    elif key == 'ja-Latn':
                        value_latn = value
                    else:
                        title = {}
                        title[key] = value
                        title_data_lang.append(title)
                else:
                    title_data_none_lang.append(value)

        if value_latn:
            return value_latn, 'ja-Latn'

        if value_en and (current_lang != 'ja' or
                         not current_app.config.get("WEKO_RECORDS_UI_LANG_DISP_FLG", False)):
            return value_en, 'en'

        if len(title_data_lang) > 0:
            if current_lang != 'en' or \
                    not current_app.config.get("WEKO_RECORDS_UI_LANG_DISP_FLG", False):
                return list(title_data_lang[0].values())[0], \
                    list(title_data_lang[0])[0]
            else:
                for t in title_data_lang:
                    if list(t)[0] != 'ja':
                        return list(t.values())[0], list(t)[0]
        return (title_data_none_lang[0], 'ja') if len(
            title_data_none_lang) > 0 else (None, 'ja')

    @staticmethod
    def _get_page_tart_and_page_end(page_start, page_end):
        """Get page start and page end.

        :param page_start:
        :param page_end:
        :return:
        """
        page = ''
        page += page_start if page_start is not None else ''
        if page_end is not None:
            temp = page_end if page == '' else '-' + page_end
            page += temp if page_end else ''

        return page

    @staticmethod
    def _get_issue_date(issue_date):
        """
        Get issue dates.

        :param issue_date:
        :return:
        """
        date = []
        issue_type = 'Issued'
        if isinstance(issue_date, list):
            for issued_date in issue_date:
                if issued_date.get(
                    'bibliographicIssueDate') and issued_date.get(
                        'bibliographicIssueDateType') == issue_type:
                    date.append(issued_date.get('bibliographicIssueDate'))
        elif isinstance(issue_date, dict) and \
            (issue_date.get('bibliographicIssueDate')
             and issue_date.get('bibliographicIssueDateType')
                == issue_type):
            date.append(issue_date.get('bibliographicIssueDate'))
        return date
