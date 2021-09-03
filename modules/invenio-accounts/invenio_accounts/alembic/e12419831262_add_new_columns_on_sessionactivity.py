# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add new columns on SessionActivity."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e12419831262'
down_revision = '9848d0149abd'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    with op.batch_alter_table('accounts_user_session_activity') as batch_op:
        batch_op.add_column(sa.Column('browser', sa.String(80), nullable=True))
        batch_op.add_column(
            sa.Column('browser_version', sa.String(30), nullable=True))
        batch_op.add_column(
            sa.Column('country', sa.String(3), nullable=True))
        batch_op.add_column(
            sa.Column('device', sa.String(80), nullable=True))
        batch_op.add_column(
            sa.Column('ip', sa.String(80), nullable=True))
        batch_op.add_column(
            sa.Column('os', sa.String(80), nullable=True))


def downgrade():
    """Downgrade database."""
    with op.batch_alter_table('accounts_user_session_activity') as batch_op:
        batch_op.drop_column('os')
        batch_op.drop_column('ip')
        batch_op.drop_column('device')
        batch_op.drop_column('country')
        batch_op.drop_column('browser_version')
        batch_op.drop_column('browser')
