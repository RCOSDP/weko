# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create weko-swordserver branch."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05683afc0320'
down_revision = None
branch_labels = ('weko_swordserver',)
depends_on = None


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
