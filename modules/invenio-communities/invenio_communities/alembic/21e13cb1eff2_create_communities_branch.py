# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create communities branch."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '21e13cb1eff2'
down_revision = None
branch_labels = (u'invenio_communities', )
depends_on = 'dbdbc1b19cf2'


def upgrade():
    """Update database."""


def downgrade():
    """Downgrade database."""
