# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Create notifications_user_settings table."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9ef65066e0d3"
down_revision = "1aceb8bc87f2"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "notifications_user_settings",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("user_profile_id", sa.Integer(), nullable=True),
        sa.Column(
            "subscribe_webpush",
            sa.Boolean(name="subscribe_webpush"),
            nullable=True
        ),
        sa.Column(
            "subscribe_email",
            sa.Boolean(name="subscribe_email"),
            nullable=False
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["accounts_user.id"],
            name="fk_notifications_user_settings_user_id_accounts_user",
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_profile_id"], ["userprofiles_userprofile.user_id"],
            name="fk_notifications_user_settings_user_profile_id_userprofiles_userprofile",
        )
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("notifications_user_settings")
