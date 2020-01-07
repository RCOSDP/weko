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
from functools import wraps

from flask import abort, current_app
from weko_deposit.api import WekoRecord
from weko_index_tree.api import Indexes
from weko_items_ui.utils import export_item_custorm

from .api import ResourceListHandler


def to_dict(resource):
    """Generate Resource Object to Dict"""
    return dict(**{
        'id': resource.id,
        'status': resource.status,
        'repository': resource.repository_id,
        'resource_dump_manifest': resource.resource_dump_manifest,
        'url_path': resource.url_path,
        'repository_name': resource.index.index_name or resource.index.index_name_english
    })

def render_resource_list_xml(index_id):
    """Generate Resource List Xml"""
    return ResourceListHandler.get_content_resource_list(index_id)

def render_resource_dump_xml(index_id):
    """Generate Resource Dump Xml"""
    return ResourceListHandler.get_content_resource_dump(index_id)


def get_file_content(record_id):
    """Generate File content"""
    record = WekoRecord.get_record_by_pid(record_id)
    list_index = get_real_path(record.get("path"))
    if ResourceListHandler.is_resync(list_index):
        return export_item_custorm({'record_id': record_id})
    else:
        return None


def get_resourcedump_marnifest(record_id):
    """Generate File content"""
    record = WekoRecord.get_record_by_pid(record_id)
    list_index = get_real_path(record.get("path"))
    if ResourceListHandler.is_resync(list_index):
        return ResourceListHandler.get_resourcedump_manifest(record)
    else:
        return None


def get_real_path(path):
    """Generate list index id from path"""
    result = []
    for item in path:
        if '/' in item:
            fl = item.split("/")
            result.extend(fl)
        else:
            result.append(item)
    return result


def public_index_checked(f):
    """Decorator to pass community."""
    @wraps(f)
    def decorate(index_id, *args, **kwargs):
        index = Indexes.get_index(index_id)
        if index is None or index.public_state == True:
            abort(404, 'Bucket does not exist.')
        return f(index_id, *args, **kwargs)

    return decorate
