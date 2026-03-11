#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create the first branch."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c509a18eb6a0'
down_revision = None
branch_labels = ('invenio_mail',)
depends_on = 'invenio_accounts'


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
