#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create MailTemplateUsers."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from invenio_mail.models import MailType

# revision identifiers, used by Alembic.
revision = 'b1495e98969b'
down_revision = 'ddbb24276fdc'
branch_labels = ()
depends_on = None

def upgrade():
    """Upgrade database."""
    op.create_table(
        'mail_template_users',
        sa.Column('created', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('template_id', sa.Integer, sa.ForeignKey('mail_templates.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('accounts_user.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('mail_type', sa.Enum(MailType), primary_key=True, nullable=False),
    )

def downgrade():
    """Downgrade database."""
    op.drop_table('mail_template_users')
    mail_type_enum = postgresql.ENUM('recipient', 'cc', 'bcc', name='mailtype')
    mail_type_enum.drop(op.get_bind())
