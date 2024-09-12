# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create community tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = '2d9884d0e3fa'
down_revision = '21e13cb1eff2'
branch_labels = None
depends_on = ('9848d0149abd', '862037093962')


def upgrade():
    """Upgrade database."""
    op.create_table(
        'communities_community',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('id_user', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('page', sa.Text(), nullable=False),
        sa.Column('curation_policy', sa.Text(), nullable=False),
        sa.Column('last_record_accepted', sa.DateTime(), nullable=False),
        sa.Column('logo_ext', sa.String(length=4), nullable=True),
        sa.Column('ranking', sa.Integer(), nullable=False),
        sa.Column('fixed_points', sa.Integer(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_user'], [u'accounts_user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'communities_community_record',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id_community', sa.String(length=100), nullable=False),
        sa.Column('id_record', sqlalchemy_utils.types.uuid.UUIDType(),
                  nullable=False),
        sa.Column('id_user', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['id_community'], ['communities_community.id'],
            name='fk_communities_community_record_id_community',
        ),
        sa.ForeignKeyConstraint(['id_record'], [u'records_metadata.id'], ),
        sa.ForeignKeyConstraint(['id_user'], [u'accounts_user.id'], ),
        sa.PrimaryKeyConstraint('id_community', 'id_record')
    )
    op.create_table(
        'communities_featured_community',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_community', sa.String(length=100), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['id_community'], [u'communities_community.id'],
            name='fk_communities_featured_community_id_community',
        ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """Downgrade database."""
    op.drop_table('communities_featured_community')
    op.drop_table('communities_community_record')
    op.drop_table('communities_community')
