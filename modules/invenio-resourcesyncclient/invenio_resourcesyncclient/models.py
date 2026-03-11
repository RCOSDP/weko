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

"""Database models for invenio-resourcesyncclient."""

from datetime import datetime

from flask import current_app
from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import Timestamp
from sqlalchemy_utils.types import JSONType
from weko_index_tree.models import Index


class ResyncIndexes(db.Model, Timestamp):
    """ResyncIndexes model.

    Stores session life_time created for Session.
    """

    __tablename__ = 'resync_indexes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Identifier of resource list."""

    status = db.Column(
        db.String(),
        nullable=False,
        default=lambda: current_app.config[
            'INVENIO_RESYNC_INDEXES_STATUS'
        ].get('automatic')
    )
    """Status of resource list."""

    index_id = db.Column(
        db.BigInteger,
        db.ForeignKey(Index.id,
                      ondelete='CASCADE'),
        nullable=True
    )
    """Index Identifier relation to resync indexes."""

    repository_name = db.Column(
        db.String(50),
        nullable=False
    )
    """Repository name."""

    from_date = db.Column(
        db.DateTime,
        nullable=True
    )
    """From Date."""

    to_date = db.Column(
        db.DateTime,
        nullable=True
    )
    """To Date."""

    resync_save_dir = db.Column(
        db.String(4096),
        nullable=False
    )
    """Path directory save."""

    resync_mode = db.Column(
        db.String(20),
        nullable=False,
        default=lambda: current_app.config[
            'INVENIO_RESYNC_INDEXES_MODE'
        ].get('baseline')
    )
    """Resync mode."""

    saving_format = db.Column(
        db.String(20),
        nullable=False,
        default=lambda: current_app.config[
            'INVENIO_RESYNC_INDEXES_SAVING_FORMAT'
        ].get('jpcoar')
    )
    """Saving format."""

    base_url = db.Column(
        db.String(255), nullable=False)
    """base url of resync."""

    is_running = db.Column(
        db.Boolean(name='is_running'), default=True)
    """is running."""

    interval_by_day = db.Column(db.Integer, nullable=False)
    """Time cycle for each change list."""

    task_id = db.Column(db.String(40), default=None)

    result = db.Column(
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

    index = db.relationship(
        Index, backref='resync_index_id', foreign_keys=[index_id])
    """Relation to the Index Identifier."""


class ResyncLogs(db.Model, Timestamp):
    """Harvest Logs."""

    __tablename__ = "resync_logs"

    id = db.Column(db.Integer, primary_key=True)

    resync_indexes_id = db.Column(
        db.Integer,
        db.ForeignKey(ResyncIndexes.id,
                      ondelete='CASCADE'),
        nullable=True
    )
    log_type = db.Column(db.String(10))

    task_id = db.Column(db.String(40), default=None)

    start_time = db.Column(db.DateTime, default=datetime.now())

    end_time = db.Column(db.DateTime, nullable=True)

    status = db.Column(db.String(10), nullable=False, default='Running')

    errmsg = db.Column(db.String(255), nullable=True, default=None)

    counter = db.Column(
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

    resync_index = db.relationship(
        ResyncIndexes,
        backref='resync_indexes_id',
        foreign_keys=[resync_indexes_id])
    """Relation to the Resync Identifier."""


__all__ = ('ResyncIndexes',
           'ResyncLogs'
           )
