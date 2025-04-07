# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add server_deafult to repository_id"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d2556236060'
down_revision = '1619a115156f'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column('feedback_mail_list', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default='Root Index')
    op.alter_column('sitelicense_info', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default='Root Index')


def downgrade():
    """Downgrade database."""
    op.alter_column('feedback_mail_list', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default=None)
    op.alter_column('sitelicense_info', 'repository_id',
                    existing_type=sa.String(length=100),
                    server_default=None)
