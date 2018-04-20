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

"""Permissions for Detail Page."""

from datetime import datetime as dt
from invenio_access import action_factory, Permission

detail_page_access = action_factory('detail-page-access')
detail_page_permission = Permission(detail_page_access)


def page_permission_factory(record, *args, **kwargs):
    def can(self):
        is_can = detail_page_permission.can()
        if not is_can:
            pst = record.get('publish_status')
            pdt = record.get('pubdate', {}).get('attribute_value')
            try:
                pdt = dt.strptime(pdt, '%Y-%m-%d')
                pdt = True if dt.today() >= pdt else False
            except:
                pdt = False
            if pst and '0' in pst and pdt:
                is_can = True
        return is_can
    return type('DetailPagePermissionChecker', (), {'can': can})()
