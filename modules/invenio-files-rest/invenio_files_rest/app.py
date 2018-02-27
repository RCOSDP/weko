# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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

from __future__ import absolute_import, print_function

from flask import Flask as FlaskBase

from .wrappers import Request


class Flask(FlaskBase):
    """Flask application class needed to use custom request class."""

    request_class = Request
