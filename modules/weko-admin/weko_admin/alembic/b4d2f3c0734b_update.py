#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""update"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4d2f3c0734b'
down_revision = '45bf6e63b05a'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_unique_constraint(op.f('uq_admin_lang_settings_lang_code'), 'admin_lang_settings', ['lang_code'])
    op.create_unique_constraint(op.f('uq_api_certificate_api_code'), 'api_certificate', ['api_code'])
    op.create_unique_constraint(op.f('uq_billing_permission_user_id'), 'billing_permission', ['user_id'])
    op.create_unique_constraint(op.f('uq_doi_identifier_id'), 'doi_identifier', ['id'])
    op.create_unique_constraint(op.f('uq_stats_report_target_target_id'), 'stats_report_target', ['target_id'])
    op.create_unique_constraint(op.f('uq_stats_report_unit_unit_id'), 'stats_report_unit', ['unit_id'])


def downgrade():
    """Downgrade database."""
    op.drop_constraint(op.f('uq_stats_report_unit_unit_id'), 'stats_report_unit', type_='unique')
    op.drop_constraint(op.f('uq_stats_report_target_target_id'), 'stats_report_target', type_='unique')
    op.drop_constraint(op.f('uq_doi_identifier_id'), 'doi_identifier', type_='unique')
    op.drop_constraint(op.f('uq_billing_permission_user_id'), 'billing_permission', type_='unique')
    op.drop_constraint(op.f('uq_api_certificate_api_code'), 'api_certificate', type_='unique')
    op.drop_constraint(op.f('uq_admin_lang_settings_lang_code'), 'admin_lang_settings', type_='unique')
