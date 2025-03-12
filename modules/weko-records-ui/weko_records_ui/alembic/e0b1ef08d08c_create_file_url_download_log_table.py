#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create file_url_download_log table."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = 'e0b1ef08d08c'
down_revision = '2750aa1ddc76'
branch_labels = ()
depends_on = 'invenio_accounts'


def upgrade():
    """Upgrade database."""
    bind = op.get_bind()
    session = Session(bind=bind)

    # Recreate 'file_onetime_download' table
    op.drop_table('file_onetime_download')
    op.create_table(
        'file_onetime_download',
        sa.Column('created', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.String(255), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('expiration_date', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('download_limit', sa.Integer(), nullable=False),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('user_mail', sa.String(255), nullable=False),
        sa.Column('is_guest', sa.Boolean(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('extra_info', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.ForeignKeyConstraint(['approver_id'], ['accounts_user.id'], name='fk_file_onetime_download_approver_id'),
        sa.CheckConstraint('created < expiration_date', name='check_expiration_date'),
        sa.CheckConstraint('download_limit > 0', name='check_download_limit_positive'),
        sa.CheckConstraint('download_count <= download_limit', name='check_download_count_limit')
    )

    # Recreate 'file_secret_download' table
    op.drop_table('file_secret_download')
    op.create_table(
        'file_secret_download',
        sa.Column('created', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.String(255), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('label_name', sa.String(255), nullable=False),
        sa.Column('expiration_date', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('download_limit', sa.Integer(), nullable=False),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.ForeignKeyConstraint(['creator_id'], ['accounts_user.id'], name='fk_file_secret_download_creator_id'),
        sa.CheckConstraint('created < expiration_date', name='check_expiration_date'),
        sa.CheckConstraint('download_limit > 0', name='check_download_limit_positive'),
        sa.CheckConstraint('download_count <= download_limit', name='check_download_count_limit')
    )

    # Add 'file_url_download_log' table
    op.create_table(
        'file_url_download_log',
        sa.Column('created', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('url_type', sa.Enum('SECRET', 'ONETIME', name='urltype'), nullable=False),
        sa.Column('secret_url_id', sa.Integer(), sa.ForeignKey('file_secret_download.id'), nullable=True),
        sa.Column('onetime_url_id', sa.Integer(), sa.ForeignKey('file_onetime_download.id'), nullable=True),
        sa.Column('ip_address', INET().with_variant(sa.String(255), 'sqlite').with_variant(sa.String(255), 'mysql'), nullable=True),
        sa.Column('access_status', sa.Enum('OPEN_NO', 'OPEN_DATE', 'OPEN_RESTRICTED', name='accessstatus'), nullable=False),
        sa.Column('used_token', sa.String(255), nullable=False),
        sa.CheckConstraint(
            """
            (url_type = 'SECRET' AND secret_url_id IS NOT NULL AND onetime_url_id IS NULL)
            OR
            (url_type = 'ONETIME' AND onetime_url_id IS NOT NULL AND secret_url_id IS NULL)
            """,
            name="chk_url_id"
        ),
        sa.CheckConstraint(
            """
            (url_type = 'SECRET' AND ip_address IS NOT NULL)
            OR
            (url_type = 'ONETIME' AND ip_address IS NULL)
            """,
            name="chk_ip_address"
        ),
        sa.CheckConstraint(
            """
            (url_type = 'SECRET' AND (access_status = 'OPEN_NO' OR access_status = 'OPEN_DATE'))
            OR
            (url_type = 'ONETIME' AND access_status = 'OPEN_RESTRICTED')
            """,
            name="chk_access_status"
        )
    )

def downgrade():
    """Downgrade database."""
    bind = op.get_bind()
    session = Session(bind=bind)

    op.drop_table('file_url_download_log')
    op.execute("DROP TYPE IF EXISTS urltype;")
    op.execute("DROP TYPE IF EXISTS accessstatus;")
    op.drop_table('file_onetime_download')
    op.create_table(
        'file_onetime_download',
        sa.Column('created', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('user_mail', sa.String(255), nullable=False),
        sa.Column('record_id', sa.String(255), nullable=False),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('expiration_date', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('extra_info', sa.JSON(), nullable=True, server_default=sa.text("'{}'")),
    )
    op.drop_table('file_secret_download')
    op.create_table(
        'file_secret_download',
        sa.Column('created', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=False), nullable=False),
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('user_mail', sa.String(255), nullable=False),
        sa.Column('record_id', sa.String(255), nullable=False),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('expiration_date', sa.Integer(), nullable=False, server_default=sa.text('0')),
    )
