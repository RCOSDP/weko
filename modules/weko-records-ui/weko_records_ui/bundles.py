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
from invenio_deposit.bundles import js_dependencies_jquery

style = NpmBundle(
    'node_modules/angular-loading-bar/build/loading-bar.css',
    'node_modules/typeahead.js-bootstrap-css/typeaheadjs.css',
    'node_modules/bootstrap-switch/dist/css/bootstrap3',
    'css/weko_records_ui/style.css',
    output="gen/weko_records_ui.%(version)s.css",
    npm={
        'bootstrap-sass': '~3.3.5',
        'bootstrap-switch': '~3.0.2',
        'font-awesome': '~4.4.0',
        'typeahead.js-bootstrap-css': '~1.2.1',
    }
)

js_angular_bootstrap = NpmBundle(
    'node_modules/angular-ui-bootstrap/ui-bootstrap-tpls.js',
    'node_modules/angular/angular.js',
    npm={
        'angular-ui-bootstrap': '~0.13.2',
    }
)

js_almond = NpmBundle(
    'node_modules/almond/almond.js',
    npm={
        'almond': '~0.3.1',
    }
)

js_angular_loading_bar = NpmBundle(
    'node_modules/angular-loading-bar/build/loading-bar.js',
    npm={
        'angular-loading-bar': '~0.9.0',
    }
)

js_typeahead = NpmBundle(
    'node_modules/typeahead.js/dist/bloodhound.js',
    'node_modules/typeahead.js/dist/typeahead.bundle.js',
    'node_modules/typeahead.js/dist/typeahead.jquery.js',
    npm={
        'typeahead.js': '~0.11.1'
    }
)

js_invenio_csl = NpmBundle(
    'node_modules/invenio-csl-js/dist/invenio-csl-js.js',
    npm={
        'invenio-csl-js': '~0.1.3',
    }
)

js_bootstrap_switch = NpmBundle(
    'node_modules/bootstrap-switch/dist/js/bootstrap-switch.js',
    npm={
        'bootstrap-switch': '~3.0.2',
    }
)

js_dependecies = NpmBundle(
    # js_dependencies_jquery,
    js_angular_bootstrap,
    js_almond,
    js_angular_loading_bar,
    js_typeahead,
    js_invenio_csl,
    js_bootstrap_switch,
    filters='jsmin',
    output='gen/weko_records_ui.dependencies.%(version)s.js',
)

js = NpmBundle(
    'node_modules/angular-ui-bootstrap/ui-bootstrap-tpls.js',
    'node_modules/angular/angular.js',
    'js/weko_records_ui/app.js',
    'js/weko_records_ui/detail.js',
    'js/weko_records_ui/csl.js',
    filters='jsmin',
    output="gen/weko_records_ui.%(version)s.js",
    npm={
        'angular-ui-bootstrap': '~0.13.2',
    },
)
