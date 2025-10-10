# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add oa_status table."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e3b07ec6e628'
down_revision = '89c58783bf65'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "oa_status",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("oa_article_id", sa.Integer(), nullable=False),
        sa.Column("oa_status", sa.Text(), nullable=True),
        sa.Column("weko_item_pid", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("oa_article_id")
    )

def downgrade():
    """Downgrade database."""
    op.drop_table("oa_status")
