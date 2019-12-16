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

"""Views module tests."""

from __future__ import absolute_import, print_function

from flask import render_template_string


def test_view_macro_file_list(app):
    """Test file list macro."""
    with app.test_request_context():
        files = [
            {
                'uri': 'http://domain/test1.txt',
                'key': 'test1.txt',
                'size': 10,
                'date': '2016-07-12',
            },
            {
                'uri': 'http://otherdomain/test2.txt',
                'key': 'test2.txt',
                'size': 12,
                'date': '2016-07-12',
            },
        ]

        result = render_template_string("""
            {%- from "invenio_previewer/macros.html" import file_list %}
            {{ file_list(files) }}
            """, files=files)

        assert '<a class="forcewrap" href="http://domain/test1.txt"' in result
        assert '<td class="nowrap">2016-07-12' in result
        assert '<td class="nowrap">10</td>' in result
        assert 'href="http://otherdomain/test2.txt"' in result
        assert '<td class="nowrap">2016-07-12</td>' in result
        assert '<td class="nowrap">12</td>' in result


def test_previwable_test(app):
    """Test template test."""
    file = {
        'type': 'md'
    }
    template = "{% if file.type is previewable %}Previwable" \
               "{% else %}Not previwable{% endif %}"
    assert render_template_string(template, file=file) == "Previwable"

    file['type'] = 'no'
    assert render_template_string(template, file=file) == "Not previwable"

    file['type'] = 'pdf'
    assert render_template_string(template, file=file) == "Previwable"

    file['type'] = ''
    assert render_template_string(template, file=file) == "Not previwable"
