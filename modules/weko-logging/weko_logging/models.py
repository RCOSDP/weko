# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""User activity log model."""

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy_utils.types import JSONType

from invenio_accounts.models import User
from invenio_communities.models import Community
from invenio_db import db

class UserActivityLog(db.Model):
    """User activity log model."""

    __tablename__ = 'user_activity_logs'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Unique identifier for the log entry."""

    date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'),
        nullable=False,
        default=datetime.now(timezone.utc)
    )
    """Date and time of the log entry."""

    user_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            User.id,
            name='fk_user_activity_active_user_id',
            ondelete='SET NULL'
        ),
        nullable=True
    )
    """User ID of the user who performed the action."""

    community_id = db.Column(
        db.String(100),
        db.ForeignKey(
            Community.id,
            name='fk_user_activity_community_id',
            ondelete='SET NULL'
        ),
        nullable=True
    )
    """Community ID of the community where the action was performed."""

    parent_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'user_activity_logs.id',
            name='fk_user_activity_parent_id',
            ondelete='SET NULL'
        ),
        nullable=True
    )
    """Parent ID of the log entry."""

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
            'parent_id': self.parent_id if self.parent_id else "",
            'log': self.log,
            'remarks': self.remarks
        }

    @classmethod
    def get_sequence(cls, session):
        """Get the next sequence for the user activity logs.

        Args:
            session: The database session.

        Returns:
            int: The next sequence.
        """
        if not session:
            session = db.session
        # Get the current value of the sequence
        result = session.execute(text("SELECT last_value FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'user_activity_logs_id_seq'"))
        current_id = result.scalar()
        return current_id + 1
