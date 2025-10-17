#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add_column_files_location"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8644b32a3eec'
down_revision = '8ae99b034410'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('files_location', sa.Column('s3_default_block_size', sa.BigInteger(), nullable=True))
    op.add_column('files_location', sa.Column('s3_maximum_number_of_parts', sa.BigInteger(), nullable=True))
    op.add_column('files_location', sa.Column('s3_region_name', sa.String(length=128), nullable=True))
    op.add_column('files_location', sa.Column('s3_signature_version', sa.String(length=20), nullable=True))
    op.add_column('files_location', sa.Column('s3_url_expiration', sa.BigInteger(), nullable=True))

def downgrade():
    """Downgrade database."""
    op.drop_column('files_location', 's3_default_block_size')
    op.drop_column('files_location', 's3_maximum_number_of_parts')
    op.drop_column('files_location', 's3_region_name')
    op.drop_column('files_location', 's3_signature_version')
    op.drop_column('files_location', 's3_url_expiration')
