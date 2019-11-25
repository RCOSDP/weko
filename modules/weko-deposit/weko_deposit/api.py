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
import uuid
from copy import deepcopy
from datetime import datetime

import redis
from dictdiffer import patch
from dictdiffer.merge import Merger, UnresolvedConflictsException
from flask import abort, current_app, has_request_context, json, request, \
    session
from flask_security import current_user
from invenio_db import db
from invenio_deposit.api import Deposit, index, preserve
from invenio_deposit.errors import MergeConflict
from invenio_files_rest.models import Bucket, MultipartObject, ObjectVersion, \
    Part
from invenio_indexer.api import RecordIndexer
from invenio_pidrelations.contrib.records import RecordDraft, index_siblings
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.serializers.utils import serialize_relations
from invenio_pidstore.errors import PIDInvalidAction
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_files.api import FileObject, Record
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest.errors import PIDResolveRESTError
from simplekv.memory.redisstore import RedisStore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified
from weko_index_tree.api import Indexes
from weko_records.api import FeedbackMailList, ItemsMetadata, ItemTypes
from weko_records.models import ItemMetadata
from weko_records.utils import get_all_items, get_attribute_value_all_items, \
    get_options_and_order_list, json_loader, set_timestamp
from weko_user_profiles.models import UserProfile

from .pidstore import get_latest_version_id, weko_deposit_fetcher, \
    weko_deposit_minter
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


class WekoIndexer(RecordIndexer):
    """Provide an interface for indexing records in Elasticsearch."""

    def get_es_index(self):
        """Elastic search settings."""
        self.es_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
        self.es_doc_type = current_app.config['INDEXER_DEFAULT_DOCTYPE']
        self.file_doc_type = current_app.config['INDEXER_FILE_DOC_TYPE']

    def upload_metadata(self, jrc, item_id, revision_id):
        """Upload the item data to ElasticSearch.

        :param jrc:
        :param item_id: item id.
        """
        # delete the item when it is exist
        # if self.client.exists(id=str(item_id), index=self.es_index,
        #                       doc_type=self.es_doc_type):
        #     self.client.delete(id=str(item_id), index=self.es_index,
        #                        doc_type=self.es_doc_type)
        full_body = dict(id=str(item_id),
                         index=self.es_index,
                         doc_type=self.es_doc_type,
                         version=revision_id + 1,
                         version_type=self._version_type,
                         body=jrc)

        if 'content' in jrc:  # Only pass through pipeline if file exists
            full_body['pipeline'] = 'item-file-pipeline'

        self.client.index(**full_body)

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

    def update_relation_info(self, record, relation_info):
        """Update relation info."""
        self.get_es_index()
        relation = 'relation'
        relation_type = 'relation_type'
        relation_type_val = []
        for d in relation_info[0]:
            pid = d.get('item_data').get('links').get('self').split('/')[len(
                d.get('item_data').get('links').get('self').split('/')) - 1]
            links = '/records/' + pid
            sub_data = dict(
                item_links=links,
                item_title=d.get('item_title'),
                value=d.get('sele_id'))
            relation_type_val.append(sub_data)
        if relation_info[0]:
            body = {'doc': {relation: {relation_type: relation_type_val}}}
        else:
            body = {'doc': {relation: {}}}
        return self.client.update(
            index=self.es_index,
            doc_type=self.es_doc_type,
            id=str(record.id),
            body=body
        )

    def get_item_link_info(self, pid):
        """Get item link info."""
        try:
            self.get_es_index()
            item_link_info = None
            get_item_link_q = {
                "query": {
                    "match": {
                        "control_number": "@control_number"
                    }
                }
            }
            query_q = json.dumps(get_item_link_q).replace(
                "@control_number", pid)
            query_q = json.loads(query_q)
            indexer = RecordIndexer()
            res = indexer.client.search(index=self.es_index, body=query_q)
            item_link_info = res.get("hits").get(
                "hits")[0].get('_source').get("relation")
        except Exception as ex:
            current_app.logger.debug(ex)
        return item_link_info

    def update_path(self, record, update_revision=True):
        """Update path."""
        self.get_es_index()
        path = 'path'
        body = {'doc': {path: record.get(path)}}
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
        args.append({})
        m = Merger(*args)
        try:
            m.run()
        except UnresolvedConflictsException:
            raise MergeConflict()
        return patch(m.unified_patches, lca)

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

    def publish(self, pid=None, id_=None):
        """Publish the deposit."""
        if self.data is None:
            self.data = self.get('_deposit', {})
        if 'control_number' in self:
            self.pop('control_number')
        if '$schema' not in self:
            self['$schema'] = current_app.extensions['invenio-jsonschemas'].\
                path_to_url(current_app.config['DEPOSIT_DEFAULT_JSONSCHEMA'])
        self.is_edit = True
        try:
            deposit = super(WekoDeposit, self).publish(pid, id_)
            # deposit = super(WekoDeposit, self).publish(pid, id_)

            # update relation version current to ES
            pid = PersistentIdentifier.query.filter_by(
                pid_type='recid', object_uuid=self.id).first()
            relations = serialize_relations(pid)
            if relations and 'version' in relations:
                relations_ver = relations['version'][0]
                relations_ver['id'] = pid.object_uuid
                relations_ver['is_last'] = relations_ver.get('index') == 0
                self.indexer.update_relation_version_is_last(relations_ver)
            return deposit
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None

    @classmethod
    def create(cls, data, id_=None, recid=None):
        """Create a deposit.

        Adds bucket creation immediately on deposit creation.
        """
        current_app.logger.debug('=================================')
        current_app.logger.debug('Adds bucket creation')
        bucket = Bucket.create(
            quota_size=current_app.config['WEKO_BUCKET_QUOTA_SIZE'],
            max_file_size=current_app.config['WEKO_MAX_FILE_SIZE'],
        )
        if '$schema' in data:
            data.pop('$schema')

        data['_buckets'] = {'deposit': str(bucket.id)}

        # save user_name & display name.
        if current_user and current_user.is_authenticated:
            user = UserProfile.get_by_userid(current_user.get_id())

            username = ''
            displayname = ''
            if user is not None:
                username = user._username
                displayname = user._displayname
            if '_deposit' in data:
                data['_deposit']['owners_ext'] = {
                    'username': username,
                    'displayname': displayname,
                    'email': current_user.email
                }
        if not recid:
            deposit = super(WekoDeposit, cls).create(data, id_=id_)
        else:
            deposit = super(
                WekoDeposit,
                cls).create(
                data,
                id_=id_,
                recid=recid)
        RecordsBuckets.create(record=deposit.model, bucket=bucket)

        dep_id = str(data['_deposit']['id'])
        recid = PersistentIdentifier.get('recid', dep_id)
        depid = PersistentIdentifier.get('depid', dep_id)
        p_depid = PersistentIdentifier.create(
            'parent',
            'parent:{0}'.format(dep_id),
            object_type='rec',
            object_uuid=uuid.uuid4(),
            status=PIDStatus.REGISTERED
        )

        PIDVersioning(parent=p_depid).insert_draft_child(child=recid)
        RecordDraft.link(recid, depid)

        return deposit

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def update(self, *args, **kwargs):
        """Update only drafts."""
        self['_deposit']['status'] = 'draft'
        if len(args) > 1:
            dc = self.convert_item_metadata(args[0], args[1])
        else:
            dc = self.convert_item_metadata(args[0])
        super(WekoDeposit, self).update(dc)
#        if 'pid' in self['_deposit']:
#            self['_deposit']['pid']['revision_id'] += 1
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
        if self.data and len(self.data):
            # save item metadata
            self.save_or_update_item_metadata()

            if self.jrc and len(self.jrc):
                # upload item metadata to Elasticsearch
                set_timestamp(self.jrc, self.created, self.updated)

                # Get file contents
                self.get_content_files()

                # upload file content to Elasticsearch
                self.indexer.upload_metadata(self.jrc, self.pid.object_uuid,
                                             self.revision_id)

                # remove large base64 files for release memory
                if self.jrc.get('content'):
                    for content in self.jrc['content']:
                        if content.get('file'):
                            del content['file']

        # fix schema url
        record = RecordMetadata.query.get(self.pid.object_uuid)
        if record and record.json and '$schema' in record.json:
            record.json.pop('$schema')
            flag_modified(record, 'json')
            db.session.merge(record)

    def newversion(self, pid=None):
        """Create a new version deposit."""
        # deposit = None
        try:
            if not self.is_published():
                raise PIDInvalidAction()

            # Check that there is not a newer draft version for this record
            # and this is the latest version
            pv = PIDVersioning(child=pid)
            if pv.exists and not pv.draft_child:  # and pid == pv.last_child:
                # the latest record: item without version ID
                last_pid = pid  # pv.last_child
                # Get copy of the latest record
                latest_record = WekoDeposit.get_record(
                    last_pid.object_uuid)
                if latest_record is not None:
                    data = latest_record.dumps()

                    current_app.logger.debug('xxxxxxxxxxxxxxxxxxxxxxxxxxx')
                    owners = data['_deposit']['owners']
                    keys_to_remove = ('_deposit', 'doi', '_oai',
                                      '_files', '$schema')
                    for k in keys_to_remove:
                        data.pop(k, None)

                    # attaching version ID
                    recid = '{0}.{1}' . format(
                        last_pid.pid_value,
                        get_latest_version_id(last_pid.pid_value))
                    # NOTE: We call the superclass `create()` method, because we
                    # don't want a new empty bucket, but an unlocked snapshot of
                    # the old record's bucket.
                    deposit = super(WekoDeposit, self).create(data, recid=recid)
                    # Injecting owners is required in case of creating new
                    # version this outside of request context
                    deposit['_deposit']['owners'] = owners

                    recid = PersistentIdentifier.get(
                        'recid', str(data['_deposit']['id']))
                    depid = PersistentIdentifier.get(
                        'depid', str(data['_deposit']['id']))

                    PIDVersioning(
                        parent=pv.parent).insert_draft_child(
                        child=recid)
                    RecordDraft.link(recid, depid)

                    # Create snapshot from the record's bucket and update data
                    if latest_record.files:
                        snapshot = latest_record.files.bucket.snapshot(
                            lock=False)
                        snapshot.locked = False
                        deposit['_buckets'] = {'deposit': str(snapshot.id)}
                        RecordsBuckets.create(
                            record=deposit.model, bucket=snapshot)
                    if 'extra_formats' in latest_record['_buckets']:
                        extra_formats_snapshot = \
                            latest_record.extra_formats.bucket.snapshot(
                                lock=False)
                        deposit['_buckets']['extra_formats'] = \
                            str(extra_formats_snapshot.id)
                        RecordsBuckets.create(record=deposit.model,
                                              bucket=extra_formats_snapshot)
                    index = {'index': self.get('path', []),
                             'actions': self.get('publish_status')}
                    if 'activity_info' in session:
                        del session['activity_info']
                    item_metadata = ItemsMetadata.get_record(
                        last_pid.object_uuid).dumps()
                    item_metadata.pop('id', None)
                    args = [index, item_metadata]
                    current_app.logger.debug(deposit)
                    deposit.update(*args)
                    deposit.commit()
            return deposit
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None

    def get_content_files(self):
        """Get content file metadata."""
        contents = []
        fmd = self.get_file_data()
        if fmd:
            for file in self.files:
                if isinstance(fmd, list):
                    for lst in fmd:
                        if file.obj.key == lst.get('filename'):
                            lst.update({'mimetype': file.obj.mimetype})

                            # update file_files's json
                            file.obj.file.update_json(lst)

                            # upload file metadata to Elasticsearch
                            try:
                                file_size_max = current_app.config[
                                    'WEKO_MAX_FILE_SIZE_FOR_ES']
                                mimetypes = current_app.config[
                                    'WEKO_MIMETYPE_WHITELIST_FOR_ES']
                                if file.obj.file.size <= file_size_max and \
                                        file.obj.mimetype in mimetypes:

                                    content = lst.copy()
                                    content.update(
                                        {"file": file.obj.file.read_file(lst)})
                                    contents.append(content)

                            except Exception as e:
                                abort(500, '{}'.format(str(e)))
                            break
            self.jrc.update({'content': contents})

    def get_file_data(self):
        """Get file data."""
        file_data = []
        for key in self.data:
            if isinstance(self.data.get(key), list):
                for item in self.data.get(key):
                    if (isinstance(item, dict) or isinstance(item, list)) \
                            and 'filename' in item:
                        file_data.extend(self.data.get(key))
                        break
        return file_data

    def save_or_update_item_metadata(self):
        """Save or update item metadata.

        Save when register a new item type, Update when edit an item
        type.
        """
        if current_user:
            current_user_id = current_user.get_id()
        else:
            current_user_id = '1'
        if current_user_id:
            dc_owner = self.data.get("owner", None)
            if not dc_owner:
                self.data.update(dict(owner=current_user_id))

        if ItemMetadata.query.filter_by(id=self.id).first():
            obj = ItemsMetadata.get_record(self.id)
            obj.update(self.data)
            obj.commit()
        else:
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

                data_str = datastore.get(cache_key)
                datastore.delete(cache_key)
                data = json.loads(data_str.decode('utf-8'))
        except BaseException:
            abort(500, 'Failed to register item')
        # Get index path
        index_lst = index_obj.get('index', [])
        # Prepare index id list if the current index_lst is a path list
        if index_lst:
            index_id_lst = []
            for index in index_lst:
                indexes = str(index).split('/')
                index_id_lst.append(indexes[len(indexes) - 1])
            index_lst = index_id_lst

        plst = Indexes.get_path_list(index_lst)

        if not plst or len(index_lst) != len(plst):
            raise PIDResolveRESTError(
                description='Any tree index has been deleted')

        index_lst.clear()
        for lst in plst:
            index_lst.append(lst.path)

        # convert item meta data
        dc, jrc, is_edit = json_loader(data, self.pid)
        dc['publish_date'] = data.get('pubdate')
        dc['title'] = [data.get('title')]
        dc['relation_version_is_last'] = True
        self.data = data
        self.jrc = jrc
        self.is_edit = is_edit

        # Save Index Path on ES
        jrc.update(dict(path=index_lst))
        # add at 20181121 start
        sub_sort = {}
        for pth in index_lst:
            # es setting
            sub_sort[pth[-13:]] = ""
#        jrc.update(dict(custom_sort=sub_sort))
#        dc.update(dict(custom_sort=sub_sort))
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
        return dc

    @classmethod
    def delete_by_index_tree_id(cls, path):
        """Delete by index tree id."""
        # first update target pid when index tree id was deleted
        # if cls.update_pid_by_index_tree_id(cls, path):
        #    from .tasks import delete_items_by_id
        #    delete_items_by_id.delay(path)
        obj_ids = next(cls.indexer.get_pid_by_es_scroll(path))
        try:
            for obj_uuid in obj_ids:
                r = RecordMetadata.query.filter_by(id=obj_uuid).first()
                try:
                    r.json['path'].remove(path)
                    flag_modified(r, 'json')
                except BaseException:
                    pass
                if r.json['path'] == []:
                    from weko_records_ui.utils import soft_delete
                    soft_delete(obj_uuid)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            raise(ex)

    @classmethod
    def update_by_index_tree_id(cls, path, target):
        """Update by index tree id."""
        # update item path only
        from .tasks import update_items_by_id
        update_items_by_id.delay(path, target)

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
                               p.object_type == 'rec').\
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

    def update_jpcoar_identifier(self):
        """Update JPCOAR meta data item for grant DOI which added at the Identifier Grant screen."""
        obj = ItemsMetadata.get_record(self.id)
        attrs = ['attribute_value_mlt',
                 'item_1551265147138',
                 'item_1551265178780']
        dc = {
            attrs[1]: {attrs[0]: obj.get(attrs[1])},
            attrs[2]: {attrs[0]: [obj.get(attrs[2])]}
        }
        self.indexer.update_jpcoar_identifier(dc, self.id)
        record = RecordMetadata.query.get(self.id)
        if record and record.json:
            try:
                with db.session.begin_nested():
                    record.json[attrs[1]][attrs[0]] = obj.get(attrs[1])
                    record.json[attrs[2]][attrs[0]] = [obj.get(attrs[2])]
                    flag_modified(record, 'json')
                    db.session.merge(record)
                db.session.commit()
            except Exception as ex:
                current_app.logger.debug(ex)
                db.session.rollback()

    def merge_data_to_record_without_version(self, pid):
        """Update changes from record attached version to without version."""
        with db.session.begin_nested():
            # update item_metadata
            index = {'index': self.get('path', []),
                     'actions': self.get('publish_status')}
            item_metadata = ItemsMetadata.get_record(pid.object_uuid).dumps()
            item_metadata.pop('id', None)
            args = [index, item_metadata]
            self.update(*args)
            self.commit()
            # update records_metadata
            flag_modified(self.model, 'json')
            db.session.merge(self.model)

        return self.__class__(self.model.json, model=self.model)


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
        def get_name_iddentifier_uri(mlt):
            for m in mlt:
                if m.get('nameIdentifiers'):
                    for v in m.get('nameIdentifiers'):
                        name = v.get('nameIdentifier')
                        if name:
                            uri = ''
                            if v.get('nameIdentifierURI'):
                                uri = v.get('nameIdentifierURI')
                            elif v.get('nameIdentifierScheme'):
                                uri = 'http://' + v.get('nameIdentifierScheme')\
                                      + '.io/' + name
                            v['nameIdentifier'] = dict(name=name, uri=uri)
            return mlt
        try:

            items = []
            solst, meta_options = get_options_and_order_list(
                self.get('item_type_id'))

            for lst in solst:
                key = lst[0]

                val = self.get(key)
                option = meta_options.get(key, {}).get('option')
                if not val or not option:
                    continue

                hidden = option.get("hidden")
                if hidden:
                    items.append({
                        'attribute_name_hidden': val.get('attribute_name')
                    })
                    continue

                mlt = val.get('attribute_value_mlt')
                if mlt is not None:

                    nval = dict()
                    nval['attribute_name'] = val.get('attribute_name')
                    nval['attribute_type'] = val.get('attribute_type')
                    if nval['attribute_name'] == 'Reference' \
                            or nval['attribute_type'] == 'file':
                        nval['attribute_value_mlt'] = \
                            get_all_items(mlt, solst, True)
                    else:
                        is_author = nval['attribute_type'] == 'creator'
                        if is_author:
                            mlt = get_name_iddentifier_uri(mlt)
                        nval['attribute_value_mlt'] = \
                            get_attribute_value_all_items(mlt, solst, is_author)
                    items.append(nval)
                else:
                    items.append(val)

            current_app.logger.debug("items: {}".format(items))

            return items
        except BaseException:
            abort(500)

    @classmethod
    def get_record_by_pid(cls, pid):
        """Get record by pid."""
        pid = PersistentIdentifier.get('depid', pid)
        return cls.get_record(id_=pid.object_uuid)

    @classmethod
    def get_record_with_hps(cls, uuid):
        """Get record with hps."""
        record = cls.get_record(id_=uuid)
        path = []
        path.extend(record.get('path'))
        harvest_public_state = True
        if path:
            harvest_public_state = Indexes.get_harvest_public_state(path)
        return harvest_public_state, record

    @classmethod
    def get_record_cvs(cls, uuid):
        """Get record cvs."""
        record = cls.get_record(id_=uuid)
        path = []
        path.extend(record.get('path'))
        coverpage_state = False
        if path:
            coverpage_state = Indexes.get_coverpage_state(path)
        return coverpage_state
