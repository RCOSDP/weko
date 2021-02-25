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

"""API for item login."""

import os

import redis
from flask import current_app, json, session, url_for, flash, redirect, request, send_file
from flask_login import login_required, current_user
from simplekv.memory.redisstore import RedisStore
from weko_records.api import ItemTypes
from weko_records.utils import find_items

from .permissions import item_permission
from .utils import is_schema_include_key, _get_max_export_items, write_tsv_files, \
    write_bibtex_files, get_ignore_item_from_mapping, hide_meta_data_for_role
from weko_records_ui.permissions import check_file_download_permission
import tempfile
from datetime import date, datetime, timedelta
import traceback
import sys
from flask_babelex import gettext as _
import re
import shutil
import bagit
from celery import shared_task
from weko_deposit.api import WekoRecord


@login_required
@item_permission.require(http_exception=403)
def item_login(item_type_id=0):
    """Return information that item register need.

    :param item_type_id: Item type ID. (Default: 0)
    """
    template_url = 'weko_items_ui/iframe/item_edit.html'
    need_file = False
    need_billing_file = False
    record = {}
    json_schema = ''
    schema_form = ''
    item_save_uri = url_for('weko_items_ui.iframe_save_model')
    files = []
    endpoints = {}
    need_thumbnail = False
    files_thumbnail = []
    allow_multi_thumbnail = False

    try:
        item_type = ItemTypes.get_by_id(item_type_id)
        if item_type is None:
            template_url = 'weko_items_ui/iframe/error.html'
        json_schema = '/items/jsonschema/{}'.format(item_type_id)
        schema_form = '/items/schemaform/{}'.format(item_type_id)
        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        activity_session = session['activity_info']
        activity_id = activity_session.get('activity_id', None)
        if activity_id and sessionstore.redis.exists(
                'activity_item_' + activity_id):
            item_str = sessionstore.get('activity_item_' + activity_id)
            item_json = json.loads(item_str)
            if 'metainfo' in item_json:
                record = item_json.get('metainfo')
            if 'files' in item_json:
                files = item_json.get('files')
                files_thumbnail = [i for i in files
                                   if 'is_thumbnail' in i.keys()
                                   and i['is_thumbnail']]
            if 'endpoints' in item_json:
                endpoints = item_json.get('endpoints')

        need_file, need_billing_file = is_schema_include_key(item_type.schema)

        if 'subitem_thumbnail' in json.dumps(item_type.schema):
            need_thumbnail = True
            key = [i[0].split('.')[0] for i in find_items(item_type.form)
                   if 'subitem_thumbnail' in i[0]]
            option = item_type.render.get('meta_list', {}). \
                get(key[0].split('[')[0], {}).get('option')
            if option:
                allow_multi_thumbnail = option.get('multiple')
    except Exception as e:
        template_url = 'weko_items_ui/iframe/error.html'
        current_app.logger.debug(str(e))

    return template_url, need_file, need_billing_file, \
        record, json_schema, schema_form, \
        item_save_uri, files, endpoints, need_thumbnail, files_thumbnail, \
        allow_multi_thumbnail

class Exporter():
    """ Class Exporter """
    @classmethod
    def __init__(self, post_data, pathfoldertemp):
        """ Init Data """  
        self._record_ids = json.loads(post_data['record_ids'])  #List item need to export
        self._record_metadata = json.loads(post_data['record_metadata'])        #Metadata
        self._temp_path = pathfoldertemp                                        #TempFile is Store in Server
        self._pathfile = None                                                   #Path File is Store in Server

    @classmethod
    def export_items(self):
        """Gather all the item data and export and return as a JSON
        :return: JSON
        """
        def check_item_type_name(name):
            """Check a list of allowed characters in filenames."""
            new_name = re.sub(r'[\/:*"<>|\s]', '_', name)
            return new_name

        item_types_data = {}
        # Set export folder
        export_path = self._temp_path .name + '/' + \
            datetime.utcnow().strftime("%Y%m%d%H%M%S")
        # Double check for limits
        for record_id in self._record_ids:
            record_path = export_path + '/recid_' + str(record_id)
            os.makedirs(record_path, exist_ok=True)
            exported_item, list_item_role = self._export_item(
                record_id,
                record_path,
                self._record_metadata.get(str(record_id))
            )

            item_type_id = exported_item.get('item_type_id')
            item_type = ItemTypes.get_by_id(item_type_id)
            if not item_types_data.get(item_type_id):
                item_type_name = check_item_type_name(
                    item_type.item_type_name.name)
                item_types_data[item_type_id] = {
                    'item_type_id': item_type_id,
                    'name': '{}({})'.format(
                        item_type_name,
                        item_type_id),
                    'root_url': request.url_root,
                    'jsonschema': 'items/jsonschema/' + item_type_id,
                    'keys': [],
                    'labels': [],
                    'recids': [],
                    'data': {},
                }
            item_types_data[item_type_id]['recids'].append(record_id)

        # Create export info JSON file
            write_tsv_files(item_types_data, export_path, list_item_role)

        # Create bag
        bagit.make_bag(export_path)

        # Create download file
        shutil.make_archive(export_path, 'zip', export_path)

        return export_path 

    @classmethod
    def _export_item(self, record_id,
                    tmp_path=None,
                    records_data=None):
        """Exports files for record according to view permissions."""
        def del_hide_sub_metadata(keys, metadata):
            """Delete hide metadata."""
            if isinstance(metadata, dict):
                data = metadata.get(keys[0])
                if data:
                    if len(keys) > 1:
                        del_hide_sub_metadata(keys[1:], data)
                    else:
                        del metadata[keys[0]]
            elif isinstance(metadata, list):
                count = len(metadata)
                for index in range(count):
                    del_hide_sub_metadata(keys[1:] if len(
                        keys) > 1 else keys, metadata[index])

        exported_item = {}
        record = WekoRecord.get_record_by_pid(record_id)
        list_item_role = {}
        if record:
            exported_item['record_id'] = record.id
            exported_item['name'] = 'recid_{}'.format(record_id)
            exported_item['files'] = []
            exported_item['path'] = 'recid_' + str(record_id)
            exported_item['item_type_id'] = record.get('item_type_id')
            if not records_data:
                records_data = record
            if exported_item['item_type_id']:
                list_hidden = get_ignore_item_from_mapping(
                    exported_item['item_type_id'])
                if records_data.get('metadata'):
                    meta_data = records_data.get('metadata')
                    record_role_ids = {
                        'weko_creator_id': meta_data.get('weko_creator_id'),
                        'weko_shared_id': meta_data.get('weko_shared_id')
                    }
                    list_item_role.update(
                        {exported_item['item_type_id']: record_role_ids})
                    if hide_meta_data_for_role(record_role_ids):
                        for hide_key in list_hidden:
                            if isinstance(hide_key, str) \
                                    and meta_data.get(hide_key):
                                del records_data['metadata'][hide_key]
                            elif isinstance(hide_key, list):
                                del_hide_sub_metadata(
                                    hide_key, records_data['metadata'])

            # Create metadata file.
            with open('{}/{}_metadata.json'.format(tmp_path,
                                                exported_item['name']),
                    'w',
                    encoding='utf8') as output_file:
                json.dump(records_data, output_file, indent=2,
                        sort_keys=True, ensure_ascii=False)

        return exported_item, list_item_role