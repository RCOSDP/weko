# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create files REST tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "2e97565eba72"
down_revision = "52ce868f33c3"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""

    def created():
        """Return instance of a column."""
        return sa.Column(
            "created",
            sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
            nullable=False,
        )

    def updated():
        """Return instance of a column."""
        return sa.Column(
            "updated",
            sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
            nullable=False,
        )

    def uri():
        """Return instance of a column."""
        return sa.Column(
            "uri", sa.Text().with_variant(mysql.VARCHAR(255), "mysql"), nullable=True
        )

    def key(nullable=True):
        """Return instance of a column."""
        return sa.Column(
            "key",
            sa.Text().with_variant(mysql.VARCHAR(255), "mysql"),
            nullable=nullable,
        )

    op.create_table(
        "files_files",
        created(),
        updated(),
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        uri(),
        sa.Column("storage_class", sa.String(length=1), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(length=255), nullable=True),
        sa.Column("readable", sa.Boolean(name="readable"), nullable=False),
        sa.Column("writable", sa.Boolean(name="writable"), nullable=False),
        sa.Column("last_check_at", sa.DateTime(), nullable=True),
        sa.Column("last_check", sa.Boolean(name="last_check"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uri"),
    )
    op.create_table(
        "files_location",
        created(),
        updated(),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=20), nullable=False),
        sa.Column("uri", sa.String(length=255), nullable=False),
        sa.Column("default", sa.Boolean(name="default"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "files_bucket",
        created(),
        updated(),
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("default_location", sa.Integer(), nullable=False),
        sa.Column("default_storage_class", sa.String(length=1), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("quota_size", sa.BigInteger(), nullable=True),
        sa.Column("max_file_size", sa.BigInteger(), nullable=True),
        sa.Column("locked", sa.Boolean(name="locked"), nullable=False),
        sa.Column("deleted", sa.Boolean(name="deleted"), nullable=False),
        sa.ForeignKeyConstraint(
            ["default_location"], ["files_location.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "files_buckettags",
        sa.Column("bucket_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["bucket_id"], ["files_bucket.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("bucket_id", "key"),
    )
    op.create_table(
        "files_multipartobject",
        created(),
        updated(),
        sa.Column("upload_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("bucket_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        key(),
        sa.Column("file_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=True),
        sa.Column("size", sa.BigInteger(), nullable=True),
        sa.Column("completed", sa.Boolean(name="completed"), nullable=False),
        sa.ForeignKeyConstraint(
            ["bucket_id"], ["files_bucket.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files_files.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("upload_id"),
        sa.UniqueConstraint("upload_id", "bucket_id", "key", name="uix_item"),
    )
    op.create_table(
        "files_object",
        created(),
        updated(),
        sa.Column("bucket_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        key(nullable=False),
        sa.Column("version_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("file_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=True),
        sa.Column("_mimetype", sa.String(length=255), nullable=True),
        sa.Column("is_head", sa.Boolean(name="is_head"), nullable=False),
        sa.ForeignKeyConstraint(
            ["bucket_id"], ["files_bucket.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files_files.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("bucket_id", "key", "version_id"),
    )
    op.create_index(
        op.f("ix_files_object__mimetype"), "files_object", ["_mimetype"], unique=False
    )
    op.create_table(
        "files_multipartobject_part",
        created(),
        updated(),
        sa.Column("upload_id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("part_number", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("checksum", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["upload_id"], ["files_multipartobject.upload_id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("upload_id", "part_number"),
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("files_multipartobject_part")
    op.drop_index(op.f("ix_files_object__mimetype"), table_name="files_object")
    op.drop_table("files_object")
    op.drop_table("files_multipartobject")
    op.drop_table("files_buckettags")
    op.drop_table("files_bucket")
    op.drop_table("files_location")
    op.drop_table("files_files")
