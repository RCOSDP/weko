# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""add repository_id column"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1619a115156f'
down_revision = '10e311ab03bf'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column('feedback_mail_list', sa.Column('repository_id', sa.String(length=100), nullable=False, server_default='Root Index'))
    op.add_column('sitelicense_info', sa.Column('repository_id', sa.String(length=100), nullable=False, server_default='Root Index'))


def downgrade():
    """Downgrade database."""
    op.drop_column('sitelicense_info', 'repository_id')
    op.drop_column('feedback_mail_list', 'repository_id')
