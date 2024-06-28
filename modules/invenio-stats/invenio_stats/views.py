# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""InvenioStats views."""

from flask import Blueprint, abort, jsonify, request
from invenio_rest.views import ContentNegotiatedMethodView
from invenio_search.engine import search

from .errors import InvalidRequestInputError, UnknownQueryError
from .proxies import current_stats
from .utils import current_user

blueprint = Blueprint(
    "invenio_stats",
    __name__,
    url_prefix="/stats",
)


class StatsQueryResource(ContentNegotiatedMethodView):
    """REST API resource providing access to statistics."""

    view_name = "stat_query"

    def __init__(self, **kwargs):
        """Constructor."""
        super(StatsQueryResource, self).__init__(
            serializers={
                "application/json": lambda data, *args, **kwargs: jsonify(data),
            },
            default_method_media_type={
                "GET": "application/json",
            },
            default_media_type="application/json",
            **kwargs
        )

    def post(self, **kwargs):
        """Get statistics."""
        data = request.get_json(force=False)
        if data is None:
            data = {}

        result = {}
        for query_name, config in data.items():
            if (
                config is None
                or not isinstance(config, dict)
                or (
                    set(config.keys()) != {"stat", "params"}
                    and set(config.keys()) != {"stat"}
                )
            ):
                # 'config' has to be a dictionary with mandatory 'stat' key and
                # optional 'params' key, and nothing else
                raise InvalidRequestInputError(
                    "Invalid Input. It should be of the form "
                    '{ STATISTIC_NAME: { "stat": STAT_TYPE, '
                    '"params": STAT_PARAMS }}'
                )

            stat = config["stat"]
            params = config.get("params", {})
            try:
                query = current_stats.get_query(stat)
            except KeyError:
                raise UnknownQueryError(stat)

            permission = current_stats.permission_factory(stat, params)
            if permission is not None and not permission.can():
                message = (
                    "You do not have a permission to query the "
                    'statistic "{}" with those '
                    "parameters".format(stat)
                )

                if current_user.is_authenticated:
                    abort(403, message)

                abort(401, message)

            try:
                result[query_name] = query.run(**params)

            except ValueError as e:
                raise InvalidRequestInputError(e.args[0])
            except search.exceptions.NotFoundError:
                # In case there is no index or value for the metric we return 0
                result[query_name] = dict.fromkeys(query.metric_fields.keys(), 0)

        return self.make_response(result)


stats_view = StatsQueryResource.as_view(
    StatsQueryResource.view_name,
)

blueprint.add_url_rule(
    "",
    view_func=stats_view,
)
