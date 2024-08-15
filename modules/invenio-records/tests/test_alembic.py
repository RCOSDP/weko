# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Invenio Records."""

import pytest
from invenio_db.utils import drop_alembic_version_table


@pytest.mark.skip(reason="Caused by mergepoint")
def test_alembic(testapp, db):
    """Test alembic recipes."""
    ext = testapp.extensions["invenio-db"]

    if db.engine.name == "sqlite":
        raise pytest.skip("Upgrades are not supported on SQLite.")

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    drop_alembic_version_table()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.stamp()
    ext.alembic.downgrade(target="96e796392533")
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    drop_alembic_version_table()
