# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015, 2016 CERN.
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

"""Render a CSV file using d3.js."""

from __future__ import absolute_import, print_function

import csv

from flask import current_app, render_template

from ..proxies import current_previewer
from ..utils import detect_encoding

previewable_extensions = ['csv', 'dsv']


def validate_csv(file):
    """Return dialect information about given csv file."""
    try:
        # Detect encoding and dialect
        with file.open() as fp:
            encoding = detect_encoding(fp, default='utf-8')
            sample = fp.read(
                current_app.config.get('PREVIEWER_CSV_VALIDATION_BYTES', 1024))
            delimiter = csv.Sniffer().sniff(sample.decode(encoding)).delimiter
            is_valid = True
    except Exception as e:
        current_app.logger.debug(
            'File {0} is not valid CSV: {1}'.format(file.uri, e))
        encoding = ''
        delimiter = ''
        is_valid = False

    return {
        'delimiter': delimiter,
        'encoding': encoding,
        'is_valid': is_valid
    }


def can_preview(file):
    """Determine if the given file can be previewed."""
    if file.is_local() and file.has_extensions('.csv', '.dsv'):
        return validate_csv(file)['is_valid']
    return False


def preview(file):
    """Render appropiate template with embed flag."""
    file_info = validate_csv(file)
    return render_template(
        'invenio_previewer/csv_bar.html',
        file=file,
        delimiter=file_info['delimiter'],
        encoding=file_info['encoding'],
        js_bundles=current_previewer.js_bundles + ['previewer_csv_js'],
        css_bundles=current_previewer.css_bundles,
    )
