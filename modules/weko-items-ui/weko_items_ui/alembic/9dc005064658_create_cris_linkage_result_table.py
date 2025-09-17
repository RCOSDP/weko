#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create cris_linkage_result table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import sqlalchemy_utils

# revision identifiers, used by Alembic.
revision = '9dc005064658'
down_revision = 'e4fdaedc126c'
branch_labels = ()
depends_on = 'weko_records'


def upgrade():
    """Upgrade database."""
    op.create_table(
        'cris_linkage_result',
        sa.Column('recid', sa.Integer(), nullable=False),
        sa.Column('cris_institution', sa.Text(), nullable=False),
        sa.Column('last_linked_date', sa.DateTime(), nullable=True),
        sa.Column('last_linked_item', sqlalchemy_utils.types.uuid.UUIDType(),
                  nullable=True),
        sa.Column('succeed', sa.Boolean(), nullable=True),
        sa.Column('failed_log', sa.Text().with_variant(mysql.VARCHAR(255), 'mysql'),
                  nullable=False, server_default=''),
        sa.ForeignKeyConstraint(['recid'], ['pidstore_recid.recid'],
                                name='fk_cris_linkage_result_recid_pidstore_recid'),
        sa.ForeignKeyConstraint(['last_linked_item'], ['item_metadata.id'],
                                name='fk_cris_linkage_result_last_linked_item_item_metadata'),
        sa.PrimaryKeyConstraint('recid', 'cris_institution'),
    )


def downgrade():
    """Downgrade database."""
    op.drop_table('cris_linkage_result')
