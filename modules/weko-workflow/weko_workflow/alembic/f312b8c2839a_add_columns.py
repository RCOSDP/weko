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
revision = 'f312b8c2839a'
down_revision = 'a560202ff0ac'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('workflow_flow_define', sa.Column('repository_id', sa.String(length=100), nullable=False, server_default='Root Index'))
    op.add_column('workflow_workflow', sa.Column('repository_id', sa.String(length=100), nullable=False, server_default='Root Index'))


def downgrade():
    """Downgrade database."""
    op.drop_column('workflow_workflow', 'repository_id')
    op.drop_column('workflow_flow_define', 'repository_id')
