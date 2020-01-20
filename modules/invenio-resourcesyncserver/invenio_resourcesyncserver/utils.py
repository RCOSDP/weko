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
from weko_deposit.api import WekoRecord
from weko_index_tree.api import Indexes
from weko_items_ui.utils import make_stats_tsv, package_export_file
from weko_records.api import ItemTypes
from weko_records_ui.permissions import check_file_download_permission

from .api import ResourceListHandler, ChangeListHandler
from resync.list_base_with_index import ListBaseWithIndex
from resync import Resource, CapabilityList


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


def render_capability_xml():
    """Generate capability xml."""
    cap = CapabilityList()
    list_resource = ResourceListHandler.get_capability_content()
    list_change = ChangeListHandler.get_capability_content()
    total_list = [*list_resource, *list_change]
    for item in total_list:
        cap.add(item)

    return cap.as_xml()


def render_well_know_resourcesync():
    """Generate capability xml."""
    cap = ListBaseWithIndex(
        capability_name='description',
        ln=[
            {
                'href': request.url_root,
                'rel': 'describedby'
            }
        ]
    )
    cap.add(Resource(
                '{}resync/capability.xml'.format(request.url_root),
                capability='capability'))

    return cap.as_xml()


