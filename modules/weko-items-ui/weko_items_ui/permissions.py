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

"""Permissions for items."""

from invenio_access import Permission, action_factory
from weko_records_ui.permissions import check_created_id

action_item_access = action_factory('item-access')
item_permission = Permission(action_item_access)


def edit_permission_factory(record, **kwargs):
    """Edit permission factory.

    編集権限そのものを見る。作成者・所有者・共有者・
    System/Repository Administrator・該当コミュニティの
    Community Administrator が対象。

    以前は page_permission_factory(record, flg='Edit') に委譲していたが、
    page_permission_factory は flg を一度も参照しない閲覧用の判定で、
    「公開アイテム かつ 閲覧可能インデックス配下」なら匿名でも True を返す。
    編集系にこれを当てていたため、認証が実質無効になっていた
    (/item/edit, /item/iframe/edit, /record/<pid>/publish)。
    """
    def can(self):
        return check_created_id(record)
    return type('EditPermissionChecker', (), {'can': can})()
