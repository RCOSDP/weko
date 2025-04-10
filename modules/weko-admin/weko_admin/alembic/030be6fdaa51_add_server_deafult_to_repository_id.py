#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add server_deafult to repository_id"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '030be6fdaa51'
down_revision = '7dc0b1ab5631'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column('feedback_email_setting', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default='Root Index')
    op.alter_column('feedback_mail_history', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default='Root Index')
    op.alter_column('stats_email_address', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default='Root Index')


def downgrade():
    """Downgrade database."""
    op.alter_column('feedback_email_setting', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default=None)
    op.alter_column('feedback_mail_history', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default=None)
    op.alter_column('stats_email_address', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default=None)

