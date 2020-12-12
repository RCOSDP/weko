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

"""Previews an XML file."""

from __future__ import absolute_import, print_function

import xml.dom.minidom

from flask import current_app, render_template

from ..utils import detect_encoding

previewable_extensions = ['xml']


def render(file):
    """Pretty print the XML file for rendering."""
    with file.open() as fp:
        encoding = detect_encoding(fp, default='utf-8')
        file_content = fp.read().decode(encoding)
        parsed_xml = xml.dom.minidom.parseString(file_content)
        return parsed_xml.toprettyxml(indent='  ', newl='')


def validate_xml(file):
    """Validate an XML file."""
    max_file_size = current_app.config.get(
        'PREVIEWER_MAX_FILE_SIZE_BYTES', 1 * 1024 * 1024)
    if file.size > max_file_size:
        return False

    with file.open() as fp:
        try:
            content = fp.read().decode('utf-8')
            xml.dom.minidom.parseString(content)
            return True
        except BaseException:
            return False


def can_preview(file):
    """Determine if the given file can be previewed."""
    return (file.is_local()
            and file.has_extensions('.xml')
            and validate_xml(file))


def preview(file):
    """Render appropiate template with embed flag."""
    return render_template(
        'invenio_previewer/xml_prismjs.html',
        file=file,
        content=render(file),
        js_bundles=['previewer_prism_js'],
        css_bundles=['previewer_prism_css'],
    )
