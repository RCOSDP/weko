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

"""Previewer bundles."""

from __future__ import unicode_literals

from flask_assets import Bundle
from invenio_assets import NpmBundle, RequireJSFilter

previewer_base_css = Bundle(
    "node_modules/bootstrap/dist/css/bootstrap.css",
    NpmBundle(
        npm={
            "bootstrap": "~3.3.6",
            "font-awesome": "~4.5.0",
        }
    ),
    output='gen/previewer-base.%(version)s.css'
)
"""CSS bundle for ZIP file previewer."""


previewer_base_js = Bundle(
    NpmBundle(
        npm={
            "bootstrap": "~3.3.6",
            "jquery": "~1.9.1",
        }
    ),
    "node_modules/bootstrap/dist/js/bootstrap.js",
    output='gen/previewer-base.%(version)s.js',
)
"""JavaScript bundle for basic tools."""

csv_previewer_js = Bundle(
    NpmBundle(
        npm={
            "flightjs": "~1.5.1",
            "d3": "~3.5.12",
            "jquery": "~1.9.1"
        }
    ),
    Bundle(
        "js/csv_previewer/init.js",
        filters=RequireJSFilter(optimize='none'),
    ),
    output="gen/csv_previewer.%(version)s.js",
)
"""JavaScript bundle for D3.js CSV previewer."""

pdfjs_css = Bundle(
    "css/pdfjs/viewer.css",
    output='gen/pdfjs.%(version)s.css',
)
"""CSS bundle for PDFjs previewer."""

pdfjs_js = Bundle(
    NpmBundle(
        npm={
            "pdfjs-dist": "1.4.192",
        }
    ),
    "node_modules/pdfjs-dist/web/compatibility.js",
    "node_modules/pdfjs-dist/build/pdf.js",
    "js/pdfjs/l10n.js",
    "js/pdfjs/viewer.js",
    output='gen/pdfjs.%(version)s.js',
)
"""JavaScript bundle for PDFjs previewer."""

fullscreen_js = Bundle(
    "js/zip/fullscreen.js",
    filters='uglifyjs',
    output='gen/fullscreen.%(version)s.js',
)
"""JavaScript bundle for ZIP file previewer."""

prism_js = Bundle(
    NpmBundle(
        npm={
            "prismjs": "1.4.1",
        },
    ),
    "node_modules/prismjs/prism.js",
    "node_modules/prismjs/components/prism-json.js",
    filters="uglifyjs",
    output='gen/prism.%(version)s.js',
)
"""JavaScript bundle for prism.js syntax highlighter."""

prism_css = Bundle(
    NpmBundle(
        npm={
            "prismjs": "1.4.1",
        },
    ),
    "node_modules/prismjs/themes/prism.css",
    "css/prismjs/simple.css",
    output='gen/prism.%(version)s.css'
)
"""CSS bundle for prism.js syntax highlighter."""

threejs = Bundle(
    NpmBundle(
        npm={
            "three": "0.127.0",
        },
    ),
    "node_modules/three/build/three.min.js",
    output='gen/threejs.%(version)s.js',
)
"""JavaScript bundle for prism.js syntax highlighter."""
