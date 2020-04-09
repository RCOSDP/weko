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

"""Configuration for weko-authors."""

from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix

WEKO_AUTHORS_LIST_SCHEME = ['e-Rad', 'NRID', 'ORCID', 'ISNI', 'VIAF', 'AID',
                            'Kakenhi', 'Ringgolf', 'GRID', 'Other']
""" List of scheme """

WEKO_AUTHORS_INDEX_ITEM_OTHER = 9
""" Item other index """

WEKO_AUTHORS_BASE_TEMPLATE = 'weko_authors/base.html'
"""Default base template for the author page."""

WEKO_AUTHORS_ADMIN_LIST_TEMPLATE = 'weko_authors/admin/author_list.html'
"""List template for the admin author page."""

WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE = 'weko_authors/admin/author_edit.html'
"""Edit template for the admin author page."""

WEKO_AUTHORS_ADMIN_PREFIX_TEMPLATE = 'weko_authors/admin/prefix_list.html'
"""template for the id prefix settings page."""

WEKO_AUTHORS_NUM_OF_PAGE = 25
"""Default number of author search results that display in one page."""

WEKO_AUTHORS_ES_INDEX_NAME = "{}-authors".format(index_prefix)
"""Elasticsearch index alias for author."""

WEKO_AUTHORS_ES_DOC_TYPE = "author-v1.0.0"
"""Elasticsearch document type for author."""
