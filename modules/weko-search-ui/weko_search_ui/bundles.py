# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Bundles for weko-search-ui."""

from flask_assets import Bundle
from invenio_assets import NpmBundle

css = Bundle(
    'node_modules/bootstrap-datepicker/dist/css/bootstrap-datepicker.css',
    filters='cleancss',
    output='gen/weko_search_ui.%(version)s.css',
)

js_dependencies_datepicker = NpmBundle(
    'node_modules/bootstrap-datepicker/dist/js/bootstrap-datepicker.js',
    npm={
        'bootstrap-datepicker': '~1.7.1',
    }
)

js_dependecies = NpmBundle(
    js_dependencies_datepicker,
    filters='requirejs',
    output='gen/weko_search_ui.dependencies.%(version)s.js',
)

js = Bundle(
    'js/weko_search_ui/app.js',
    filters='requirejs',
    output="gen/weko_search_ui.%(version)s.js",
)
