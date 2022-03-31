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
revision = '5872b2d73941'
down_revision = '4aadad0a1ff7'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_unique_constraint(op.f('uq_authors_id'), 'authors', ['id'])
    op.create_unique_constraint(op.f('uq_authors_prefix_settings_id'), 'authors_prefix_settings', ['id'])


def downgrade():
    """Downgrade database."""
    op.drop_constraint(op.f('uq_authors_prefix_settings_id'), 'authors_prefix_settings', type_='unique')
    op.drop_constraint(op.f('uq_authors_id'), 'authors', type_='unique')
