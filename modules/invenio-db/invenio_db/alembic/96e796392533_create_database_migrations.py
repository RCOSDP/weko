# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create database migrations."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "96e796392533"
down_revision = None
branch_labels = ("default",)
depends_on = None


def upgrade():
    """Update database."""


def downgrade():
    """Downgrade database."""
