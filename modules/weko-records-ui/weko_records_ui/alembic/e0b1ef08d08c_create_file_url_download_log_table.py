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


# revision identifiers, used by Alembic.
revision = 'e0b1ef08d08c'
down_revision = '2750aa1ddc76'
branch_labels = ()
depends_on = 'invenio_accounts'

def upgrade():
    """Upgrade database."""
    op.create_table(
        'file_url_download_log',
        sa.Column('created', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
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

    # Modify file_onetime_download table
    op.add_column('file_onetime_download', sa.Column('approver_id', sa.Integer(), nullable=False, default=0))
    op.add_column('file_onetime_download', sa.Column('is_guest', sa.Boolean(), nullable=False, default=False))
    op.add_column('file_onetime_download', sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False))
    op.add_column('file_onetime_download', sa.Column('download_limit', sa.Integer(), nullable=False, default=0))
    op.drop_column('file_onetime_download', 'expiration_date')
    op.add_column('file_onetime_download', sa.Column('expiration_date', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')))
    op.create_foreign_key('fk_file_onetime_download_approver_id', 'file_onetime_download', 'accounts_user', ['approver_id'], ['id'])
    op.create_check_constraint('check_expiration_date', 'file_onetime_download', 'created < expiration_date')
    op.create_check_constraint('check_download_limit_positive', 'file_onetime_download', 'download_limit > 0')
    op.create_check_constraint('check_download_count_limit', 'file_onetime_download', 'download_count <= download_limit')

    # Modify file_secret_download table
    op.add_column('file_secret_download', sa.Column('creator_id', sa.Integer(), nullable=False, default=0))
    op.add_column('file_secret_download', sa.Column('label_name', sa.String(255), nullable=False, default=''))
    op.add_column('file_secret_download', sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False))
    op.add_column('file_secret_download', sa.Column('download_limit', sa.Integer(), nullable=False, default=0))
    op.drop_column('file_secret_download', 'user_mail')
    op.drop_column('file_secret_download', 'expiration_date')
    op.add_column('file_secret_download', sa.Column('expiration_date', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')))
    op.create_foreign_key('fk_file_secret_download_creator_id', 'file_secret_download', 'accounts_user', ['creator_id'], ['id'])
    op.create_check_constraint('check_expiration_date', 'file_secret_download', 'created < expiration_date')
    op.create_check_constraint('check_download_limit_positive', 'file_secret_download', 'download_limit > 0')
    op.create_check_constraint('check_download_count_limit', 'file_secret_download', 'download_count <= download_limit')

def downgrade():
    """Downgrade database."""
    op.drop_table('file_url_download_log')
    op.drop_constraint('fk_file_onetime_download_approver_id', 'file_onetime_download', type_='foreignkey')
    op.drop_constraint('check_expiration_date', 'file_onetime_download', type_='check')
    op.drop_constraint('check_download_limit_positive', 'file_onetime_download', type_='check')
    op.drop_constraint('check_download_count_limit', 'file_onetime_download', type_='check')
    op.drop_column('file_onetime_download', 'approver_id')
    op.drop_column('file_onetime_download', 'is_guest')
    op.drop_column('file_onetime_download', 'is_deleted')
    op.drop_column('file_onetime_download', 'download_limit')
    op.drop_column('file_onetime_download', 'expiration_date')
    op.add_column('file_onetime_download', sa.Column('expiration_date', sa.Integer(), nullable=False))

    op.drop_constraint('fk_file_secret_download_creator_id', 'file_secret_download', type_='foreignkey')
    op.drop_constraint('check_expiration_date', 'file_secret_download', type_='check')
    op.drop_constraint('check_download_limit_positive', 'file_secret_download', type_='check')
    op.drop_constraint('check_download_count_limit', 'file_secret_download', type_='check')
    op.drop_column('file_secret_download', 'creator_id')
    op.drop_column('file_secret_download', 'label_name')
    op.drop_column('file_secret_download', 'is_deleted')
    op.drop_column('file_secret_download', 'download_limit')
    op.drop_column('file_secret_download', 'expiration_date')
    op.add_column('file_secret_download', sa.Column('user_mail', sa.String(255), nullable=False))
    op.add_column('file_secret_download', sa.Column('expiration_date', sa.Integer(), nullable=False))

    op.execute("DROP TYPE IF EXISTS urltype;")
    op.execute("DROP TYPE IF EXISTS accessstatus;")
