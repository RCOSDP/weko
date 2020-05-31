# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI application for Invenio flavours."""

from __future__ import absolute_import, print_function

from invenio_base.app import create_cli

from .factory import create_app

#: Invenio CLI application.
cli = create_cli(create_app=create_app)
