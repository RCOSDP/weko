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

"""Database models for weko-accounts."""

from invenio_accounts.models import User
from invenio_db import db


class ShibbolethUser(db.Model):
    """Shibboleth User Model"""

    __tablename__ = "shibboleth_user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """ShibbolethUser identifier."""

    shib_eppn = db.Column(db.String(128), unique=True, nullable=False)
    """SHIB_ATTR_ePPN"""

    weko_uid = db.Column(db.Integer, db.ForeignKey(
        User.id, name='fk_shib_weko_user_id'))
    """ID of user to whom this shib user belongs."""

    weko_user = db.relationship(User, backref='shib_weko_user')

    shib_handle = db.Column(db.String(255), nullable=True)
    """SHIB_ATTR_HANDLE"""

    shib_role_authority_name = db.Column(db.String(255), nullable=True)
    """SHIB_ATTR_ROLE_AUTHORITY_NAME"""

    shib_page_name = db.Column(db.String(255), nullable=True)
    """SHIB_ATTR_PAGE_NAME"""

    shib_active_flag = db.Column(db.String(255), nullable=True)
    """SHIB_ATTR_ACTIVE_FLAG"""

    shib_mail = db.Column(db.String(255), nullable=True)
    """SHIB_ATTR_MAIL"""

    shib_user_name = db.Column(db.String(255), nullable=True)
    """SHIB_ATTR_USER_NAME"""

    shib_ip_range_flag = db.Column(db.String(255), nullable=True)
    """SHIB_ATTR_SITE_USER_WITHIN_IP_RANGE_FLAG"""

    @classmethod
    def create(cls, weko_user, **kwargs):
        """
        create shibboleth user
        :param weko_user: The :class:`invenio_accounts.models.User` instance.
        :param kwargs: Dict of shibboleth user attr info
        :return:
        """
        with db.session.begin_nested():
            obj = cls(
                weko_uid=weko_user.id,
                weko_user=weko_user,
                **kwargs
            )
            db.session.add(obj)
        db.session.commit()

        return obj
