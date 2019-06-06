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

"""Bundles for weko-admin-ui."""

from flask_assets import Bundle

js = Bundle(
    'js/weko_admin/block_style.js',
    'js/weko_admin/app.js',
    filters='requirejs',
    output="gen/weko_admin_ui.%(version)s.js",
)

report_reactjs_lib = Bundle(
    'js/weko_admin/react.production.min.js',
    'js/weko_admin/react-dom.production.min.js',
    'js/weko_admin/browser.min.js',
    filters='jsmin',
    output="gen/weko_report_reactjs_lib.%(version)s.js",
)

custom_report_js = Bundle(
    'js/weko_admin/custom_report.js',
    filters='jsmin',
    output="gen/weko_custom_report.%(version)s.js",
)

search_management_js = Bundle(
    'js/weko_admin/search_management.js',
    filters='requirejs',
    output="gen/weko_admin_ui_search.%(version)s.js",
)

stats_report_js = Bundle(
    'js/weko_admin/stats_report.js',
    output="gen/weko_admin_ui_stats_report.%(version)s.js",
)

log_analysis_js = Bundle(
    'js/weko_admin/log_analysis.js',
    output="gen/weko_admin_ui_log_analysis.%(version)s.js",
)

date_picker_css = Bundle(
    'css/weko_admin/react-datepicker.min.css',
    'css/weko_admin/react-datepicker-cssmodules.min.css',
    output="gen/weko_admin_date_picker.%(version)s.css",
)

date_picker_js = Bundle(
    'js/weko_admin/bootstrap-datepicker.min.js',
    'js/weko_admin/prop-types.min.js',
    output="gen/weko_admin_date_picker.%(version)s.js",
)

css = Bundle(
    'css/weko_admin/styles.css',
    output="gen/weko_admin_ui.%(version)s.css",
)

weko_admin_quill_sknow_css = Bundle(
    'css/weko_admin/quill.snow.css',
    output="gen/weko_admin_ui_quill.%(version)s.css",
)
