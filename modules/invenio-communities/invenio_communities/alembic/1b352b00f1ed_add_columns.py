#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add columns"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b352b00f1ed'
down_revision = 'd2d56dc5e385'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('communities_community', sa.Column('content_policy', sa.Text(), nullable=True))
    op.add_column('communities_community', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('fk_communities_community_group_id_accounts_role'), 'communities_community', 'accounts_role', ['group_id'], ['id'])


def downgrade():
    """Downgrade database."""
    op.drop_constraint(op.f('fk_communities_community_group_id_accounts_role'), 'communities_community', type_='foreignkey')
    op.drop_column('communities_community', 'group_id')
    op.drop_column('communities_community', 'content_policy')
