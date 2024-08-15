#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add versioning information to models."""

from alembic import op
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "999dcbd19ace"
down_revision = "e12419831262"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    role_tbl = "accounts_role"
    user_tbl = "accounts_user"

    # create the new columns as nullable fields
    op.add_column(role_tbl, Column("created", DateTime(), nullable=True))
    op.add_column(role_tbl, Column("updated", DateTime(), nullable=True))
    op.add_column(role_tbl, Column("version_id", Integer(), nullable=True))
    op.add_column(user_tbl, Column("created", DateTime(), nullable=True))
    op.add_column(user_tbl, Column("updated", DateTime(), nullable=True))
    op.add_column(user_tbl, Column("version_id", Integer(), nullable=True))

    # populate the columns of existing rows
    op.execute(
        text(
            "UPDATE accounts_role SET created = CURRENT_TIMESTAMP, updated = CURRENT_TIMESTAMP, version_id = 1;"
        )
    )  # noqa
    op.execute(
        text(
            "UPDATE accounts_user SET created = CURRENT_TIMESTAMP, updated = CURRENT_TIMESTAMP, version_id = 1;"
        )
    )  # noqa

    # make the columns not nullable
    dt_args = {"existing_type": DateTime(), "nullable": False}
    int_args = {"existing_type": Integer(), "nullable": False}
    op.alter_column(role_tbl, "created", **dt_args)
    op.alter_column(role_tbl, "updated", **dt_args)
    op.alter_column(role_tbl, "version_id", **int_args)
    op.alter_column(user_tbl, "created", **dt_args)
    op.alter_column(user_tbl, "updated", **dt_args)
    op.alter_column(user_tbl, "version_id", **int_args)


def downgrade():
    """Downgrade database."""
    op.drop_column("accounts_user", "version_id")
    op.drop_column("accounts_user", "updated")
    op.drop_column("accounts_user", "created")

    op.drop_column("accounts_role", "version_id")
    op.drop_column("accounts_role", "updated")
    op.drop_column("accounts_role", "created")
