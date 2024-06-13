# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create oiaserver tables."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e655021de0de"
down_revision = "759d47cbdba7"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "oaiserver_set",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("spec", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("search_pattern", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("spec"),
    )
    op.create_index(
        op.f("ix_oaiserver_set_name"), "oaiserver_set", ["name"], unique=False
    )


def downgrade():
    """Downgrade database."""
    op.drop_index(op.f("ix_oaiserver_set_name"), table_name="oaiserver_set")
    op.drop_table("oaiserver_set")
