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

"""IPython notebooks previewer."""

from __future__ import absolute_import, unicode_literals

import nbformat
from flask import render_template
from nbconvert import HTMLExporter


def render(file):
    """Generate the result HTML."""
    fp = file.open()
    content = fp.read()
    fp.close()

    notebook = nbformat.reads(content.decode('utf-8'), as_version=4)

    html_exporter = HTMLExporter()
    html_exporter.template_file = 'basic'
    (body, resources) = html_exporter.from_notebook_node(notebook)
    return body, resources


def can_preview(file):
    """Determine if file can be previewed."""
    return file.is_local() and file.has_extensions('.ipynb')


def preview(file):
    """Render the IPython Notebook."""
    body, resources = render(file)
    default_ipython_style = resources['inlining']['css'][1]
    return render_template(
        'invenio_previewer/ipynb.html',
        file=file,
        content=body,
        style=default_ipython_style
    )
