# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
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

"""Previews a JSON file."""
from __future__ import absolute_import, print_function

import orjson
import re
from collections import OrderedDict

from flask import current_app, render_template, request

from ..utils import detect_encoding

previewable_extensions = ['json']


def validate_json(file):
    """Validate a JSON file."""
    max_file_size = current_app.config.get(
        'PREVIEWER_MAX_FILE_SIZE_BYTES', 1 * 1024 * 1024)
    if file.size > max_file_size:
        return False

    with file.open() as fp:
        try:
            json_data = orjson.loads(fp.read().decode('utf-8'))
            if "@context" in json_data.keys():
                context = json_data["@context"]
                if type(context) is list:
                    context = ",".join(context)
                if re.match("http://iiif.io/api/presentation/./context.json", context):
                    return True
            return False
        except BaseException:
            return False


def can_preview(file):
    """Determine if the given file can be previewed."""
    
    if (file.is_local() and file.filename == 'manifest.json'
            and validate_json(file)):
        return True
    if (file.is_local() and file.filename == 'manifest.json'):
        return True


def preview(file):
    """Render appropiate template with embed flag."""
    url = file.uri
    if (not validate_json(file)):
        url = request.url_root+'api/iiif/v2/records/'+file.pid.pid_value+'/manifest.json'
    
    return render_template(
        'invenio_previewer/iiif_presentation.html',
        file=url,
    )
