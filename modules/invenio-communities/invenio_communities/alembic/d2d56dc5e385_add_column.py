#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add_column"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'd2d56dc5e385'
down_revision = '2d9884d0e3fa'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('communities_community', sa.Column('thumbnail_path', sa.Text(), nullable=True))
    op.add_column('communities_community', sa.Column('login_menu_enabled', sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()))
    op.add_column('communities_community', sa.Column('catalog_json', JSONB, nullable=True))
    op.add_column('communities_community', sa.Column('cnri', sa.Text(), nullable=True))


def downgrade():
    """Downgrade database."""
    op.drop_column('communities_community', 'thumbnail_path')
    op.drop_column('communities_community', 'login_menu_enabled')
    op.drop_column('communities_community', 'catalog_json')
    op.drop_column('communities_community', 'cnri')
