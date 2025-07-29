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

"""Bundles for weko-items-ui."""

from flask_assets import Bundle
from invenio_assets import NpmBundle, RequireJSFilter

indextree_style = Bundle(
    'css/weko_items_ui/indextree.bundle.css',
    'css/weko_items_ui/styles.bundle.css',
    filters='cleancss',
    output="gen/indextree_ui.%(version)s.css"
)

js_dependencies_angularjs = NpmBundle(
    'js/weko_items_ui/inline.bundle.js',
    'js/weko_items_ui/polyfills.bundle.js',
    'js/weko_items_ui/main.bundle.js',
)

js_angular_ui = NpmBundle(
    'js/weko_items_ui/ui-bootstrap-tpls.min.js',
)

js_dependencies = NpmBundle(
    js_dependencies_angularjs,
    output='gen/items_ui.dependencies.js',
)

items_author_search_css = Bundle(
    'css/weko_items_ui/styles.items.authorSearch.bundle.css',
    filters='cleancss',
    output="gen/items_ui_authorSearch.%(version)s.css"
)

items_author_search_js = NpmBundle(
    'js/weko_items_ui/inline.items.authorSearch.bundle.js',
    'js/weko_items_ui/polyfills.items.authorSearch.bundle.js',
    'js/weko_items_ui/main.items.authorSearch.bundle.js',
    filters='jsmin',
    output="gen/items_ui_authorSearch.%(version)s.js",
)

js = Bundle(
    'js/weko_items_ui/app.js',
    output="gen/items_ui.%(version)s.js",
)

dependencies_upload_js = NpmBundle(
    'node_modules/tv4/tv4.js',
    'node_modules/objectpath/lib/ObjectPath.js',
    filters=RequireJSFilter(),
)
upload_js = NpmBundle(
    'node_modules/angular-sanitize/angular-sanitize.min.js',
    dependencies_upload_js,
    'js/weko_items_ui/upload.js',
    output="gen/items_ui_upload.%(version)s.js",
)

feedback_maillist_js = Bundle(
    'js/weko_items_ui/feedback_maillist.js',
    filters='jsmin',
    output="gen/weko_items_ui_feedback_maillist.%(version)s.js",
)

feedback_maillist_css = Bundle(
    'css/weko_items_ui/feedback.mail.css',
    output="gen/weko_items_ui_feedback_maillist.%(version)s.css",
)

request_maillist_js = Bundle(
    'js/weko_items_ui/request_maillist.js',
    filters='jsmin',
    output="gen/weko_items_ui_request_maillist.%(version)s.js",
)

no_file_approval_js = Bundle(
    'js/weko_items_ui/no_file_approval.js',
    filters='jsmin',
    output="gen/weko_items_ui_no_file_approval.%(version)s.js",
)
