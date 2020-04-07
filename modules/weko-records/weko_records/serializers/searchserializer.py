# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO Search Serializer."""
from flask import flash, json
from invenio_records_rest.serializers.json import JSONSerializer
from weko_index_tree.api import Indexes
from weko_index_tree.utils import check_groups, check_roles, get_user_groups, \
    get_user_roles

from weko_records.utils import sort_meta_data_by_options


class SearchSerializer(JSONSerializer):
    """Extend JSONSerializer to modify search result."""

    def transform_search_hit(self, pid, record_hit, links_factory=None):
        """Transform search hit."""
        sort_meta_data_by_options(record_hit)
        return super(SearchSerializer, self).\
            transform_search_hit(pid, record_hit, links_factory)
