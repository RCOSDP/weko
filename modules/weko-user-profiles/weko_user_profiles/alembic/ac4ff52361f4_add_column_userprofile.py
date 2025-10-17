#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add_column_userprofile"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac4ff52361f4'
down_revision = 'c4d16e640acc'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('userprofiles_userprofile', sa.Column('s3_endpoint_url', sa.String(length=128), nullable=True))
    op.add_column('userprofiles_userprofile', sa.Column('s3_region_name', sa.String(length=128), nullable=True))
    op.add_column('userprofiles_userprofile', sa.Column('access_key', sa.String(length=128), nullable=True))
    op.add_column('userprofiles_userprofile', sa.Column('secret_key', sa.String(length=128), nullable=True))

def downgrade():
    """Downgrade database."""
    op.drop_column('userprofiles_userprofile', 's3_endpoint_url')
    op.drop_column('userprofiles_userprofile', 's3_region_name')
    op.drop_column('userprofiles_userprofile', 'access_key')
    op.drop_column('userprofiles_userprofile', 'secret_key')
