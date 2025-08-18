#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add activity request mail"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '841860bb1333'
down_revision = '2084f52e00b7'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        'workflow_activity_request_mail',
        sa.Column('status', sa.String(1), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('activity_id', sa.String(length=24), nullable=False, index=True),
        sa.Column('display_request_button', sa.Boolean(name='display_request_button'), nullable=False, server_default='0'),
        sa.Column('request_maillist',
            sa.JSON()
                .with_variant(postgresql.JSONB(none_as_null=True), 'postgresql')
                .with_variant(sa.JSON(), 'sqlite')
                .with_variant(sa.JSON(), 'mysql'),
            nullable=True
        ),
    )

def downgrade():
    """Downgrade database."""
    op.drop_table('workflow_activity_request_mail')
