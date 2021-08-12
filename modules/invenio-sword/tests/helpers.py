# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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
"""Pytest helpers."""
from __future__ import absolute_import
from __future__ import print_function

import binascii
from copy import deepcopy

from flask_security import url_for_security
from six import BytesIO


def stringio_to_base64(stringio_obj):
    """Get base64 encoded version of a BytesIO object."""
    return binascii.b2a_base64(stringio_obj.getvalue())


def make_file_fixture(filename, base64_file):
    """Generate a file fixture suitable for use with the Flask test client.

    :param base64_file: A string encoding a file in base64. Use
        file_to_base64() to get the base64 encoding of a file. If not provided
        a PDF file be generated instead, including
    """
    fp = BytesIO(binascii.a2b_base64(base64_file))
    return fp, filename


def make_pdf_fixture(filename, text=None):
    """Generate a PDF fixture.

    It's suitable for use with Werkzeug test client and Flask test request
    context.
    Use of this function requires that reportlab have been installed.

    :param filename: Desired filename.
    :param text: Text to include in PDF. Defaults to "Filename: <filename>", if
        not specified.
    """
    if text is None:
        text = "Filename: %s" % filename

    # Generate simple PDF
    from reportlab.pdfgen import canvas

    output = BytesIO()
    c = canvas.Canvas(output)
    c.drawString(100, 100, text)
    c.showPage()
    c.save()

    return make_file_fixture(filename, stringio_to_base64(output))


def fill_oauth2_headers(json_headers, token):
    """Create authentication headers (with a valid oauth2 token)."""
    headers = deepcopy(json_headers)
    headers.append(("Authorization", "Bearer {0}".format(token.access_token)))
    return headers


def login(client, email="info@inveniosoftware.org", password="tester", **kwargs):
    client.post(
        url_for_security("login"), data={"email": email, "password": password},
    )
