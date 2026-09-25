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

from functools import wraps

import pkg_resources
from flask import abort, current_app, request
from flask_login import current_user
from flask_principal import ActionNeed
from invenio_access import Permission, action_factory

superuser_access = Permission(action_factory('superuser-access'))

action_admin_access = ActionNeed('read-style-action')
action_admin_update = ActionNeed('update-style-action')
"""Define the action needed by the default permission factory."""

_action2need_map = {
    'read-style-action': action_admin_access,
    'update-style-action': action_admin_update,
}


def admin_permission_factory(action):
    """Default factory for creating a permission for an admin.

    It tries to load a :class:`invenio_access.permissions.DynamicPermission`
    instance if `invenio_access` is installed.
    Otherwise, it loads a :class:`flask_principal.Permission` instance.

    :param admin_view: Instance of administration view which is currently being
        protected.
    :returns: Permission instance.
    """
    action_class = _action2need_map[action]
    try:
        pkg_resources.get_distribution('invenio-access')
        from invenio_access.permissions import Permission as Permission
    except pkg_resources.DistributionNotFound:
        from flask_principal import Permission

    return Permission(action_class)


def _is_super_user(user):
    """Check whether the user has a system/repository administrator role."""
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
    return any(role.name in supers for role in (user.roles or []))


def _is_community_admin(user):
    """Check whether the user has a community administrator role."""
    comadmin = current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
    return any(role.name in comadmin for role in (user.roles or []))


def repository_scope_required(repository_id_param=None,
                               id_param=None, id_model=None, id_attr='repository_id',
                               pk_attr='id'):
    """repository_id(またはid_param経由でid_modelから解決したid_attr)が
    current_userの担当範囲内であることを要求する。

    - System/Repository Administrator: 無条件許可
    - Community Administrator: 担当コミュニティ(Community.get_repositories_by_user)のみ許可
    - id_paramが指定されかつ値が存在する場合はDB側の値を優先する
      (クライアント送信値より、既存レコードの実際の所属を信頼する)
    - pk_attr: id_modelの主キー列名。デフォルトは'id'。主キーが異なる場合は
      明示的に指定する(例: WidgetItemはid列を持たず主キーはwidget_id)
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if _is_super_user(current_user):
                return f(*args, **kwargs)

            data = request.get_json(silent=True) or request.form or request.args
            repository_id = None

            target_id = (data.get(id_param) or kwargs.get(id_param)) if id_param else None
            if target_id:
                record = id_model.query.filter_by(**{pk_attr: target_id}).one_or_none()
                if record is None:
                    abort(404)
                repository_id = getattr(record, id_attr, None)
            elif repository_id_param:
                repository_id = data.get(repository_id_param) or kwargs.get(repository_id_param)

            if _is_community_admin(current_user) and repository_id:
                # weko_admin初期化時のimportで循環参照が発生するため、
                # get_repository_list()と同様に関数内でimportする。
                from invenio_communities.models import Community
                communities = Community.get_repositories_by_user(current_user)
                if any(str(c.id) == str(repository_id) for c in communities):
                    return f(*args, **kwargs)

            abort(403)
        return wrapped
    return decorator
