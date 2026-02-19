# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""User activity log model."""

from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from sqlalchemy import Sequence, event
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy_utils.types import JSONType
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.ddl import DDL

from invenio_accounts.models import User
from invenio_communities.models import Community
from invenio_db import db

group_id_seq = Sequence('user_activity_log_group_id_seq', metadata=db.metadata)

class _UserActivityLogBase:
    """User activity log model."""

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Unique identifier for the log entry."""

    date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        primary_key=True
    )
    """Date and time of the log entry."""

    @declared_attr
    def user_id(cls):
        return db.Column(
            db.Integer(),
            db.ForeignKey(
                User.id,
                name='fk_user_activity_active_user_id',
                ondelete='SET NULL'
            ),
            nullable=True
        )
    """User ID of the user who performed the action."""

    @declared_attr
    def community_id(cls):
        return db.Column(
            db.String(100),
            db.ForeignKey(
                Community.id,
                name='fk_user_activity_community_id',
                ondelete='SET NULL'
            ),
            nullable=True
        )
    """Community ID of the community where the action was performed."""

    log_group_id = db.Column(
        db.Integer(),
        nullable=True
    )
    """Log group ID for grouping related log entries."""

    log = db.Column(
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
        nullable=False
    )
    """Log entry."""

    remarks = db.Column(
        db.Text(),
        nullable=True
    )
    """Remarks for the log entry."""

    def to_dict(self):
        """Serialize object to dictionary.

        Returns:
            dict: Dictionary representation of the object.
        """
        return {
            'id': self.id,
            'date': self.date,
            'user_id': self.user_id if self.user_id else "",
            'community_id': self.community_id if self.community_id else "",
            "log_group_id": self.log_group_id if self.log_group_id else "",
            'log': self.log,
            'remarks': self.remarks
        }

    @classmethod
    def get_log_group_sequence(cls, session):
        """Get the next sequence for user activity log group.

        Args:
            session: The database session.

        Returns:
            int: The next sequence.
        """
        if not session:
            session = db.session
        next_id = session.execute(group_id_seq)
        return next_id

class UserActivityLog(db.Model,_UserActivityLogBase):
    """User activity log model."""

    __tablename__ = 'user_activity_logs'
    __table_args__ = (
        db.UniqueConstraint('date', name='uq_date'),
        { "postgresql_partition_by": 'RANGE (date)' }
    )

def get_user_activity_logs_partition_tables():
    """Get the partition table for the user_activity_logs table

    Returns:
        list: List of partition table names.
    """
    
    query = "select tablename from pg_tables where tablename like 'user_activity_logs_partition_%'"
    tables = db.session.execute(query).fetchall()

    return [a[0] for a in tables]

def make_user_activity_logs_partition_table(year, month):
    """Create a new partition table for user_activity_logs for a specific year and month.

    Args:
        year (int): The year for the partition.
        month (int): The month for the partition.
    Returns:
        str: The name of the created partition table.
    """
    start_date = datetime(year, month, 1, 0, 0, 0)
    end_date = start_date + relativedelta(months=1)
    suffix = '_' + start_date.strftime('%Y%m')
    tablename = UserActivityLog.__tablename__ + suffix

    NewPartitionTable = type('UserActivityLogPartition' + suffix,
                             (db.Model,_UserActivityLogBase),
                             {"__tablename__": tablename})
    NewPartitionTable.__table__.add_is_dependent_on(UserActivityLog.__table__)

    alter_table = \
        "ALTER TABLE " + UserActivityLog.__tablename__ + " ATTACH PARTITION " + \
        tablename + \
        " FOR VALUES FROM ('{}') TO ('{}');".format(start_date.strftime('%Y-%m-%d'),
                                                    end_date.strftime('%Y-%m-%d'))

    event.listen(NewPartitionTable.__table__,
                 "after_create",
                 DDL(alter_table))

    return tablename
