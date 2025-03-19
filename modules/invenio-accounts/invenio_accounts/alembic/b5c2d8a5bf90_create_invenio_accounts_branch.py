#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create invenio_accounts branch"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5c2d8a5bf90'
down_revision = 'e12419831262'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    with op.batch_alter_table('accounts_user_session_activity') as batch_op:
        batch_op.add_column(
            sa.Column('orgniazation_name', sa.String(255), nullable=True)
        )


def downgrade():
    """Downgrade database."""
    with op.batch_alter_table('accounts_user_session_activity') as batch_op:
        batch_op.drop_column('orgniazation_name')
