# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio App configuration.

`Invenio-App` is partially overwriting default configuration of `Limiter` and
`Talisman` applications.
You can find below more details about which configuration are set.

For more information, please also see
`Flask-Limiter <https://flask-limiter.readthedocs.io/en/stable/>`_ and
`Flask-Talisman <https://github.com/GoogleCloudPlatform/flask-talisman/>`__
websites.
"""

from __future__ import absolute_import, print_function, unicode_literals

from invenio_app.limiter import set_rate_limit

RATELIMIT_APPLICATION = set_rate_limit
"""Global rate limit."""

RATELIMIT_STRATEGY = 'moving-window'
"""The rate limiting strategy to use.

The strategy used here is the most consistant but also expensive one.
If you are experiencing performance issues due to the increased Redis
traffic, you can replace it with another one from the following
`Flask-Limiter strategies
<https://flask-limiter.readthedocs.io/en/stable/#ratelimit-strategy>`_.
"""

RATELIMIT_HEADERS_ENABLED = True
"""Enable rate limit headers. (Default: ``True``)"""

RATELIMIT_STORAGE_URL = 'memory://'
"""Storage backend to store rate-limiting information.

    Memory is used by default if no value is provided.
    For more information regarding the mentioned above configuration values and
    their available options you can see the `Flask-Limiter configuration
    <https://flask-limiter.readthedocs.io/en/stable/#configuration>`_.

.. note::

   Provide your Redis URL if you are rate limiting a multithreaded application.

"""

RATELIMIT_KEY_FUNC = None
"""Define custom key function.

This config is not part of Flask-Limiter.

This function is used to generate a unique key for each visitor to track
the number of performed requests. If not defined, the default ``key_func``
will be used, which will create the key by concatenating the user agent and
the IP address of the user.

For more information you can also see `here
<https://flask-limiter.readthedocs.io/en/stable/#rate-limit-domain>`_
"""

RATELIMIT_PER_ENDPOINT = {}
"""Specifically defined Flask rate limits per endpoint.

This config is not part of Flask-Limiter.
Use this for endpoints that need to be *whitelisted*, providing the Flask
blueprint path accompanied by a `rate limit value
<https://flask-limiter.readthedocs.io/en/stable/#rate-limit-string-notation>`_.

.. code-block:: python

    RATELIMIT_PER_ENDPOINT = \
    {
        'zenodo_frontpage.index': '10 per second',
        'security.login': '10 per second'
    }
"""

RATELIMIT_AUTHENTICATED_USER = '5000 per hour;100 per minute'
"""Rate limit for logged in users."""

RATELIMIT_GUEST_USER = '1000 per hour;60 per minute'
"""Rate limit for non logged in users."""

APP_ENABLE_SECURE_HEADERS = True
"""Enable Secure Headers. (Default: ``True``)

In case you want to disable completely `Talisman`, you can set to `False`.

Remember that, for development purpose, setting ```DEBUG = True``` is already
enough to disable any side effects such as force ``https``.

.. note::
    `W3C
    <https://www.w3.org/TR/CSP2/>`_
"""

APP_DEFAULT_SECURE_HEADERS = {
    'force_https': True,
    'force_https_permanent': False,
    'force_file_save': False,
    'frame_options': 'sameorigin',
    'frame_options_allow_from': None,
    'strict_transport_security': True,
    'strict_transport_security_preload': False,
    'strict_transport_security_max_age': 31556926,  # One year in seconds
    'strict_transport_security_include_subdomains': True,
    'content_security_policy': {
        'default-src': ["'self'"],
        'object-src': ["'none'"]
    },
    'content_security_policy_report_uri': None,
    'content_security_policy_report_only': False,
    'session_cookie_secure': True,
    'session_cookie_http_only': True
}
"""Talisman default Secure Headers configuration.

As default, invenio assumes that HTTPS is enabled.
If you are not using SSL, then remember to disable the `force_https` and
`session_cookie_secure` configuration options related to HTTPS.

Please note that, as default `Talisman` behaviour, if Flask `DEBUG` mode is on,
then also many security barriers are automatically switched off
(e.g. `force_https` and `session_cookie_secure`).

.. note:: Overwrite
    `Flask-Talisman
    <https://github.com/GoogleCloudPlatform/flask-talisman>`_ configuration.

.. code-block:: python

    from flask import Flask
    from flask_talisman import Talisman

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY='SECRET_KEY'
    )
    talisman = Talisman(app)

    @app.route('/defenders')
    @talisman(frame_options_allow_from='*')
    def defenders():
        \"\"\"Override policies for the specific view.\"\"\"
        return 'Jessica Jones'
"""

APP_ALLOWED_HOSTS = None
"""A list of host/domain names that can be served.

This is a security measure to prevent HTTP Host header attacks, which are
possible even under many seemingly-safe web server configurations.

By default all hosts are allowed. Values in this list can be fully qualified
names (e.g. 'www.example.com'). The validation only applies to
``request.host``.

In addition to this configuration variable, you should make sure that your
web server does not route requests to the application with an invalid Host
header.
"""

APP_HEALTH_BLUEPRINT_ENABLED = True
"""Enable the ping (healthcheck) blueprint. (Default: ``False``)
"""

APP_REQUESTID_HEADER = "X-Request-Id"
"""Name of header containing a request id (max length 200 characters).

If set, the request id will be extracted from the header and set on the global
Flask ``g`` request object. The extracted request id can be used by other
Invenio modules - e.g. Invenio-Logging could include it in log messages.

The request id can be used to trace requests between systems to make
troubleshooting easier.

You can configure Nginx 1.10+ to automatically generate a request id and
add it as a header to both the upstream WSGI server and downstream client::

    add_header X-Request-ID $request_id;

Set to ``None`` to not extract a request id.
"""
