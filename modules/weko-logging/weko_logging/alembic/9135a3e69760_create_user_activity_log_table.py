#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create user activity log table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql
from sqlalchemy.schema import Sequence, CreateSequence, DropSequence
from sqlalchemy_utils import JSONType

# revision identifiers, used by Alembic.
revision = '9135a3e69760'
down_revision = 'f97e5ecfc4ec'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        'user_activity_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.DateTime().with_variant(
                mysql.DATETIME(fsp=6),
                'mysql'
            ), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('community_id', sa.String(100), nullable=True),
        sa.Column('log_group_id', sa.Integer(), nullable=True),
        sa.Column("log", sa.JSON().with_variant(
                postgresql.JSONB(none_as_null=True),
                'postgresql',
            ).with_variant(
                JSONType(),
                'sqlite',
            ).with_variant(
                JSONType(),
                'mysql',
            ), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['accounts_user.id'],
            name='fk_user_activity_active_user_id',
        ),
        sa.ForeignKeyConstraint(
            ["community_id"], ["communities_community.id"],
            name="fk_user_activity_community_id",
        ),
    )
    
    # create sequence "user_activity_log_group_id_seq"
    op.execute(
        CreateSequence(Sequence("user_activity_log_group_id_seq"))
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("user_activity_log")
    # drop sequence "user_activity_log_group_id_seq"
    op.execute(
        DropSequence(Sequence("user_activity_log_group_id_seq"))
    )
