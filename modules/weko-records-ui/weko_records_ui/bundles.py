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

style = NpmBundle(
    'node_modules/angular-loading-bar/build/loading-bar.css',
    'node_modules/typeahead.js-bootstrap-css/typeaheadjs.css',
    'node_modules/bootstrap-switch/dist/css/bootstrap3/bootstrap-switch.css',
    'css/weko_records_ui/style.css',
    output="gen/weko_records_ui.%(version)s.css",
    npm={
        'bootstrap-sass': '~3.3.5',
        'bootstrap-switch': '~3.0.2',
        'font-awesome': '~4.4.0',
        'typeahead.js-bootstrap-css': '~1.2.1',
    }
)

js_dependecies = NpmBundle(
    "node_modules/angular-ui-bootstrap/ui-bootstrap-tpls.js",
    "node_modules/angular/angular.js",
    'node_modules/angular-animate/angular-animate.js',
    'node_modules/angular-sanitize/angular-sanitize.js',
    'node_modules/angular-strap/dist/angular-strap.js',
    "node_modules/angular-loading-bar/build/loading-bar.js",
    "node_modules/typeahead.js/dist/bloodhound.js",
    "node_modules/typeahead.js/dist/typeahead.bundle.js",
    "node_modules/typeahead.js/dist/typeahead.jquery.js",
    "node_modules/invenio-csl-js/dist/invenio-csl-js.js",
    "node_modules/bootstrap-switch/dist/js/bootstrap-switch.js",
    filters='jsmin',
    output='gen/weko_records_ui.dependencies.%(version)s.js',
    npm={
        'angular-animate': '~1.4.8',
        'angular-sanitize': '~1.4.10',
        'angular-strap': '~2.3.9',
        'angular-ui-bootstrap': '~0.13.2',
        'almond': '~0.3.1',
        'angular-loading-bar': '~0.9.0',
        'typeahead.js': '~0.11.1',
        'invenio-csl-js': '~0.1.3',
        'bootstrap-switch': '~3.0.2',
    }
)

js = NpmBundle(
    'node_modules/angular-ui-bootstrap/ui-bootstrap-tpls.js',
    'node_modules/angular/angular.js',
    'js/weko_records_ui/app.js',
    'js/weko_records_ui/csl.js',
    'js/weko_records_ui/detail.js',
    'js/weko_records_ui/bulk_update.js',
    filters='jsmin',
    output="gen/weko_records_ui.%(version)s.js",
    npm={
        'angular-ui-bootstrap': '~0.13.2',
    },
)

preview_carousel = Bundle(
    'js/weko_records_ui/preview_carousel.js',
    filters='jsmin',
    output="gen/weko_records_ui_preview_carousel.%(version)s.js",
)

file_action_js = Bundle(
    'js/weko_records_ui/file_action.js',
    filters='jsmin',
    output="gen/weko_records_ui_file_action.%(version)s.js",
)

bucket_js = Bundle(
    'js/weko_records_ui/bucket.js',
    filters='jsmin',
    output="gen/weko_records_ui_bucket_js.%(version)s.js",
)

bootstrap_popover_js = Bundle(
    'js/weko_records_ui/bootstrap-popover-x.min.js',
    filters='jsmin',
    output="gen/bootstrap_popover_js.%(version)s.js",
)

bootstrap_popover_css = Bundle(
    'css/weko_records_ui/bootstrap-popover-x.min.css',
    output="gen/bootstrap_popover_css.%(version)s.css",
)
