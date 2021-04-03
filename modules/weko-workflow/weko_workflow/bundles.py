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

js_workflow = Bundle(
    'js/weko_workflow/workflow_detail.js',
    filters='requirejs',
    output="gen/workflow_workflow.js"
)

js_item_link = Bundle(
    'js/weko_workflow/workflow_item_link.js',
    filters='requirejs',
    output="gen/workflow_item_link.%(version)s.js"
)

js_activity_list = Bundle(
    'js/weko_workflow/activity_list.js',
    'js/weko_workflow/bootstrap-datepicker.min.js',
    filters='requirejs',
    output="gen/workflow_activity_list.js"
)

js_iframe = Bundle(
    'js/weko_workflow/iframe_pop.js',
    filters='requirejs',
    output="gen/workflow_iframe_pop.js"
)

js_oa_policy = Bundle(
    'js/weko_workflow/workflow_oa_policy.js',
    filters='requirejs',
    output="gen/workflow_oa_policy.js"
)

js_identifier_grant = Bundle(
    'js/weko_workflow/workflow_identifier_grant.js',
    filters='requirejs',
    output="gen/workflow_identifier_grant.%(version)s.js"
)

js_quit_confirmation = Bundle(
    'js/weko_workflow/quit_confirmation.js',
    filters='requirejs',
    output="gen/workflow_quit_confirmation.%(version)s.js"
)

js_lock_activity = Bundle(
    'js/weko_workflow/lock_activity.js',
    filters='requirejs',
    output="gen/workflow_lock_activity.%(version)s.js"
)

js_admin_workflow_detail = Bundle(
    'js/weko_workflow/admin/workflow_detail.js',
    filters='jsmin',
    output="gen/weko_workflow_detail.%(version)s.js",
)

css_workflow = Bundle(
    'css/weko_workflow/style.css',
    output="gen/workflow_workflow.css"
)

css_datepicker_workflow = Bundle(
    'css/weko_workflow/bootstrap-datepicker3.standalone.min.css',
    output="gen/bootstrap-datepicker3.css"
)

js_admin_flow_detail = Bundle(
    'js/weko_workflow/admin/flow_detail.js',
    output="gen/weko_flow_detail.%(version)s.js",
)
