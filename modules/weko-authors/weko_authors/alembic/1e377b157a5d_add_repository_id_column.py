#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add repository_id column"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import JSONType

# revision identifiers, used by Alembic.
revision = '1e377b157a5d'
down_revision = 'e471f74f4f27'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('authors',
        sa.Column(
            'repository_id',
            sa.JSON().with_variant(
                postgresql.JSONB(none_as_null=True),
                'postgresql',
            ).with_variant(
                JSONType(),
                'sqlite',
            ).with_variant(
                JSONType(),
                'mysql',
            ),
            nullable=True
        )
    )
    op.add_column('authors_affiliation_settings',
        sa.Column(
            'repository_id',
            sa.JSON().with_variant(
                postgresql.JSONB(none_as_null=True),
                'postgresql',
            ).with_variant(
                JSONType(),
                'sqlite',
            ).with_variant(
                JSONType(),
                'mysql',
            ),
            nullable=True
        )
    )
    op.add_column('authors_prefix_settings',
        sa.Column(
            'repository_id',
            sa.JSON().with_variant(
                postgresql.JSONB(none_as_null=True),
                'postgresql',
            ).with_variant(
                JSONType(),
                'sqlite',
            ).with_variant(
                JSONType(),
                'mysql',
            ),
            nullable=True
        )
    )


def downgrade():
    """Downgrade database."""
    op.drop_column('authors_prefix_settings', 'repository_id')
    op.drop_column('authors_affiliation_settings', 'repository_id')
    op.drop_column('authors', 'repository_id')
    