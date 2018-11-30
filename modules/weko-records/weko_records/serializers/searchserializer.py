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

"""WEKO Search Serializer."""
from invenio_records_rest.serializers.json import JSONSerializer
from weko_records.utils import sort_meta_data_by_options

from flask import json, flash

from weko_index_tree.utils import get_user_roles, get_user_groups, \
    check_roles, check_groups
from weko_index_tree.api import Indexes

class SearchSerializer(JSONSerializer):
    """
    extend JSONSerializer to modify search result
    """

    def transform_search_hit(self, pid, record_hit, links_factory=None):
        sort_meta_data_by_options(record_hit)
        return super(SearchSerializer, self).\
            transform_search_hit(pid, record_hit, links_factory)
