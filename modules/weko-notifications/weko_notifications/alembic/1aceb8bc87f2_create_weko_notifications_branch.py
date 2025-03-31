# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Create weko-notifications branch."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1aceb8bc87f2'
down_revision = None
branch_labels = ('weko_notifications',)
depends_on = None


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
