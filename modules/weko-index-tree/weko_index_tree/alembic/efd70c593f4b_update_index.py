#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""update index"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'efd70c593f4b'
down_revision = 'b21aaf04d802'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('index', sa.Column('index_url', sa.Text(), nullable=True))
    op.add_column('index', sa.Column('cnri', sa.Text(), nullable=True))

def downgrade():
    """Downgrade database."""
    op.drop_column('index', 'index_url')
    op.drop_column('index', 'cnri')
