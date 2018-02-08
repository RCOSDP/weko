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

"""Configuration for weko-records-ui."""

WEKO_RECORDS_UI_DETAIL_TEMPLATE = 'weko_records_ui/detail.html'

RECORDS_UI_ENDPOINTS = dict(
    recid=dict(
        pid_type='recid',
        route="/records/<pid_value>",
        view_imp="weko_records.fd.weko_view_method",
        template="weko_records_ui/detail.html",
    ),
    recid_export=dict(
        pid_type='recid',
        route="/records/<pid_value>/export/<format>",
        view_imp="invenio_records_ui.views.export",
        template="weko_records_ui/export.html",
    ),
    recid_files=dict(
        pid_type='recid',
        route='/record/<pid_value>/files/<path:filename>',
        view_imp='weko_records.fd.file_download_ui',
    ),
    recid_preview=dict(
        pid_type='recid',
        route='/record/<pid_value>/preview/<path:filename>',
        view_imp='weko_records.fd.file_preview_ui',
    ),
)
