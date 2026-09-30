#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create weko_notifications branch."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33c2a0cb8f5f'
down_revision = None
branch_labels = ('weko_notifications',)
depends_on = None


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
