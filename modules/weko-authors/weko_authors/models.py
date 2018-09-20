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

"""Models for weko-index-tree."""

from datetime import datetime

from flask import current_app
from invenio_db import db
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.event import listen
from weko_records.models import Timestamp
# from sqlalchemy_utils.types import UUIDType
from sqlalchemy_utils.types import JSONType, UUIDType
# from invenio_records.models import RecordMetadata


class Authors(db.Model,Timestamp):
    """
    Represent an index.

    The Index object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'authors'

    id = db.Column(db.BigInteger, primary_key=True, unique=True)
    """id of the authors."""

    gather_flg = db.Column(db.BigInteger, primary_key=False, unique=False,default=0)
    """gather_flg of the authors."""

    json = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )
    """json for author info"""


__all__ = ('Authors', )
