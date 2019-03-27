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

"""WEKO3 module docstring."""

from flask_assets import Bundle
from invenio_assets import NpmBundle

style = Bundle(
    'node_modules/angular-loading-bar/build/loading-bar.css',
    'css/weko_records_ui/style.css',
    output="gen/weko_records_ui.%(version)s.css"
)

# js_dependencies_angular_loading_bar = NpmBundle(
#     'node_modules/angular-loading-bar/build/*.js',
#     npm={
#         'angular-loading-bar': '~0.9.0',
#     }
# )
# 
# js_dependencies_invenio_csl_js = NpmBundle(
#     'node_modules/invenio-csl-js/dist/*.js',
#     npm={
#         'invenio-csl-js': '~0.1.3',
#     }
# )
# 
# js_dependencies_typeahead_js = NpmBundle(
#     'node_modules/typeahead.js/dist/*.js',
#     npm={
#         'typeahead.js': '~0.11.1',
#     }
# )

# js_dependencies = NpmBundle(
#     'node_modules/angular-ui-bootstrap/ui-bootstrap-tpls.js',
#     'node_modules/angular/angular.js',
#     'node_modules/bootstrap-switch/dist/js/bootstrap-switch.js',
#     js_dependencies_angular_loading_bar,
#     js_dependencies_invenio_csl_js,
#     js_dependencies_typeahead_js,
#     npm={
#         'angular-ui-bootstrap': '~0.13.2',
#         'bootstrap-switch': '~3.0.2',
#         'typeahead.js-bootstrap-css': '~1.2.1',
#     },
#     filters='requirejs',
#     output='gen/weko_records_ui.dependencies.%(version)s.js',
# )

js_dependencies_datepicker = NpmBundle(
    'node_modules/bootstrap-datepicker/dist/js/bootstrap-datepicker.js',
    npm={
        'bootstrap-datepicker': '~1.7.1',
    }
)

js_dependecies = NpmBundle(
    js_dependencies_datepicker,
    filters='requirejs',
    output='gen/weko_records_ui.dependencies.%(version)s.js',
)

js = NpmBundle(
    'node_modules/angular-ui-bootstrap/ui-bootstrap-tpls.js',
    'node_modules/angular/angular.js',
    'js/weko_records_ui/detail.js',
    'js/weko_records_ui/app.js',
    depends=(
        'node_modules/angular-loading-bar/build/*.js',
        'node_modules/typeahead.js/dist/*.js',
        'node_modules/invenio-csl-js/dist/*.js',
        'node_modules/bootstrap-switch/dist/js/bootstrap-switch.js',
    ),
    filters='jsmin',
    output="gen/weko_records_ui.%(version)s.js",
    npm={
        'angular-ui-bootstrap': '~0.13.2',
        'almond': '~0.3.1',
        'angular': '~1.4.9',
        'angular-sanitize': '~1.4.9',
        'angular-loading-bar': '~0.9.0',
        'bootstrap-switch': '~3.0.2',
        'invenio-csl-js': '~0.1.3',
        'typeahead.js': '~0.11.1',
        'typeahead.js-bootstrap-css': '~1.2.1',
    },
)
