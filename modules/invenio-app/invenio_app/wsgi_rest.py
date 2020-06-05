# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST-only WSGI application for Invenio flavours."""

from __future__ import absolute_import, print_function

from .factory import create_api

#: WSGI application for Invenio REST API.
application = create_api()
