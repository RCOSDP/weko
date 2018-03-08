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

from flask import current_app, abort, json
from invenio_db import db
from invenio_deposit.api import Deposit, index, preserve
from invenio_files_rest.models import Bucket, MultipartObject, Part
from invenio_records_files.models import RecordsBuckets
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records_files.api import FileObject, FilesIterator, Record, \
    _writable
import redis
from simplekv.memory.redisstore import RedisStore
from weko_records.api import ItemTypes, ItemsMetadata
from weko_records.utils import save_item_metadata, save_items_data, \
    upload_metadata
from .pidstore import weko_deposit_fetcher, weko_deposit_minter

# from invenio_pidrelations.contrib.records import RecordDraft, index_siblings
# from invenio_pidrelations.contrib.versioning import PIDVersioning
# from .models import WekoObjectVersion
from weko_index_tree.api import Indexes
from weko_items_ui import current_weko_items_ui

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


# def sorted_files_from_bucket(bucket, keys=None):
#     """Return files from bucket sorted by given keys.
#
#     :param bucket: :class:`~invenio_files_rest.models.Bucket` containing the
#         files.
#     :param keys: Keys order to be used.
#     :returns: Sorted list of bucket items.
#     """
#     keys = keys or []
#     total = len(keys)
#     sortby = dict(zip(keys, range(total)))
#     values = WekoObjectVersion.get_by_bucket(bucket).all()
#     return sorted(values, key=lambda x: sortby.get(x.key, total))


class WekoFileObject(FileObject):
    """extend  FileObject for detail page """

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


# class WekoFilesIterator(FilesIterator):
#     """ extend  FilesIterator for detail page"""
#
#     def __iter__(self):
#         """"""
#         self._it = iter(sorted_files_from_bucket(self.bucket, self.keys))
#         return self
#
#     def __getitem__(self, key):
#         """Get a specific file."""
#         obj = WekoObjectVersion.get(self.bucket, key)
#         if obj:
#             return self.file_cls(obj, self.filesmap.get(obj.key, {}))
#         raise KeyError(key)


class WekoIndexer(object):
    """"""

    def index(self, record):
        pass

    def delete(self, record):
        pass


class WekoDeposit(Deposit):
    """Define API for changing deposit state."""

    indexer = WekoIndexer()

    # files_iter_cls = WekoFilesIterator

    deposit_fetcher = staticmethod(weko_deposit_fetcher)

    deposit_minter = staticmethod(weko_deposit_minter)

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

        dc, jrc = save_item_metadata(data, self.pid)
        self.data = data
        self.jrc = jrc

        # Save Index Path on ES
        jrc.update(dict(path=td))
        dc.update(dict(path=td))

        super(WekoDeposit, self).update(dc)

    @preserve(result=False, fields=PRESERVE_FIELDS)
    def clear(self, *args, **kwargs):
        """Clear only drafts."""
        super(WekoDeposit, self).clear(*args, **kwargs)

    def commit(self, *args, **kwargs):
        """Store changes on current instance in database and index it."""

        super(WekoDeposit, self).commit(*args, **kwargs)
        if self.data and len(self.data):
            fmd = self.data.get("filemeta")
            save_items_data(self.data, self.pid.object_uuid,
                            self.get('item_type_id'))

            if self.jrc and len(self.jrc):
                # upload item metadata to Elasticsearch
                upload_metadata(self.jrc, self.pid.object_uuid)
            for file in self.files:
                if isinstance(fmd, list):
                    for lst in fmd:
                        if file.obj.key == lst.get('filename'):
                            lst.update({'mimetype': file.obj.mimetype})

                            # update file_files's json
                            file.obj.file.update_json(lst)

                            # upload file metadata to Elasticsearch
                            file.obj.file.upload_file(lst,
                                                      str(file.obj.file_id),
                                                      self.pid.object_uuid,
                                                      'weko', 'content')
                            break

    @property
    def item_metadata(self):
        return ItemsMetadata.get_record(self.id).dumps()


class WekoRecord(Record):
    """ extend Record obj for record ui"""

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
        """"""
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

