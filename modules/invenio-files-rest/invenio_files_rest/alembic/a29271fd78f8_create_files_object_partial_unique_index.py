#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create files object partial unique index."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a29271fd78f8"
down_revision = "8ae99b034410"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    if op.get_context().dialect.name == "postgresql":
        op.create_index(
            "ix_uq_partial_files_object_is_head",
            "files_object",
            ["bucket_id", "key"],
            unique=True,
            postgresql_where=sa.text("is_head"),
        )


def downgrade():
    """Downgrade database."""
    if op.get_context().dialect.name == "postgresql":
        op.drop_index("ix_uq_partial_files_object_is_head", table_name="files_object")
