# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create sword_clients table."""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType

# revision identifiers, used by Alembic.
revision = "ce82f0d78dcb"
down_revision = "05683afc0320"
branch_labels = ()
depends_on = ["invenio_oauth2server", "weko_records"]


def upgrade():
    """Upgrade database."""
    op.create_table(
        "sword_clients",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=False),
        sa.Column("registration_type_id", sa.SmallInteger(), nullable=False),
        sa.Column("mapping_id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Integer()),
        sa.Column("active", sa.Boolean(name="active")),
        sa.Column(
            "meta_data_api",
            sa.JSON().with_variant(
                postgresql.JSONB(none_as_null=True),
                'postgresql',
            ).with_variant(
                JSONType(),
                'sqlite',
            ).with_variant(
                JSONType(),
                'mysql',
            ),
            nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", name="uq_sword_clients_client_id"),
        sa.ForeignKeyConstraint(
            ["client_id"], ["oauth2server_client.client_id"],
            name="fk_sword_clients_client_id_oauth2server_client",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["mapping_id"], ["jsonld_mappings.id"],
            name="fk_sword_clients_mapping_id_jsonld_mappings",
        ),
        sa.ForeignKeyConstraint(
            ["workflow_id"], ["workflow_workflow.id"],
            name="fk_sword_clients_workflow_id_workflow_workflow",
        )
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("sword_clients")
