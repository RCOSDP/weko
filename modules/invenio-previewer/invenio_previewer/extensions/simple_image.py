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

"""Previews simple image files."""

from __future__ import absolute_import, print_function

from flask import current_app, render_template

previewable_extensions = ['jpg', 'jpeg', 'png', 'gif']


def validate(file):
    """Validate a simple image file."""
    max_file_size = current_app.config.get(
        'PREVIEWER_MAX_IMAGE_SIZE_BYTES', 0.5 * 1024 * 1024)
    return file.size <= max_file_size


def can_preview(file):
    """Determine if the given file can be previewed."""
    supported_extensions = ('.jpg', '.jpeg', '.png', '.gif')
    return file.has_extensions(*supported_extensions) and validate(file)


def preview(file):
    """Render appropiate template with embed flag."""
    return render_template(
        'invenio_previewer/simple_image.html',
        file=file,
        file_url=file.uri
    )
