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

"""Utilities for convert response json."""

import json
import os
import shutil
import sys
import tempfile
import traceback
from datetime import datetime
from functools import wraps

from flask import abort, current_app, request, send_file
from invenio_search import RecordsSearch
from weko_deposit.api import WekoRecord
from weko_index_tree.api import Indexes
from weko_items_ui.utils import make_stats_tsv, package_export_file
from weko_records.api import ItemTypes
from weko_records_ui.permissions import check_file_download_permission

from .api import ResourceListHandler
from .query import item_path_search_factory


def to_dict(resource):
    """Generate Resource Object to Dict."""
    return dict(**{
        'id': resource.id,
        'status': resource.status,
        'repository': resource.repository_id,
        'resource_dump_manifest': resource.resource_dump_manifest,
        'url_path': resource.url_path,
        'repository_name': resource.index.index_name or resource.index.index_name_english
    })


def render_resource_list_xml(index_id):
    """Generate Resource List Xml."""
    return ResourceListHandler.get_content_resource_list(index_id)


def render_resource_dump_xml(index_id):
    """Generate Resource Dump Xml."""
    return ResourceListHandler.get_content_resource_dump(index_id)


def get_file_content(index_id, record_id):
    """Generate File content."""
    record = WekoRecord.get_record_by_pid(record_id)
    list_index = get_real_path(record.get("path"))
    if ResourceListHandler.is_resync(list_index):
        return export_item_custorm({'record_id': record_id, 'index_id': index_id})
    else:
        return None


def get_resourcedump_manifest(index_id, record_id):
    """Generate File content."""
    record = WekoRecord.get_record_by_pid(record_id)
    list_index = get_real_path(record.get("path"))
    if ResourceListHandler.is_resync(list_index):
        return ResourceListHandler.get_resourcedump_manifest(index_id, record)
    else:
        return None


def get_real_path(path):
    """Generate list index id from path."""
    result = []
    for item in path:
        if '/' in item:
            fl = item.split("/")
            result.extend(fl)
        else:
            result.append(item)
    return list(set(result))


def export_item_custorm(post_data):
    """Gather all the item data and export and return as a JSON or BIBTEX.

    :return: JSON, BIBTEX
    """
    include_contents = True
    record_id = post_data['record_id']
    index_id = post_data['index_id']

    result = {'items': []}
    temp_path = tempfile.TemporaryDirectory()
    item_types_data = {}

    try:
        # Set export folder
        export_path = temp_path.name + '/' + datetime.utcnow().strftime(
            "%Y%m%d%H%M%S")
        # Double check for limits
        record_path = export_path + '/recid_' + str(record_id)
        os.makedirs(record_path, exist_ok=True)
        record, exported_item = _export_item(
            record_id,
            None,
            include_contents,
            record_path,
        )

        result['items'].append(exported_item)

        item_type_id = exported_item.get('item_type_id')
        item_type = ItemTypes.get_by_id(item_type_id)
        if not item_types_data.get(item_type_id):
            item_types_data[item_type_id] = {}

            item_types_data[item_type_id] = {
                'item_type_id': item_type_id,
                'name': '{}({})'.format(
                    item_type.item_type_name.name,
                    item_type_id),
                'root_url': request.url_root,
                'jsonschema': 'items/jsonschema/' + item_type_id,
                'keys': [],
                'labels': [],
                'recids': [],
                'data': {},
            }
        item_types_data[item_type_id]['recids'].append(record_id)

        # Create export info file
        for item_type_id in item_types_data:
            keys, labels, records = make_stats_tsv(
                item_type_id,
                item_types_data[item_type_id]['recids'])
            item_types_data[item_type_id]['recids'].sort()
            item_types_data[item_type_id]['keys'] = keys
            item_types_data[item_type_id]['labels'] = labels
            item_types_data[item_type_id]['data'] = records
            item_type_data = item_types_data[item_type_id]

            with open('{}/{}.tsv'.format(export_path,
                                         item_type_data.get('name')),
                      'w') as file:
                tsvs_output = package_export_file(item_type_data)
                file.write(tsvs_output.getvalue())

        # Create bag
        # bagit.make_bag(export_path)
        with open('{}/{}.xml'.format(export_path,
                                     'manifest'),
                  'w') as file:
            xml_output = ResourceListHandler.get_resourcedump_manifest(index_id, record)
            file.write(xml_output)

        # Create download file
        shutil.make_archive(export_path, 'zip', export_path)
    except Exception:
        current_app.logger.error('-' * 60)
        traceback.print_exc(file=sys.stdout)
        current_app.logger.error('-' * 60)
    return send_file(export_path + '.zip')


def _export_item(record_id,
                 export_format,
                 include_contents,
                 tmp_path=None,
                 records_data=None):
    """Exports files for record according to view permissions."""
    exported_item = {}
    record = WekoRecord.get_record_by_pid(record_id)

    if record:
        exported_item['record_id'] = record.id
        exported_item['name'] = 'recid_{}'.format(record_id)
        exported_item['files'] = []
        exported_item['path'] = 'recid_' + str(record_id)
        exported_item['item_type_id'] = record.get('item_type_id')
        if not records_data:
            records_data = record

        # Create metadata file.
        with open('{}/{}_metadata.json'.format(tmp_path,
                                               exported_item['name']),
                  'w',
                  encoding='utf8') as output_file:
            json.dump(records_data, output_file, indent=2,
                      sort_keys=True, ensure_ascii=False)
        # First get all of the files, checking for permissions while doing so
        if include_contents:
            # Get files
            for file in record.files:  # TODO: Temporary processing
                if check_file_download_permission(record, file.info()):
                    exported_item['files'].append(file.info())
                    # TODO: Then convert the item into the desired format
                    if file:
                        shutil.copy2(file.obj.file.uri,
                                     tmp_path + '/' + file.obj.basename)

    return record, exported_item


def public_index_checked(f):
    """Decorator to pass community."""
    @wraps(f)
    def decorate(index_id, record_id=None, *args, **kwargs):
        if record_id:
            current_app.logger.debug("================")
            current_app.logger.debug(record_id)
            record = WekoRecord.get_record_by_pid(record_id)
            if not record:
                abort(404, 'Current Record isn\'t public.')
            list_index = get_real_path(record.get("path"))
            if index_id not in list_index:
                abort(404, 'Current Repository isn\'t belong to Index.')
        index = Indexes.get_index(index_id)
        if index is None or not index.public_state:
            abort(404, 'Current Repository isn\'t public.')
        if record_id:
            return f(index_id, record_id, *args, **kwargs)
        else:
            return f(index_id, *args, **kwargs)

    return decorate


def get_items_by_index_tree(index_tree_id):
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance = item_path_search_factory(records_search, index_id=index_tree_id)
    search_result = search_instance.execute()
    rd = search_result.to_dict()
    return rd.get('hits').get('hits')
