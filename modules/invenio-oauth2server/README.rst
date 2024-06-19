..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

======================
 Invenio-OAuth2Server
======================

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-oauth2server.svg
        :target: https://github.com/inveniosoftware/invenio-oauth2server/blob/master/LICENSE

.. image:: https://github.com/inveniosoftware/invenio-oauth2server/workflows/CI/badge.svg
        :target: https://github.com/inveniosoftware/invenio-oauth2server/actions

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-oauth2server.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-oauth2server

.. image:: https://img.shields.io/pypi/v/invenio-oauth2server.svg
        :target: https://pypi.org/pypi/invenio-oauth2server


Invenio module that implements OAuth 2 server.

* Free software: MIT license
* Documentation: https://invenio-oauth2server.readthedocs.io/

Features
========

* Implements the OAuth 2.0 authentication protocol.
    - Provides REST API to provide access tokens.
    - Provides decorators that can be used to restrict access to resources.
* Handles authentication using JSON Web Tokens.
* Adds support for CSRF protection in REST API.
