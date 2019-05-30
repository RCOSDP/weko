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
import sys
import traceback
from datetime import datetime

import redis
from flask import abort, current_app, flash, g, has_request_context, json
from flask_login import current_user
from flask_security import current_user
from invenio_db import db
from invenio_deposit.api import Deposit, index, preserve
from invenio_files_rest.models import Bucket, MultipartObject, ObjectVersion, \
    Part
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_records_files.api import FileObject, Record
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest.errors import PIDResolveRESTError
from invenio_pidrelations.contrib.records import RecordDraft
from invenio_pidrelations.contrib.versioning import PIDVersioning
from simplekv.memory.redisstore import RedisStore
from sqlalchemy.orm.attributes import flag_modified
from weko_index_tree.api import Indexes
from weko_records.api import ItemsMetadata, ItemTypes
from weko_records.utils import get_all_items, get_options_and_order_list, \
    json_loader, set_timestamp
from weko_user_profiles.models import UserProfile

from .pidstore import weko_deposit_fetcher, weko_deposit_minter
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
        self.client.index(id=str(item_id),
                          index=self.es_index,
                          doc_type=self.es_doc_type,
                          version=revision_id + 1,
                          version_type=self._version_type,
                          body=jrc,
                          )

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

    def update_relation_info(self, record, relation_info):
        """Update relation info."""
        self.get_es_index()
        relation = 'relation'
        relation_type = 'relation_type'
        relation_type_val = []
        for d in relation_info[0]:
            pid = d.get('item_data').get('links').get('self').split(
                '/')[len(d.get('item_data').get('links').get('self').split('/')) - 1]
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
            res = indexer.client.search(index="weko", body=query_q)
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
        return None


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

    def publish(self, pid=None, id_=None):
        """Publish the deposit."""
        if self.data is None:
            self.data=self.get('_deposit', {})
        if 'control_number' in self:
            self.pop('control_number')
        if '$schema' not in self:
            self['$schema'] = ''
        deposit = super(WekoDeposit, self).publish(pid, id_)
        return deposit

    @classmethod
    def create(cls, data, id_=None):
        """Create a deposit.

        Adds bucket creation immediately on deposit creation.
        """
        bucket = Bucket.create(
            quota_size=current_app.config['WEKO_BUCKET_QUOTA_SIZE'],
            max_file_size=current_app.config['WEKO_MAX_FILE_SIZE'],
        )
        if '$schema' in data:
            data.pop('$schema')

        data['_buckets'] = {'deposit': str(bucket.id)}

        # save user_name & display name.
        if current_user and current_user.is_authenticated:
            creator_id = int(current_user.get_id())
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
        deposit = super(WekoDeposit, cls).create(data, id_=id_)
        RecordsBuckets.create(record=deposit.model, bucket=bucket)

        recid = PersistentIdentifier.get('recid', str(data['_deposit']['id']))
        depid = PersistentIdentifier.get('depid', str(data['_deposit']['id']))

        PIDVersioning(parent=recid).insert_draft_child(child=recid)
        RecordDraft.link(recid, depid)

        return deposit

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def update(self, *args, **kwargs):
        """Update only drafts."""
        if len(args) > 1:
            dc = self.convert_item_metadata(args[0], args[1])
        else:
            dc = self.convert_item_metadata(args[0])
        super(WekoDeposit, self).update(dc)
        if has_request_context():
            item_created.send(
                current_app._get_current_object(), item_id=self.pid)

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def clear(self, *args, **kwargs):
        """Clear only drafts."""
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
                    if 'filename' in item:
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

        if self.is_edit:
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
            actions = index_obj.get('actions', 'private')
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
        plst = Indexes.get_path_list(index_lst)

        if not plst or len(index_lst) != len(plst):
            raise PIDResolveRESTError(
                description='Any tree index has been deleted')

        index_lst.clear()
        for lst in plst:
            index_lst.append(lst.path)

        # convert item meta data
        dc, jrc, is_edit = json_loader(data, self.pid)
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
        jrc.update(dict(custom_sort=sub_sort))
        dc.update(dict(custom_sort=sub_sort))
        dc.update(dict(path=index_lst))

        pubs = '1' if 'private' in actions else '0'
        ps = dict(publish_status=pubs)
        jrc.update(ps)
        dc.update(ps)
        return dc

    @classmethod
    def delete_by_index_tree_id(cls, path):
        """Delete by index tree id."""
        # first update target pid when index tree id was deleted
        if cls.update_pid_by_index_tree_id(cls, path):
            from .tasks import delete_items_by_id
            delete_items_by_id.delay(path)

    @classmethod
    def update_by_index_tree_id(cls, path, target):
        """Update by index tree id."""
        # update item path only
        from .tasks import update_items_by_id
        update_items_by_id.delay(path)
        # update_items_by_id(path, target)

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
                        filter(p.object_uuid.in_(result), p.object_type == 'rec'). \
                        update({p.status: 'D', p.updated: dt},
                               synchronize_session=False)
                    result.clear()
            db.session.commit()
            return True
        except Exception as e:
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


class WekoRecord(Record):
    """Extend Record obj for record ui."""

    file_cls = WekoFileObject

    # files_iter_cls = WekoFilesIterator

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
        return Indexes.get_path_name(self.get('path', []))

    @property
    def item_type_info(self):
        """Return the information of item type."""
        item_type = ItemTypes.get_by_id(self.get('item_type_id'))
        return '{}({})'.format(item_type.item_type_name.name, item_type.tag)

    @property
    def items_show_list(self):
        """Return the item show list."""
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
                    continue

                mlt = val.get('attribute_value_mlt')
                if mlt:
                    nval = dict()
                    nval['attribute_name'] = val.get('attribute_name')
                    nval['attribute_type'] = val.get('attribute_type')
                    if 'creator' == nval['attribute_type']:
                        nval['attribute_value_mlt'] = mlt
                    else:
                        nval['attribute_value_mlt'] = get_all_items(mlt, solst)
                    items.append(nval)
                else:
                    items.append(val)
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
