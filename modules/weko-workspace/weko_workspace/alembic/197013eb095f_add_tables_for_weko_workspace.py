#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add tables for weko-workspace."""

from datetime import datetime, timezone
from alembic import op
from invenio_db import db
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '197013eb095f'
down_revision = 'fa62eaff62c9'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "workspace_default_conditions",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("default_con", db.JSON().with_variant(
            sa.dialects.postgresql.JSONB(
                none_as_null=True), "postgresql",
        ), nullable=False),
        sa.PrimaryKeyConstraint("user_id")
    )
    op.create_table(
        "workspace_status_management",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("recid", sa.Integer(), nullable=False),
        sa.Column("is_favorited", sa.Boolean(name="is_favorited"), nullable=False, default=False),
        sa.Column("is_read", sa.Boolean(name="is_read"), nullable=False, default=False),
        sa.PrimaryKeyConstraint("user_id", "recid")
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("workspace_default_conditions")
    op.drop_table("workspace_status_management")
