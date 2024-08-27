# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Alter files_files.last_check column to nullable."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f741aa746a7d"
down_revision = "2e97565eba72"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.alter_column(
        "files_files", "last_check", existing_type=sa.BOOLEAN(), nullable=True
    )


def downgrade():
    """Downgrade database."""
    op.alter_column(
        "files_files", "last_check", existing_type=sa.BOOLEAN(), nullable=False
    )
