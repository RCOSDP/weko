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

from .utils import OpenSearchDetailData


class AtomSerializer(JSONSerializer):
    """Serialize search result to atom format."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: search engine search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory:
        """
        detail_data = OpenSearchDetailData(pid_fetcher, search_result,
                                           OpenSearchDetailData.OUTPUT_ATOM,
                                           links, item_links_factory, **kwargs)
        return detail_data.output_open_search_detail_data()
