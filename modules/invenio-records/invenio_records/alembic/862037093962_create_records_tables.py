# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create records tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "862037093962"
down_revision = "1095cdf9f350"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "records_metadata",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column(
            "json",
            sqlalchemy_utils.JSONType().with_variant(
                sa.dialects.postgresql.JSON(none_as_null=True),
                "postgresql",
            ),
            nullable=True,
        ),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "records_metadata_version",
        sa.Column("created", sa.DateTime(), autoincrement=False, nullable=True),
        sa.Column("updated", sa.DateTime(), autoincrement=False, nullable=True),
        sa.Column(
            "id",
            sqlalchemy_utils.types.uuid.UUIDType(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "json",
            sqlalchemy_utils.JSONType().with_variant(
                sa.dialects.postgresql.JSON(none_as_null=True),
                "postgresql",
            ),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("version_id", sa.Integer(), autoincrement=False, nullable=True),
        sa.Column(
            "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
        ),
        sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", "transaction_id"),
    )
    op.create_index(
        op.f("ix_records_metadata_version_end_transaction_id"),
        "records_metadata_version",
        ["end_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_records_metadata_version_operation_type"),
        "records_metadata_version",
        ["operation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_records_metadata_version_transaction_id"),
        "records_metadata_version",
        ["transaction_id"],
        unique=False,
    )


def downgrade():
    """Downgrade database."""
    op.drop_index(
        op.f("ix_records_metadata_version_transaction_id"),
        table_name="records_metadata_version",
    )
    op.drop_index(
        op.f("ix_records_metadata_version_operation_type"),
        table_name="records_metadata_version",
    )
    op.drop_index(
        op.f("ix_records_metadata_version_end_transaction_id"),
        table_name="records_metadata_version",
    )
    op.drop_table("records_metadata_version")
    op.drop_table("records_metadata")
