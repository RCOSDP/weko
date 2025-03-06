#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create weko-records-ui branch."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2750aa1ddc76'
down_revision = None
branch_labels = ('weko_records_ui',)
depends_on = 'invenio_accounts'


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
