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

"""Bundles for invenio-resourcesyncclient."""

from flask_assets import Bundle

invenio_admin_resync_client_js = Bundle(
    'js/invenio_resourcesyncclient/resync_client.js',
    filters='jsmin',
    output="gen/invenio_resourcesyncclient_js.%(version)s.js",
)

invenio_admin_resync_client_css = Bundle(
    'css/invenio_resourcesyncclient/resync_client.css',
    output="gen/invenio_resourcesyncclient_css.%(version)s.css",
)
