#
# This file is part of Invenio.
# Copyright (C) 2016-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create tables for domain list feature."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import JSONType

# revision identifiers, used by Alembic.
revision = "6ec5ce377ca3"
down_revision = "037afe10e9ff"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "accounts_domain_category",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts_domain_category")),
    )
    op.create_table(
        "accounts_domain_org",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pid", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "json",
            sa.JSON()
            .with_variant(JSONType(), "mysql")
            .with_variant(
                postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), "postgresql"
            )
            .with_variant(JSONType(), "sqlite"),
            nullable=False,
        ),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["accounts_domain_org.id"],
            name=op.f("fk_accounts_domain_org_parent_id_accounts_domain_org"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts_domain_org")),
        sa.UniqueConstraint("pid", name=op.f("uq_accounts_domain_org_pid")),
    )
    op.create_table(
        "accounts_domains",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("tld", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=False),
        sa.Column("flagged_source", sa.String(length=255), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.Integer(), nullable=True),
        sa.Column("num_users", sa.Integer(), nullable=False),
        sa.Column("num_active", sa.Integer(), nullable=False),
        sa.Column("num_inactive", sa.Integer(), nullable=False),
        sa.Column("num_confirmed", sa.Integer(), nullable=False),
        sa.Column("num_verified", sa.Integer(), nullable=False),
        sa.Column("num_blocked", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category"],
            ["accounts_domain_category.id"],
            name=op.f("fk_accounts_domains_category_accounts_domain_category"),
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["accounts_domain_org.id"],
            name=op.f("fk_accounts_domains_org_id_accounts_domain_org"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts_domains")),
        sa.UniqueConstraint("domain", name=op.f("uq_accounts_domains_domain")),
    )
    op.add_column(
        "accounts_user", sa.Column("domain", sa.String(length=255), nullable=True)
    )


def downgrade():
    """Downgrade database."""
    op.drop_column("accounts_user", "domain")
    op.drop_table("accounts_domains")
    op.drop_table("accounts_domain_org")
    op.drop_table("accounts_domain_category")
