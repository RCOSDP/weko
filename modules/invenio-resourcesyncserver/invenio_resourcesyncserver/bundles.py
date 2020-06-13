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

"""Bundles for invenio-resourcesyncserver."""

from flask_assets import Bundle

invenio_admin_resource_js = Bundle(
    'js/invenio-resourcesyncserver/resource.js',
    filters='jsmin',
    output="gen/invenio_admin_resource_js.%(version)s.js",
)

invenio_admin_resource_css = Bundle(
    'css/invenio-resourcesyncserver/resource.css',
    output="gen/invenio_resource_css.%(version)s.css",
)

invenio_admin_change_list_js = Bundle(
    'js/invenio-resourcesyncserver/change_list.js',
    filters='jsmin',
    output="gen/invenio_admin_change_list_js.%(version)s.js",
)

invenio_admin_change_list_css = Bundle(
    'css/invenio-resourcesyncserver/change_list.css',
    output="gen/invenio_change_list_css.%(version)s.css",
)
