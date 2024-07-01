#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add user profile and preferences as JSON fields to the User table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType

# revision identifiers, used by Alembic.
revision = "eb9743315a9d"
down_revision = "62efc52773d4"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column(
        "accounts_user",
        sa.Column(
            "profile",
            sa.JSON()
            .with_variant(JSONType(), "mysql")
            .with_variant(
                postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
                "postgresql",
            )
            .with_variant(JSONType(), "sqlite"),
            nullable=True,
        ),
    )
    op.add_column(
        "accounts_user",
        sa.Column(
            "preferences",
            sa.JSON()
            .with_variant(JSONType(), "mysql")
            .with_variant(
                postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
                "postgresql",
            )
            .with_variant(JSONType(), "sqlite"),
            nullable=True,
        ),
    )

    # the user name is split into two columns:
    # 'displayname' which stores the original version of the username, and
    # 'username' which stores a lower-case version to ensure uniqueness
    op.add_column(
        "accounts_user",
        sa.Column("displayname", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "accounts_user",
        sa.Column("username", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        op.f("uq_accounts_user_username"), "accounts_user", ["username"]
    )


def downgrade():
    """Downgrade database."""
    op.drop_column("accounts_user", "preferences")
    op.drop_column("accounts_user", "profile")
    op.drop_constraint(
        op.f("uq_accounts_user_username"), "accounts_user", type_="unique"
    )
    op.drop_column("accounts_user", "displayname")
    op.drop_column("accounts_user", "username")
