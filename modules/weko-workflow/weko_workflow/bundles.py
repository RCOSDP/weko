# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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

css_workflow = Bundle(
    'css/weko_workflow/style.css',
    output="gen/workflow_workflow.css"
)

css_datepicker_workflow = Bundle(
    'css/weko_workflow/bootstrap-datepicker3.standalone.min.css',
    output="gen/bootstrap-datepicker3.css"
)
