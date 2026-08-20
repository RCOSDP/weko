#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add doi deposit log"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1c7d3f9a204'
down_revision = 'f312b8c2839a'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        'doi_deposit_log',
        sa.Column('status', sa.String(1), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.BigInteger(), primary_key=True,
                  autoincrement=True, nullable=False),
        sa.Column('item_uuid', sa.String(length=36), nullable=False),
        sa.Column('agency', sa.String(length=32), nullable=False),
        sa.Column('doi_select', sa.String(length=2), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=False),
        sa.Column('resource_url', sa.Text(), nullable=True),
        sa.Column('record_type', sa.String(length=50), nullable=True),
        sa.Column('tracking_id', sa.String(length=255), nullable=True),
        sa.Column('deposit_status', sa.String(length=16), nullable=False,
                  server_default='pending'),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('poll_attempt', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('http_status', sa.SmallInteger(), nullable=True),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index(op.f('ix_doi_deposit_log_item_uuid'),
                    'doi_deposit_log', ['item_uuid'], unique=False)
    op.create_index(op.f('ix_doi_deposit_log_agency'),
                    'doi_deposit_log', ['agency'], unique=False)
    op.create_index(op.f('ix_doi_deposit_log_doi'),
                    'doi_deposit_log', ['doi'], unique=False)
    op.create_index(op.f('ix_doi_deposit_log_tracking_id'),
                    'doi_deposit_log', ['tracking_id'], unique=False)
    op.create_index(op.f('ix_doi_deposit_log_deposit_status'),
                    'doi_deposit_log', ['deposit_status'], unique=False)


def downgrade():
    """Downgrade database."""
    op.drop_index(op.f('ix_doi_deposit_log_deposit_status'),
                  table_name='doi_deposit_log')
    op.drop_index(op.f('ix_doi_deposit_log_tracking_id'),
                  table_name='doi_deposit_log')
    op.drop_index(op.f('ix_doi_deposit_log_doi'),
                  table_name='doi_deposit_log')
    op.drop_index(op.f('ix_doi_deposit_log_agency'),
                  table_name='doi_deposit_log')
    op.drop_index(op.f('ix_doi_deposit_log_item_uuid'),
                  table_name='doi_deposit_log')
    op.drop_table('doi_deposit_log')
