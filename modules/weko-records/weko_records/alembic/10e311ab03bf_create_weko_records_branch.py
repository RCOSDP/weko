# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create weko_records branch."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10e311ab03bf'
down_revision = None
branch_labels = ('weko_records',)
depends_on = None


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
