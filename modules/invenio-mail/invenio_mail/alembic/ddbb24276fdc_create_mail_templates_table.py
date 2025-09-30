#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create mail_templates table"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddbb24276fdc'
down_revision = 'c509a18eb6a0'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        'mail_template_genres',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False, server_default=''),
    )

    op.create_table(
        'mail_templates',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('mail_subject', sa.String(255), nullable=True),
        sa.Column('mail_body', sa.Text, nullable=True),
        sa.Column('default_mail', sa.Boolean, nullable=True),
        sa.Column('genre_id', sa.Integer, nullable=False, server_default='3'),
        sa.ForeignKeyConstraint(
            ['genre_id'], ['mail_template_genres.id'],
            name='fk_mail_templates_genre_id_mail_template_genres',
            ondelete='RESTRICT',
            onupdate='CASCADE'
        )
    )


def downgrade():
    """Downgrade database."""
    op.drop_table('mail_templates')
    op.drop_table('mail_template_genres')

