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

from flask import current_app, json, request, render_template, render_template_string, flash

from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.schemas.json import RecordSchemaJSONV1
from .atom import AtomSerializer
from weko_search_ui.views import search

class OpenSearchSerializer(JSONSerializer):
    """
    extend JSONSerializer to modify search result
    """

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.
        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        format = request.values.get('format')
        if not format or format == 'atom':
            mimetype = 'application/atom+xml'
            atom_v1 = AtomSerializer(RecordSchemaJSONV1)
            return atom_v1.serialize_search(pid_fetcher, search_result,
                                            links=None, item_links_factory=None,
                                            **kwargs), mimetype
        else:
            mimetype = 'application/json'
            json_v1 = JSONSerializer(RecordSchemaJSONV1)
            return json_v1.serialize_search(pid_fetcher, search_result,
                                            links=None, item_links_factory=None,
                                            **kwargs), mimetype
