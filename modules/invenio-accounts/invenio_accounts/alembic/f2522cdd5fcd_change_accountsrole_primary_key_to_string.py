#
# This file is part of Invenio.
# Copyright (C) 2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Change AccountsRole primary key to string."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text
from sqlalchemy_utils import get_referencing_foreign_keys

from invenio_accounts.models import Role

# revision identifiers, used by Alembic.
revision = "f2522cdd5fcd"
down_revision = "eb9743315a9d"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Drop primary key and all foreign keys
    ctx = op.get_context()
    if ctx.connection.engine.name == "mysql":
        # mysql does not support CASCADE on drop constraint command
        dependent_tables = get_referencing_foreign_keys(Role)

        for fk in dependent_tables:
            op.drop_constraint(
                fk.constraint.name, fk.constraint.table.name, type_="foreignkey"
            )

        op.execute(text("ALTER TABLE accounts_role MODIFY COLUMN id INT"))

        op.drop_constraint("pk_accounts_role", "accounts_role", type_="primary")
    else:
        op.execute(
            text("ALTER TABLE accounts_role DROP CONSTRAINT pk_accounts_role CASCADE;")
        )

    op.alter_column(
        "accounts_userrole",
        "role_id",
        existing_type=sa.Integer,
        type_=sa.String(80),
        postgresql_using="role_id::integer",
    )
    # Change primary key type
    # server_default=None will remove the autoincrement
    op.alter_column(
        "accounts_role",
        "id",
        existing_type=sa.Integer,
        type_=sa.String(80),
        server_default=None,
    )
    op.create_primary_key("pk_accounts_role", "accounts_role", ["id"])
    # Add new column `is_managed`
    op.add_column(
        "accounts_role",
        sa.Column(
            "is_managed", sa.Boolean(name="is_managed"), default=True, nullable=True
        ),
    )
    op.execute(text("UPDATE accounts_role SET is_managed = true;"))
    op.alter_column(
        "accounts_role", "is_managed", existing_type=sa.Boolean, nullable=False
    )

    # Re-create the foreign key constraint
    op.create_foreign_key(
        "fk_accounts_userrole_role_id",
        "accounts_userrole",
        "accounts_role",
        ["role_id"],
        ["id"],
    )


def downgrade():
    """Downgrade database."""
    # Drop new column `is_managed`
    op.drop_column("accounts_role", "is_managed")
    ctx = op.get_context()
    if ctx.connection.engine.name == "mysql":
        # mysql does not support CASCADE on drop constraint command
        dependent_tables = get_referencing_foreign_keys(Role)

        for fk in dependent_tables:
            op.drop_constraint(
                fk.constraint.name, fk.constraint.table.name, type_="foreignkey"
            )

        op.drop_constraint("pk_accounts_role", "accounts_role", type_="primary")
    else:
        op.execute(
            text("ALTER TABLE accounts_role DROP CONSTRAINT pk_accounts_role CASCADE;")
        )

    op.alter_column(
        "accounts_userrole",
        "role_id",
        existing_type=sa.String(80),
        type_=sa.Integer,
        postgresql_using="role_id::integer",
    )
    # Change primary key type
    # op.drop_constraint("pk_accounts_role", "accounts_role", type_="primary")
    op.alter_column(
        "accounts_role",
        "id",
        existing_type=sa.String(80),
        type_=sa.Integer,
        postgresql_using="id::integer",
    )
    op.create_primary_key("pk_accounts_role", "accounts_role", ["id"])
    op.alter_column(
        "accounts_role",
        "id",
        existing_type=sa.String(80),
        type_=sa.Integer,
        autoincrement=True,
        existing_autoincrement=True,
        nullable=False,
    )

    # Re-create the foreign key constraint
    op.create_foreign_key(
        "fk_accounts_userrole_role_id",
        "accounts_userrole",
        "accounts_role",
        ["role_id"],
        ["id"],
    )
