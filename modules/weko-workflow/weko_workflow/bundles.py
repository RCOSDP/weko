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
    output="gen/workflow_item_link.js"
)

js_activity_list = Bundle(
    'js/weko_workflow/activity_list.js',
    filters='requirejs',
    output="gen/workflow_activity_list.js"
)

js_iframe = Bundle(
    'js/weko_workflow/iframe_pop.js',
    filters='requirejs',
    output="gen/workflow_iframe_pop.js"
)

css_workflow = Bundle(
    'css/weko_workflow/style.css',
    output="gen/workflow_workflow.css"
)
