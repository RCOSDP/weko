#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add column file readonly_keys"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'faf4faa08601'
down_revision = '8644b32a3eec'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('files_location', sa.Column('readonly_access_key', sa.String(length=128), nullable=True))
    op.add_column('files_location', sa.Column('readonly_secret_key', sa.String(length=128), nullable=True))


def downgrade():
    """Downgrade database."""
    op.drop_column('files_location', 'readonly_secret_key')
    op.drop_column('files_location', 'readonly_access_key')
