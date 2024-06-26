# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Form data parser customization.

Flask and Werkzeug by default checks a request's content length against
``MAX_CONTENT_LENGTH`` configuration variable as soon as *any* content type is
specified in the request and not only when a form data content type is
specified. This behavior prevents both setting a MAX_CONTENT_LENGTH for form
data *and* allowing streaming uploads of large binary files.

In order to allow for both max content length checking and streaming uploads
of large files, we provide a custom form data parser which only checks the
content length if a form data content type is specified. The custom form data
parser is installed by using the custom Flask application class provided
provided in this module.
"""

from flask import Flask as FlaskBase

from .wrappers import Request


class Flask(FlaskBase):
    """Flask application class needed to use custom request class."""

    request_class = Request
