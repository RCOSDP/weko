# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask Limiter functions."""

from __future__ import absolute_import, print_function

import pkg_resources
from flask import current_app, g, request


def useragent_and_ip_limit_key():
    """Create key for the rate limiting."""
    return str(request.user_agent) + request.remote_addr


def set_rate_limit():
    r"""Set rates for Flask limiter.

    :return: a rate limit string with the Flask-Limiter format.

    For more information regarding the format you can see `here
    <https://flask-limiter.readthedocs
    .io/en/stable/#rate-limit-string-notation>`_.

    The order in which the rate will be evaluated is the following:

    1)Initially the endpoint is going to be evaluated against the whitelisted
    ones. If it has been marked as whitelisted then the custom limit for this
    endpoint will be the one to be returned.

    2)If the endpoint is not whitelisted and the flask-security package is
    installed, it will evaluate if the user is logged in and if this is the
    case it will also check if there is an explicitly defined rate limit for
    them by comparing theire ID with the ones present in the
    ```RATELIMIT_PER_USER``` mapping.
    If it is present then the custom rate limit value will be returned,
    otherwise the one returned will be the ```RATELIMIT_AUTHENTICATED_USER```

    3)Finally if none of the above is our case then the
    ```RATELIMIT_GUEST_USER``` will be the one to be returned.
    """
    endpoint_limits = \
        current_app.config.get('RATELIMIT_PER_ENDPOINT', {})
    if request.endpoint in endpoint_limits:
        # Case of whitelisted endpoint.
        return endpoint_limits[request.endpoint]
    try:
        pkg_resources.get_distribution('flask_security')
        from flask_security import current_user
        user = current_user
    except pkg_resources.DistributionNotFound:
        user = None
    if user and user.is_authenticated:
        return g.get(
            'user_rate_limit',
            current_app.config['RATELIMIT_AUTHENTICATED_USER']
        )
    return current_app.config['RATELIMIT_GUEST_USER']
