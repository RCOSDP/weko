# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request wrapper."""

from flask.wrappers import Request as RequestBase

from .formparser import FormDataParser


class Request(RequestBase):
    """Custom request class needed for using custom form data parser."""

    form_data_parser_class = FormDataParser
