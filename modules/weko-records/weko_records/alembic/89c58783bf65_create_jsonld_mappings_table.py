# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create jsonld_mapping table."""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType

# revision identifiers, used by Alembic.
revision = "89c58783bf65"
down_revision = "1a120f8b96a7"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "jsonld_mappings",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "mapping",
            sa.JSON().with_variant(
                postgresql.JSONB(none_as_null=False),
                "postgresql",
            ).with_variant(
                JSONType(),
                "sqlite",
            ).with_variant(
                JSONType(),
                "mysql",
            ),
            nullable=False
        ),
        sa.Column("item_type_id", sa.Integer(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.Column(
            "is_deleted", sa.Boolean(name="is_deleted"),
            nullable=False, default=False
        ),
        sa.ForeignKeyConstraint(
            ["item_type_id"], ["item_type.id"],
            name="fk_jsonld_mappings_item_type_id_item_type",
        ),
        sa.PrimaryKeyConstraint("id")
    )

    op.create_table(
        "jsonld_mappings_version",
        sa.Column("created", sa.DateTime()),
        sa.Column("updated", sa.DateTime()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255)),
        sa.Column(
            "mapping",
            sa.JSON().with_variant(
                postgresql.JSONB(none_as_null=True),
                "postgresql",
            ).with_variant(
                JSONType(),
                "sqlite",
            ).with_variant(
                JSONType(),
                "mysql",
            ),
            default=lambda: {}
        ),
        sa.Column("item_type_id", sa.Integer()),
        sa.Column("version_id", sa.Integer()),
        sa.Column("is_deleted", sa.Boolean(name="is_deleted")),
        sa.Column("transaction_id", sa.BigInteger(), nullable=False),
        sa.Column("end_transaction_id", sa.BigInteger()),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", "transaction_id"),
    )
    op.create_index(
        op.f("ix_jsonld_mappings_version_transaction_id"),
        "jsonld_mappings_version",
        ["transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jsonld_mappings_version_operation_type"),
        "jsonld_mappings_version",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_jsonld_mappings_version_end_transaction_id"),
        "jsonld_mappings_version",
        ["end_transaction_id"],
        unique=False,
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("jsonld_mappings")
    op.drop_table("jsonld_mappings_version")
