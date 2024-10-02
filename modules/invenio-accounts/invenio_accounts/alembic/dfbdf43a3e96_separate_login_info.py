#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Separate login info from user table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text
from sqlalchemy_utils.types.ip_address import IPAddressType

# revision identifiers, used by Alembic.
revision = "dfbdf43a3e96"
down_revision = "999dcbd19ace"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # create the new login information table
    op.create_table(
        "accounts_user_login_information",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("current_login_at", sa.DateTime(), nullable=True),
        sa.Column("current_login_ip", IPAddressType(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_ip", IPAddressType(), nullable=True),
        sa.Column("login_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["accounts_user.id"],
            name="fk_accounts_login_information_user_id",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", name=op.f("pk_accounts_user_login_information")
        ),
    )

    # move information from the user table into the new table
    op.execute(
        text(
            "INSERT INTO accounts_user_login_information "
            "(user_id, current_login_at, current_login_ip, last_login_at, last_login_ip, login_count) "  # noqa
            "SELECT id, current_login_at, current_login_ip, last_login_at, last_login_ip, login_count "  # noqa
            "FROM accounts_user;"
        )
    )

    # remove columns from the user table
    op.drop_column("accounts_user", "login_count")
    op.drop_column("accounts_user", "last_login_at")
    op.drop_column("accounts_user", "current_login_ip")
    op.drop_column("accounts_user", "last_login_ip")
    op.drop_column("accounts_user", "current_login_at")


def downgrade():
    """Downgrade database."""
    # create the old columns on the user table
    op.add_column(
        "accounts_user",
        sa.Column("current_login_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "accounts_user",
        sa.Column("current_login_ip", IPAddressType(), nullable=True),
    )
    op.add_column(
        "accounts_user",
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "accounts_user",
        sa.Column("last_login_ip", IPAddressType(), nullable=True),
    )
    op.add_column(
        "accounts_user",
        sa.Column("login_count", sa.Integer(), nullable=True),
    )

    # move the data from the new table to the old columns
    # (at least with postgres)
    dialect_name = op._proxy.migration_context.dialect.name
    if dialect_name == "postgresql":
        op.execute(
            text(
                "UPDATE accounts_user SET "
                " current_login_at = li.current_login_at, "
                " current_login_ip = li.current_login_ip, "
                " last_login_at = li.last_login_at, "
                " last_login_ip = li.last_login_ip, "
                " login_count = li.login_count "
                "FROM accounts_user_login_information AS li "
                "WHERE accounts_user.id = li.user_id;"
            )
        )

    # drop the new table
    op.drop_table("accounts_user_login_information")
