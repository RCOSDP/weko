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

from collections import OrderedDict

import redis
from flask import current_app, abort, json
from invenio_deposit.api import Deposit, preserve
from invenio_files_rest.models import Bucket
from invenio_files_rest.models import ObjectVersion
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import FileObject, Record
from invenio_records_files.models import RecordsBuckets
from simplekv.memory.redisstore import RedisStore
from weko_index_tree.api import Indexes
from weko_items_ui import current_weko_items_ui
from weko_records.api import ItemTypes, ItemsMetadata
from weko_records.utils import save_item_metadata, find_items, set_timestamp, get_all_items

from .pidstore import weko_deposit_fetcher, weko_deposit_minter

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
        super(WekoFileObject, self).dumps()
        self.data.update(self.obj.file.json)
        index = self['filename'].rfind('.')
        self['filename'] = self['filename'][:index]
        return self.data


class WekoIndexer(RecordIndexer):
    """Provide an interface for indexing records in Elasticsearch."""

    def get_es_index(self):
        """Elastic search settings"""
        self.es_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
        self.es_doc_type = current_app.config['INDEXER_DEFAULT_DOCTYPE']
        self.file_doc_type = current_app.config['INDEXER_FILE_DOC_TYPE']

    def upload_metadata(self, jrc, item_id, revision_id):
        """
        Upload the item data to ElasticSearch

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
            except:
                pass

    def update_publish_status(self, record):
        self.get_es_index()
        pst = 'publish_status'
        body = {'doc': {pst: record.get(pst)}}
        return self.client.update(
            index=self.es_index,
            doc_type=self.es_doc_type,
            id=str(record.id),
            version=record.revision_id,
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
        pass

    def get_count_by_index_id(self, tree_path):
        """Get count by index id.

        :param tree_path: Tree_path instance.
        """
        search_query = {
            "query": {
                "term": {
                    "path.tree": tree_path
                }
            }
        }
        self.get_es_index()
        search_result = self.client.count(index=self.es_index,
                                          doc_type=self.es_doc_type,
                                          body=search_query)
        return search_result.get('count')


class WekoDeposit(Deposit):
    """Define API for changing deposit state."""

    indexer = WekoIndexer()

    deposit_fetcher = staticmethod(weko_deposit_fetcher)

    deposit_minter = staticmethod(weko_deposit_minter)

    @property
    def item_metadata(self):
        """Return the Item metadata."""
        return ItemsMetadata.get_record(self.id).dumps()

    @classmethod
    def create(cls, data, id_=None):
        """Create a deposit.

        Adds bucket creation immediately on deposit creation.
        """
        bucket = Bucket.create(
            quota_size=current_app.config['WEKO_BUCKET_QUOTA_SIZE'],
            max_file_size=current_app.config['WEKO_MAX_FILE_SIZE'],
        )
        if "$schema" in data:
            data.pop("$schema")

        data['_buckets'] = {'deposit': str(bucket.id)}
        deposit = super(WekoDeposit, cls).create(data, id_=id_)

        RecordsBuckets.create(record=deposit.model, bucket=bucket)

        # recid = PersistentIdentifier.get(
        #     'recid', str(data['recid']))
        # conceptrecid = PersistentIdentifier.get(
        #     'recid', str(data['conceptrecid']))
        # depid = PersistentIdentifier.get(
        #     'depid', str(data['_deposit']['id']))

        # PIDVersioning(parent=conceptrecid).insert_draft_child(child=recid)
        # RecordDraft.link(recid, depid)

        return deposit

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def update(self, *args, **kwargs):
        """Update only drafts."""
        td = args[0]

        try:
            datastore = RedisStore(redis.StrictRedis.from_url(
                current_app.config['CACHE_REDIS_URL']))
            cache_key = current_app.config[
                'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(
                pid_value=self.pid.pid_value)

            data_str = datastore.get(cache_key)
            datastore.delete(cache_key)
            data = json.loads(data_str)

            # td = ['6', '14']
            plst = Indexes.get_path_list(td)
            if plst:
                td.clear()
                for lst in plst:
                    td.append(lst.path)
        except:
            abort(400, "Failed to register item")

        dc, jrc, is_edit = save_item_metadata(data, self.pid)
        self.data = data
        self.jrc = jrc
        self.is_edit = is_edit

        # Save Index Path on ES
        jrc.update(dict(path=td))
        dc.update(dict(path=td))

        # default to set private status
        if not is_edit:
            ps = dict(publish_status='1')
            jrc.update(ps)
            dc.update(ps)

        super(WekoDeposit, self).update(dc)

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def clear(self, *args, **kwargs):
        """Clear only drafts."""
        super(WekoDeposit, self).clear(*args, **kwargs)

    def commit(self, *args, **kwargs):
        """Store changes on current instance in database and index it."""

        super(WekoDeposit, self).commit(*args, **kwargs)
        if self.data and len(self.data):
            # save item metadata
            self.save_or_update_item_metadata()

            if self.jrc and len(self.jrc):
                # upload item metadata to Elasticsearch
                set_timestamp(self.jrc, self.created, self.updated)

                # upload file content to Elasticsearch
                self.get_content_files()
                self.indexer.upload_metadata(self.jrc, self.pid.object_uuid,
                                             self.revision_id)
                # remove large base64 files for release memory
                if self.jrc.get('content'):
                    for content in self.jrc['content']:
                        del content['file']

    def get_content_files(self):
        """Upload files."""
        fmd = self.data.get("filemeta")
        if fmd:
            fmd = fmd.copy()
            for file in self.files:
                if isinstance(fmd, list):
                    for lst in fmd:
                        if file.obj.key == lst.get('filename'):
                            lst.update({'mimetype': file.obj.mimetype})

                            # update file_files's json
                            file.obj.file.update_json(lst)

                            # upload file metadata to Elasticsearch
                            file.obj.file.upload_file(lst)
                            break
            self.jrc.update({"content": fmd})

    def save_or_update_item_metadata(self):
        """Save or update item metadata.

        Save when register a new item type,
        Update when edit an item type.

        """
        if self.is_edit:
            obj = ItemsMetadata.get_record(self.id)
            obj.update(self.data)
            obj.commit()
        else:
            ItemsMetadata.create(self.data, id_=self.pid.object_uuid,
                                 item_type_id=self.get('item_type_id'))

    def delete_old_file_index(self):
        """Delete old file index before file upload when edit am item."""
        if self.is_edit:
            lst = ObjectVersion.get_by_bucket(
                self.files.bucket, True).filter_by(is_head=False).all()
            klst = []
            for obj in lst:
                if obj.file_id:
                    klst.append(obj.file_id)
            if klst:
                self.indexer.delete_file_index(klst, self.pid.object_uuid)


class WekoRecord(Record):
    """Extend Record obj for record ui."""

    file_cls = WekoFileObject

    # files_iter_cls = WekoFilesIterator

    record_fetcher = staticmethod(weko_deposit_fetcher)

    @property
    def pid(self):
        """Return an instance of record PID."""
        pid = self.record_fetcher(self.id, self)
        return PersistentIdentifier.get(pid.pid_type, pid.pid_value)

    @property
    def navi(self):
        """Return the path name."""
        return Indexes.get_path_name(self.get('path', []))

    @property
    def item_type_info(self):
        """Return the information of item type."""
        item_type = ItemTypes.get_by_id(self.get('item_type_id'))
        return "{}({})".format(item_type.item_type_name.name, item_type.tag)

    @property
    def editable(self):
        """Return the permission of modifying item."""
        return current_weko_items_ui.permission.can()

    @property
    def items_show_list(self):
        """Return the item show list."""
        ojson = ItemTypes.get_record(self.get('item_type_id'))
        items = []
        solst = find_items(ojson.model.form)

        for lst in solst:
            key = lst[0].split('.')[-1]

            val = self.get(key)
            if not val:
                continue

            mlt = val.get('attribute_value_mlt')
            if mlt:
                nval = dict()
                nval['attribute_name'] = val.get('attribute_name')
                nval['attribute_value_mlt'] = get_all_items(mlt, solst)
                items.append(nval)
            else:
                items.append(val)
        return items
