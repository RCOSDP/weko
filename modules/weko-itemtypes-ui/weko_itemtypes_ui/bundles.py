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

"""Bundles for weko-itemtypes-ui."""

from flask_assets import Bundle
from invenio_assets import NpmBundle

style = Bundle(
    'css/weko_itemtypes_ui/itemtype.less',
    filters='cleancss',
    output="gen/itemtypes_ui.%(version)s.css"
)

style_mapping = Bundle(
    'css/weko_itemtypes_ui/mapping.less',
    filters='cleancss',
    output="gen/mapping_ui.%(version)s.css"
)

style_rocrate_mapping = Bundle(
    'css/weko_itemtypes_ui/rocrate_mapping.less',
    filters='cleancss',
    output='gen/rocrate_mapping_ui.%(version)s.css'
)

js_dependencies_schema_editor = NpmBundle(
    'node_modules/react/dist/react.js',
    'node_modules/react-dom/dist/react-dom.js',
    npm={
        'react': '0.14.8',
        'react-dom': '0.14.8',
    },
)

js_dependencies = NpmBundle(
    js_dependencies_schema_editor,
    filters='jsmin',
    output='gen/itemtypes_ui.dependencies.%(version)s.js',
)

js_schema_editor = NpmBundle(
    'js/weko_itemtypes_ui/jsonschemaeditor.js',
    output='gen/itemtypes_ui.schema_editor.js',
)

js = Bundle(
    'js/weko_itemtypes_ui/create_itemtype.js',
    filters='jsmin',
    output="gen/itemtypes_ui.js"
)

js_property = Bundle(
    'js/weko_itemtypes_ui/create_property.js',
    filters='jsmin',
    output="gen/itemtypes_ui_property.js"
)

js_mapping = Bundle(
    'js/weko_itemtypes_ui/create_mapping.js',
    filters='jsmin',
    output="gen/itemtypes_ui_mapping.js"
)

js_rocrate_mapping = Bundle(
    'js/weko_itemtypes_ui/create_rocrate_mapping.js',
    filters='jsmin',
    output='gen/itemtypes_ui_rocrate_mapping.js'
)
