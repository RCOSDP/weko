# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Workflow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Add columns for deleting items."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a560202ff0ac"
down_revision = "841860bb1333"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    with op.batch_alter_table("workflow_flow_define") as batch_op:
        # Step 1: Add column as nullable
        batch_op.add_column(
            sa.Column("flow_type", sa.SmallInteger(), nullable=True)
        )
    # Step 2: Set default value for existing records
    op.execute("UPDATE workflow_flow_define SET flow_type = 1")
    # Step 3: Alter column to be NOT NULL
    with op.batch_alter_table("workflow_flow_define") as batch_op:
        batch_op.alter_column("flow_type", nullable=False)

    with op.batch_alter_table("workflow_workflow") as batch_op:
        batch_op.add_column(
            sa.Column("delete_flow_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_workflow_workflow_delete_flow_id_workflow_flow_define",
            "workflow_flow_define",
            ["delete_flow_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    """Downgrade database."""
    with op.batch_alter_table("workflow_workflow") as batch_op:
        batch_op.drop_constraint(
            "fk_workflow_workflow_delete_flow_id_workflow_flow_define",
            type_="foreignkey"
        )
        batch_op.drop_column("delete_flow_id")

    with op.batch_alter_table("workflow_flow_define") as batch_op:
        batch_op.drop_column("flow_type")
