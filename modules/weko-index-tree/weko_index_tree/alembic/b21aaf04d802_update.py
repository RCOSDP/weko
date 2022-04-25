#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""update"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b21aaf04d802'
down_revision = '0d2fe6767b9c'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_unique_constraint(op.f('uq_index_id'), 'index', ['id'])
    

def downgrade():
    """Downgrade database."""
    op.drop_constraint(op.f('uq_index_id'), 'index', type_='unique')
    rm 