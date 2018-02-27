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

"""Request customization tests."""

from __future__ import absolute_import, print_function

from flask import request
from six import BytesIO

from invenio_files_rest.app import Flask


def test_max_content_length():
    """Test max content length."""
    max_len = 10

    app = Flask('test')
    app.config['MAX_CONTENT_LENGTH'] = max_len

    @app.route('/test', methods=['GET', 'PUT'])
    def test():
        # Access request.form to ensure form parser kicks-in.
        request.form.to_dict()
        return request.stream.read()

    with app.test_client() as client:
        # No content-type, no max content length checking
        data = b'a' * (max_len + 1)
        res = client.put('/test', input_stream=BytesIO(data))
        assert res.status_code == 200
        assert res.data == data

        # Non-formdata content-type, no max content length checking
        res = client.put(
            '/test',
            input_stream=BytesIO(data),
            headers={'Content-Type': 'application/octet-stream'}
        )
        assert res.status_code == 200
        assert res.data == data

        # With form data content-type (below max content length)
        res = client.put(
            '/test',
            data={'123': 'a' * (max_len - 4)}  # content-length == 10
        )
        assert res.status_code == 200
        # Because formdata parsing reads the data stream, trying to read it
        # again means we just get empty data:
        assert res.data == b''

        # With formdata content-type (above max content length)
        res = client.put(
            '/test',
            data={'123': 'a' * (max_len - 3)}  # content-length == 11
        )
        assert res.status_code == 413
