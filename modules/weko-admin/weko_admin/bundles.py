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
from invenio_assets import NpmBundle

js = Bundle(
    'js/weko_admin/block_style.js',
    'js/weko_admin/app.js',
    filters='requirejs',
    output="gen/weko_admin_ui.%(version)s.js",
)

statistics_reactjs_lib = Bundle(
    'js/weko_admin/react.production.min.js',
    'js/weko_admin/react-dom.production.min.js',
    'js/weko_admin/browser.min.js',
    filters='jsmin',
    output="gen/weko_statistics_reactjs_lib.%(version)s.js",
)

custom_report_js = Bundle(
    'js/weko_admin/custom_report.js',
    filters='jsmin',
    output="gen/weko_custom_report.%(version)s.js",
)

search_management_js = Bundle(
    'js/weko_admin/search_management.js',
    output="gen/weko_admin_ui_search.%(version)s.js",
)

react_bootstrap_js = Bundle(
    'js/weko_admin/react-bootstrap.min.js',
    output="gen/react_bootstrap_js.%(version)s.js",
)

stats_report_js = Bundle(
    'js/weko_admin/stats_report.js',
    'js/weko_admin/email_schedule.js',
    output="gen/weko_admin_ui_stats_report.%(version)s.js",
)

feedback_mail_js = Bundle(
    'js/weko_admin/feedback_mail.js',
    filters='jsmin',
    output="gen/weko_admin_feedback_mail.%(version)s.js",
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

weko_admin_feedback_mail_css = Bundle(
    'css/weko_admin/feedback.mail.css',
    output="gen/weko_admin_feedback_mail.%(version)s.css",
)

admin_lte_js_dependecies = NpmBundle(
    'node_modules/jquery/jquery.js',
    'node_modules/moment/moment.js',
    'node_modules/select2/dist/js/select2.full.js',
    'node_modules/requirejs/require.js',
    'js/settings.js',
    'node_modules/angular/angular.js',
    filters='jsmin',
    npm={
        'requirejs': '~2.3.6',
        'jquery': '~1.9.1',
        'angular': '~1.4.9',
        'moment': '~2.9.0',
        'select2': '~4.0.2',
    },
    output='gen/weko_admin_ui.admin_js_dependecies.%(version)s.js',
)

admin_lte_js = NpmBundle(
    'node_modules/admin-lte/dist/js/app.js',
    npm={
        'admin-lte': '~2.3.6',
    },
    output='gen/weko_admin_ui.admin_lte_js.%(version)s.js',
)

angular_js = NpmBundle(  # Already included in front-end
    'node_modules/angular/angular.js',
    npm={
        'angular': '~1.4.9',
    },
    output='gen/weko_admin_ui.angular_js.%(version)s.js',
)

weko_admin_sword_api_jsonld_js = Bundle(
    'js/weko_admin/sword_api_jsonld_setting.js',
    output="gen/weko_admin_sword_api_jsonld.%(version)s.js",
)

weko_admin_jsonld_mapping_js = Bundle(
    'js/weko_admin/jsonld_mapping_setting.js',
    output="gen/weko_admin_jsonld_mapping.%(version)s.js",
)


weko_admin_site_info_js = Bundle(
    'js/weko_admin/site_info.js',
    filters='jsmin',
    output="gen/weko_admin_site_info_js.%(version)s.js",
)

weko_admin_site_info_css = Bundle(
    'css/weko_admin/site.info.css',
    output="gen/weko_site_info_css.%(version)s.css",
)

weko_admin_ng_js_tree_js = NpmBundle(
    'js/weko_admin/jstree.min.js',
    'js/weko_admin/ngJsTree.min.js',
    filters='jsmin',
    output='gen/weko_admin_ui.ng_js_tree.%(version)s.js',
)

weko_admin_restricted_access_js = NpmBundle(
    'js/weko_admin/restricted_access.js',
    # filters='jsmin',
    output='gen/restricted_access.%(version)s.js',
)

weko_admin_facet_search_js = NpmBundle(
    'js/weko_admin/facet_search_admin.js',
    output='gen/facet_search.%(version)s.js',
)

weko_admin_cris_linkage_js = NpmBundle(
    'js/weko_admin/cris_linkage.js',
    output='gen/cris_linkage.%(version)s.js',
)

reindex_elasticsearch_js = NpmBundle(
    'js/weko_admin/reindex_elasticsearch.js',
    output='gen/reindex_elasticsearch.%(version)s.js',
)
