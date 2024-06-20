# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add on delete cascade."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4e57407b8e4a"
down_revision = "12a88921ada2"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.drop_constraint(
        "fk_oauth2server_client_user_id_accounts_user",
        "oauth2server_client",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_oauth2server_client_user_id_accounts_user"),
        "oauth2server_client",
        "accounts_user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_oauth2server_client_user_id"),
        "oauth2server_client",
        ["user_id"],
        unique=False,
    )
    op.drop_constraint(
        "fk_oauth2server_token_user_id_accounts_user",
        "oauth2server_token",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_oauth2server_token_user_id_accounts_user"),
        "oauth2server_token",
        "accounts_user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_oauth2server_token_user_id"),
        "oauth2server_token",
        ["user_id"],
        unique=False,
    )
    op.drop_constraint(
        "fk_oauth2server_token_client_id_oauth2server_client",
        "oauth2server_token",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_oauth2server_token_client_id_oauth2server_client"),
        "oauth2server_token",
        "oauth2server_client",
        ["client_id"],
        ["client_id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_oauth2server_token_client_id"),
        "oauth2server_token",
        ["client_id"],
        unique=False,
    )


def downgrade():
    """Downgrade database."""
    op.drop_constraint(
        op.f("fk_oauth2server_token_user_id_accounts_user"),
        "oauth2server_token",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_oauth2server_token_user_id"), table_name="oauth2server_token"
    )
    op.create_foreign_key(
        "fk_oauth2server_token_user_id_accounts_user",
        "oauth2server_token",
        "accounts_user",
        ["user_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("fk_oauth2server_token_client_id_oauth2server_client"),
        "oauth2server_token",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_oauth2server_token_client_id"), table_name="oauth2server_token"
    )
    op.create_foreign_key(
        "fk_oauth2server_token_client_id_oauth2server_client",
        "oauth2server_token",
        "oauth2server_client",
        ["client_id"],
        ["client_id"],
    )
    op.drop_constraint(
        op.f("fk_oauth2server_client_user_id_accounts_user"),
        "oauth2server_client",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_oauth2server_client_user_id"), table_name="oauth2server_client"
    )
    op.create_foreign_key(
        "fk_oauth2server_client_user_id_accounts_user",
        "oauth2server_client",
        "accounts_user",
        ["user_id"],
        ["id"],
    )
