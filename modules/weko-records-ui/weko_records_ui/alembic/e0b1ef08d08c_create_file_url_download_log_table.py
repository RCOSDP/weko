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

    # Modify 'file_onetime_download' table
    op.execute("TRUNCATE TABLE file_onetime_download RESTART IDENTITY CASCADE")
    op.add_column('file_onetime_download', sa.Column('approver_id', sa.Integer(), nullable=False))
    op.add_column('file_onetime_download', sa.Column('is_guest', sa.Boolean(), nullable=True))
    session.execute("""
                    UPDATE file_onetime_download f
                    SET is_guest = NOT EXISTS (
                        SELECT 1 FROM accounts_user a WHERE a.email = f.user_mail)
                    """)
    op.alter_column('file_onetime_download', 'is_guest', nullable=False)
    op.add_column('file_onetime_download', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
    op.add_column('file_onetime_download', sa.Column('download_limit', sa.Integer(), nullable=True))
    session.execute("""
                    UPDATE file_onetime_download
                    SET download_limit = download_count
                    """)
    session.execute("""
                    UPDATE file_onetime_download
                    SET download_count = 0
                    """)
    op.alter_column('file_onetime_download', 'download_limit', nullable=False)
    op.add_column('file_onetime_download', sa.Column('new_expiration_date', sa.DateTime(), nullable=True))
    session.execute("""
                    UPDATE file_onetime_download
                    SET new_expiration_date = created + INTERVAL '1 day' * expiration_date
                    """)
    op.drop_column('file_onetime_download', 'expiration_date')
    op.alter_column('file_onetime_download', 'new_expiration_date', new_column_name='expiration_date')

    # Add constraints to 'file_onetime_download' table
    op.create_foreign_key('fk_file_onetime_download_approver_id', 'file_onetime_download', 'accounts_user', ['approver_id'], ['id'])
    op.create_check_constraint('check_expiration_date', 'file_onetime_download', 'created < expiration_date')
    op.create_check_constraint('check_download_limit_positive', 'file_onetime_download', 'download_limit > 0')
    op.create_check_constraint('check_download_count_limit', 'file_onetime_download', 'download_count <= download_limit')

    # Modify 'file_secret_download' table
    op.add_column('file_secret_download', sa.Column('creator_id', sa.Integer(), nullable=True))
    session.execute("""
                    UPDATE file_secret_download f
                    SET creator_id = (SELECT id FROM accounts_user WHERE email = f.user_mail)
                    """)
    op.alter_column('file_secret_download', 'creator_id', nullable=False)
    op.drop_column('file_secret_download', 'user_mail')
    op.add_column('file_secret_download', sa.Column('label_name', sa.String(255), nullable=True))
    session.execute("""
                    UPDATE file_secret_download
                    SET label_name = TO_CHAR(created, 'YYYY-MM-DD') || '_' || file_name
                    """)
    op.alter_column('file_secret_download', 'label_name', nullable=False)
    op.add_column('file_secret_download', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
    op.add_column('file_secret_download', sa.Column('download_limit', sa.Integer(), nullable=True))
    session.execute("""
                    UPDATE file_secret_download
                    SET download_limit = download_count
                    """)
    session.execute("""
                    UPDATE file_secret_download
                    SET download_count = 0
                    """)
    op.alter_column('file_secret_download', 'download_limit', nullable=False)
    op.add_column('file_secret_download', sa.Column('new_expiration_date', sa.DateTime(), nullable=True))
    session.execute("""
                    UPDATE file_secret_download
                    SET new_expiration_date = created + INTERVAL '1 day' * expiration_date
                    """)
    op.drop_column('file_secret_download', 'expiration_date')
    op.alter_column('file_secret_download', 'new_expiration_date', new_column_name='expiration_date')

    # Add constraints to 'file_secret_download' table
    op.create_foreign_key('fk_file_secret_download_creator_id', 'file_secret_download', 'accounts_user', ['creator_id'], ['id'])
    op.create_check_constraint('check_expiration_date', 'file_secret_download', 'created < expiration_date')
    op.create_check_constraint('check_download_limit_positive', 'file_secret_download', 'download_limit > 0')
    op.create_check_constraint('check_download_count_limit', 'file_secret_download', 'download_count <= download_limit')

def downgrade():
    """Downgrade database."""
    bind = op.get_bind()
    session = Session(bind=bind)

    op.drop_table('file_url_download_log')
    op.execute("DROP TYPE IF EXISTS urltype;")
    op.execute("DROP TYPE IF EXISTS accessstatus;")

    # Remove constraints from 'file_onetime_download' table
    op.drop_constraint('check_download_count_limit', 'file_onetime_download', type_='check')
    op.drop_constraint('check_download_limit_positive', 'file_onetime_download', type_='check')
    op.drop_constraint('check_expiration_date', 'file_onetime_download', type_='check')
    op.drop_constraint('fk_file_onetime_download_approver_id', 'file_onetime_download', type_='foreignkey')

    # Modify 'file_onetime_download' table
    op.alter_column('file_onetime_download', 'expiration_date', new_column_name='new_expiration_date')
    op.add_column('file_onetime_download', sa.Column('expiration_date', sa.Integer(), nullable=True))
    session.execute("""
                    UPDATE file_onetime_download
                    SET expiration_date = EXTRACT(DAY FROM (new_expiration_date - created))
                    """)
    op.alter_column('file_onetime_download', 'expiration_date', nullable=False)
    op.drop_column('file_onetime_download', 'new_expiration_date')
    session.execute("""
                    UPDATE file_onetime_download
                    SET download_count = download_limit
                    """)
    op.drop_column('file_onetime_download', 'download_limit')
    op.drop_column('file_onetime_download', 'is_deleted')
    op.drop_column('file_onetime_download', 'is_guest')
    op.drop_column('file_onetime_download', 'approver_id')

    # Remove constraints from 'file_secret_download' table
    op.drop_constraint('check_download_count_limit', 'file_secret_download', type_='check')
    op.drop_constraint('check_download_limit_positive', 'file_secret_download', type_='check')
    op.drop_constraint('check_expiration_date', 'file_secret_download', type_='check')
    op.drop_constraint('fk_file_secret_download_creator_id', 'file_secret_download', type_='foreignkey')

    # Modify 'file_secret_download' table
    op.alter_column('file_secret_download', 'expiration_date', new_column_name='new_expiration_date')
    op.add_column('file_secret_download', sa.Column('expiration_date', sa.Integer(), nullable=True))
    session.execute("""
                    UPDATE file_secret_download
                    SET expiration_date = EXTRACT(DAY FROM (new_expiration_date - created))
                    """)
    op.alter_column('file_secret_download', 'expiration_date', nullable=False)
    op.drop_column('file_secret_download', 'new_expiration_date')
    session.execute("""
                    UPDATE file_secret_download
                    SET download_count = download_limit
                    """)
    op.drop_column('file_secret_download', 'download_limit')
    op.drop_column('file_secret_download', 'is_deleted')
    op.drop_column('file_secret_download', 'label_name')
    op.add_column('file_secret_download', sa.Column('user_mail', sa.String(255), nullable=True))
    session.execute("""
                    UPDATE file_secret_download f
                    SET user_mail = (SELECT email FROM accounts_user WHERE id = f.creator_id)
                    """)
    op.alter_column('file_secret_download', 'user_mail', nullable=False)
    op.drop_column('file_secret_download', 'creator_id')
