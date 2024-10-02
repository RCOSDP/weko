# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Force naming convention."""

import sqlalchemy as sa
from alembic import op, util
from sqlalchemy import inspect
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "35c1075e6360"
down_revision = "dbdbc1b19cf2"
branch_labels = ()
depends_on = None

NAMING_CONVENTION = sa.util.immutabledict(
    {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
"""Configuration for constraint naming conventions (v1.0.0b5)."""


def upgrade():
    """Upgrade database."""
    op.execute(text("COMMIT"))  # See https://bitbucket.org/zzzeek/alembic/issue/123
    ctx = op.get_context()
    metadata = ctx.opts["target_metadata"]
    metadata.naming_convention = NAMING_CONVENTION
    metadata.bind = ctx.connection.engine
    insp = inspect(ctx.connection.engine)

    for table_name in insp.get_table_names():
        if table_name not in metadata.tables:
            continue

        table = metadata.tables[table_name]

        ixs = {}
        uqs = {}
        fks = {}

        for ix in insp.get_indexes(table_name):
            ixs[tuple(ix["column_names"])] = ix
        for uq in insp.get_unique_constraints(table_name):
            uqs[tuple(uq["column_names"])] = uq
        for fk in insp.get_foreign_keys(table_name):
            fks[(tuple(fk["constrained_columns"]), fk["referred_table"])] = fk

        with op.batch_alter_table(
            table_name, naming_convention=NAMING_CONVENTION
        ) as batch_op:
            for c in list(table.constraints) + list(table.indexes):
                key = None
                if isinstance(c, sa.schema.ForeignKeyConstraint):
                    key = (tuple(c.column_keys), c.referred_table.name)
                    fk = fks.get(key)
                    if fk and c.name != fk["name"]:
                        batch_op.drop_constraint(fk["name"], type_="foreignkey")
                        batch_op.create_foreign_key(
                            op.f(c.name),
                            fk["referred_table"],
                            fk["constrained_columns"],
                            fk["referred_columns"],
                            **fk["options"]
                        )
                elif isinstance(c, sa.schema.UniqueConstraint):
                    key = tuple(c.columns.keys())
                    uq = uqs.get(key)
                    if uq and c.name != uq["name"]:
                        batch_op.drop_constraint(uq["name"], type_="unique")
                        batch_op.create_unique_constraint(
                            op.f(c.name), uq["column_names"]
                        )
                elif isinstance(c, sa.schema.CheckConstraint):
                    util.warn(
                        "Update {0.table.name} CHECK {0.name} " "manually".format(c)
                    )
                elif isinstance(c, sa.schema.Index):
                    key = tuple(c.columns.keys())
                    ix = ixs.get(key)
                    if ix and c.name != ix["name"]:
                        batch_op.drop_index(ix["name"])
                        batch_op.create_index(
                            op.f(c.name),
                            ix["column_names"],
                            unique=ix["unique"],
                        )
                elif (
                    isinstance(c, sa.schema.PrimaryKeyConstraint)
                    or c.name == "_unnamed_"
                ):
                    # NOTE we don't care about primary keys since they have
                    # specific syntax.
                    pass
                else:
                    raise RuntimeError("Missing {0!r}".format(c))


def downgrade():
    """Downgrade database."""
