# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create transaction table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.schema import Sequence, CreateSequence, \
    DropSequence

# revision identifiers, used by Alembic.
revision = 'dbdbc1b19cf2'
down_revision = '96e796392533'
branch_labels = ()
depends_on = None


def upgrade():
    """Update database."""
    op.create_table(
        'transaction',
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('remote_addr', sa.String(length=50), nullable=True),
    )
    op.create_primary_key('pk_transaction', 'transaction', ['id'])
    if op._proxy.migration_context.dialect.supports_sequences:
        op.execute(CreateSequence(Sequence('transaction_id_seq')))


def downgrade():
    """Downgrade database."""
    op.drop_table('transaction')
    if op._proxy.migration_context.dialect.supports_sequences:
        op.execute(DropSequence(Sequence('transaction_id_seq')))
