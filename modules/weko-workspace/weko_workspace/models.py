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

from flask_babelex import gettext as _
from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType
from sqlalchemy_utils.models import Timestamp


class WorkspaceDefaultConditions(db.Model, Timestamp):
    """define WorkspaceDefaultConditions."""

    __tablename__ = "workspace_default_conditions"

    user_id = db.Column(db.Integer(), nullable=False, primary_key=True, index=True)
    """WorkspaceDefaultConditions identifier."""

    default_con = db.Column(
        db.JSON()
        .with_variant(
            postgresql.JSONB(none_as_null=True),
            "postgresql",
        )
        .with_variant(
            JSONType(),
            "sqlite",
        )
        .with_variant(
            JSONType(),
            "mysql",
        ),
        nullable=False,
    )
    """the name of WorkspaceDefaultConditions."""


class WorkspaceStatusManagement(db.Model, Timestamp):
    """define WorkspaceStatusManagement."""

    __tablename__ = "workspace_status_management"

    user_id = db.Column(db.Integer(), nullable=False, primary_key=True, index=True)
    """WorkspaceStatusManagement first identifier."""

    recid = db.Column(db.Integer(), nullable=False, primary_key=True, index=True)
    """WorkspaceStatusManagement second identifier."""

    is_favorited = db.Column(
        db.Boolean(name="is_favorited"), nullable=False, default=False
    )
    """is_favorited of WorkspaceStatusManagement."""

    is_read = db.Column(db.Boolean(name="is_read"), nullable=False, default=False)
    """is_read of WorkspaceStatusManagement."""
