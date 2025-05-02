# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

import traceback
from flask import current_app
from sqlalchemy_utils import Timestamp
from sqlalchemy.exc import SQLAlchemyError

from invenio_accounts.models import User
from invenio_db import db

from weko_user_profiles.models import UserProfile

class NotificationsUserSettings(db.Model, Timestamp):
    """User notifications settings.

    Columns:
        `user_id` (int): ID of the settings. Primary key, foreign key
            referencing `User.id`.
        `subscribe_email` (bool): Email notification subscription status.
    Relationship:
        `user` (User): Foreign key relationship to `User`.
        `user_profile` (UserProfile): Foreign key relationship to `UserProfile`.
    """

    __tablename__ = 'notifications_user_settings'

    """ID of the settings."""

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id, ondelete="CASCADE"),
        primary_key=True
    )
    """Foreign key to :class:`~invenio_accounts.models.User`."""

    user = db.relationship(
        User, backref=db.backref(
            'notifications_settings',
            uselist=False, cascade='all, delete-orphan'
        )
    )
    """User relationship."""

    user_profile_id = db.Column(
        db.Integer,
        db.ForeignKey(UserProfile.user_id),
        nullable=True
    )
    """Foreign key to :class:`~weko_user_profiles.models.UserProfile`."""


    user_profile = db.relationship(
        UserProfile, backref=db.backref(
            'notifications_settings',
            uselist=False, cascade='all, delete-orphan'
        )
    )
    """User profile relationship."""

    subscribe_email = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    """Email notification subscription status."""

    @classmethod
    def get_by_user_id(cls, user_id):
        """Retrieve settings by user ID.

        Args:
            user_id (int): User ID.
        Returns:
            NotificationsUserSettings: Settings.
        """
        return cls.query.filter_by(user_id=user_id).one_or_none()

    @classmethod
    def create_or_update(
        cls, user_id, subscribe_email=None
    ):
        """Create or update settings.

        Args:
            user_id (int): User ID.
            subscribe_webpush (bool): Web push notification subscription status.
            subscribe_email (bool): Email notification subscription status.
        Returns:
            NotificationsUserSettings: Settings.
        """
        settings = cls.get_by_user_id(user_id)
        if settings is None:
            settings = cls(user_id=user_id)
        if subscribe_email is not None:
            settings.subscribe_email = subscribe_email

        try:
            with db.session.begin_nested():
                db.session.add(settings)
            db.session.commit()
        except SQLAlchemyError:
            current_app.logger.error(
                f"Error creating/updating notifications settings. user_id={user_id}"
            )
            traceback.print_exc()
            db.session.rollback()
            raise

        return settings
