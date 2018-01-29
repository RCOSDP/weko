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

"""Query factories for REST API."""

from functools import partial

from elasticsearch_dsl.query import Q
from flask import current_app, request

from .errors import InvalidQueryRESTError


def default_search_factory(self, search, query_parser=None):
    """Parse query using Invenio-Query-Parser.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :param query_parser: parser query method
    :returns: Tuple with search instance and URL arguments.
    """
    def _default_parser(qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl."""
        if qstr:
            return Q('query_string', query=qstr)
        return Q()

    from .facets import default_facets_factory
    from .sorter import default_sorter_factory

    query_string = request.values.get('q')
    query_parser = query_parser or _default_parser

    try:
        search = search.query(query_parser(query_string))
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(
                request.values.get('q', '')),
            exc_info=True)
        raise InvalidQueryRESTError()

    search_index = search._index[0]
    search, urlkwargs = default_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

    urlkwargs.add('q', query_string)
    return search, urlkwargs


es_search_factory = default_search_factory


def invenio_search_parser(search_factory):
    """Set the default search factory to use invenio-query-parser.

    :param search_factory: factory for search
    """
    from invenio_query_parser.contrib.elasticsearch import IQ
    return partial(default_search_factory, query_parser=IQ)


invenio_search_factory = invenio_search_parser(default_search_factory)
