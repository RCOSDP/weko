#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add columns"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7dc0b1ab5631'
down_revision = 'b4d2f3c0734b'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('feedback_email_setting', sa.Column('repository_id', sa.String(length=100), nullable=False, server_default='Root Index'))
    op.add_column('feedback_mail_history', sa.Column('repository_id', sa.String(length=100), nullable=False, server_default='Root Index'))
    op.add_column('stats_email_address', sa.Column('repository_id', sa.String(length=100), nullable=True, server_default='Root Index'))


def downgrade():
    """Downgrade database."""
    op.drop_column('stats_email_address', 'repository_id')
    op.drop_column('feedback_mail_history', 'repository_id')
    op.drop_column('feedback_email_setting', 'repository_id')

