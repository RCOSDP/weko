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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Bundles for weko-grid-layout module."""
from flask_assets import Bundle

widget_design_js_lib = Bundle(
    'js/weko_gridlayout/jquery-ui.js',
    'js/weko_gridlayout/lodash.min.js',
    'js/weko_gridlayout/gridstack.js',
    'js/weko_gridlayout/gridstack.jQueryUI.js',
    filters='jsmin',
    output="gen/weko_gridlayout_lib.%(version)s.js",
)

widget_design_reactjs_lib = Bundle(
    'js/weko_gridlayout/react.production.min.js',
    'js/weko_gridlayout/react-dom.production.min.js',
    'js/weko_gridlayout/browser.min.js',
    filters='jsmin',
    output="gen/weko_gridlayout_reactjs_lib.%(version)s.js",
)

widget_design_js = Bundle(
    'js/weko_gridlayout/widget.design.js',
    filters='jsmin',
    output="gen/weko_gridlayout_widget_design.%(version)s.js",
)

widget_setting_js = Bundle(
    'js/weko_gridlayout/widget.setting.js',
    filters='jsmin',
    output="gen/weko_gridlayout_widget_setting.%(version)s.js",
)

widget_design_css = Bundle(
    'css/weko_gridlayout/gridstack.css',
    'css/weko_gridlayout/styles.css',
    output="gen/weko_gridlayout.%(version)s.css",
)

widget_setting_css = Bundle(
    'css/weko_gridlayout/widget.item.css',
    output="gen/weko_gridlayout_widget_setting.%(version)s.css",
)

katex_min_css = Bundle(
    'css/weko_gridlayout/katex.min.css',
    output="gen/weko_gridlayout_katex_min.%(version)s.css",
)

katex_min_js = Bundle(
    'js/weko_gridlayout/katex.min.js',
    output="gen/weko_gridlayout_katex_min.%(version)s.js",
)

prop_types_js = Bundle(
    'js/weko_gridlayout/prop.types.js',
    output="gen/weko_gridlayout_prop_types.%(version)s.js",
)

react_quill_js = Bundle(
    'js/weko_gridlayout/react.quill.js',
    output="gen/weko_gridlayout_react_quill.%(version)s.js",
)
