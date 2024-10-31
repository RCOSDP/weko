#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""userprofiles-userprofile"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '250f0661704b'
down_revision = 'c4d16e640acc'
branch_labels = ()
depends_on = 'invenio_accounts'


def upgrade():
    """Upgrade database."""
    with op.batch_alter_table('userprofiles_userprofile') as profile_op:
        profile_op.add_column(sa.Column("item13", sa.String(255),nullable=True))
        profile_op.add_column(sa.Column("item14", sa.String(255),nullable=True))
        profile_op.add_column(sa.Column("item15", sa.String(255),nullable=True))
        profile_op.add_column(sa.Column("item16", sa.String(255),nullable=True))

def downgrade():
    """Downgrade database."""
    op.drop_column("userprofiles_userprofile", "item13")
    op.drop_column("userprofiles_userprofile", "item14")
    op.drop_column("userprofiles_userprofile", "item15")
    op.drop_column("userprofiles_userprofile", "item16")
