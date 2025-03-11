#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add_column"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6cb93e7e896'
down_revision = 'ad3fd78b0175'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('journal', sa.Column('abstract', sa.Text(), nullable=True))
    op.add_column('journal', sa.Column('code_issnl', sa.Text(), nullable=True))

def downgrade():
    """Downgrade database."""
    op.drop_column('journal', 'abstract')
    op.drop_column('journal', 'code_issnl')
