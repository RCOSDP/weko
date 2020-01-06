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

"""Database models for invenio-resourcesyncserver."""

from datetime import datetime

from sqlalchemy_utils import Timestamp
from invenio_db import db
from sqlalchemy import Sequence, asc
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import desc
from sqlalchemy_utils import Timestamp
from sqlalchemy_utils.types import JSONType


class ResourceListIndexes(db.Model, Timestamp):
    """ResourceListIndexes model.

    Stores session life_time create_date for Session.
    """

    __tablename__ = 'resourcelist_indexes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    status = db.Column(
        db.Boolean(),
        nullable=False,
        default=True
    )

    repository = db.Column(
        db.String(255), nullable=True, unique=True, index=True)

    resource_dump_manifest = db.Column(
        db.Boolean(),
        nullable=False,
        default=True
    )

    url_path = db.Column(
        db.String(255), nullable=True)

    create_date = db.Column(db.DateTime, default=datetime.now)

    update_date = db.Column(db.DateTime, default=datetime.now)


__all__ = ([
    'ResourceListIndexes'
])
