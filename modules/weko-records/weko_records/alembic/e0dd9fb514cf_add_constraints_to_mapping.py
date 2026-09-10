# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add constraints to mapping"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0dd9fb514cf'
down_revision = '32ecd938a01b'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    with op.batch_alter_table('item_type_mapping') as batch_op:
        batch_op.create_unique_constraint(
            'uq_item_type_mapping_item_type_id', ['item_type_id']
        )
        batch_op.create_foreign_key(
            'fk_item_type_mapping_item_type_id_item_type',
            'item_type', ['item_type_id'], ['id'],
            ondelete="CASCADE"
        )

    # Drop indexes from DDL.
    op.execute("DROP INDEX IF EXISTS idx_created_item_type_mapping")
    op.execute("DROP INDEX IF EXISTS idx_item_type_id_item_type_mapping")



def downgrade():
    """Downgrade database."""
    with op.batch_alter_table('item_type_mapping') as batch_op:
        batch_op.drop_constraint(
            'fk_item_type_mapping_item_type_id_item_type', type_='foreignkey'
        )
        batch_op.drop_constraint(
            'uq_item_type_mapping_item_type_id', type_='unique'
        )

    # Recreate indexes from DDL.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_item_type_mapping
        ON item_type_mapping USING BTREE (created)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_item_type_id_item_type_mapping
        ON item_type_mapping USING BTREE (item_type_id)
    """)
