# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Versioning tests for Invenio-DB"""

import pytest
from mock import patch
from sqlalchemy_continuum import VersioningManager, make_versioned, \
    remove_versioning
from test_db import _mock_entry_points

from invenio_db import InvenioDB


@patch('pkg_resources.iter_entry_points', _mock_entry_points)
def test_disabled_versioning(db, app):
    """Test SQLAlchemy-Continuum with disabled versioning."""
    InvenioDB(app, entry_point_group='invenio_db.models_a')

    with app.app_context():
        assert 2 == len(db.metadata.tables)


@pytest.mark.parametrize("versioning,tables", [
    (False, 1),  (True, 3)
])
def test_disabled_versioning_with_custom_table(db, app, versioning, tables):
    """Test SQLAlchemy-Continuum table loading."""
    app.config['DB_VERSIONING'] = versioning

    class EarlyClass(db.Model):

        __versioned__ = {}

        pk = db.Column(db.Integer, primary_key=True)

    idb = InvenioDB(app, entry_point_group=None, db=db,
                    versioning_manager=VersioningManager())

    with app.app_context():
        db.drop_all()
        db.create_all()

        before = len(db.metadata.tables)
        ec = EarlyClass()
        ec.pk = 1
        db.session.add(ec)
        db.session.commit()

        assert tables == len(db.metadata.tables)

        db.drop_all()

    if versioning:
        remove_versioning(manager=idb.versioning_manager)


@patch('pkg_resources.iter_entry_points', _mock_entry_points)
def test_versioning(db, app):
    """Test SQLAlchemy-Continuum enabled versioning."""
    app.config['DB_VERSIONING'] = True

    idb = InvenioDB(app, entry_point_group='invenio_db.models_b', db=db,
                    versioning_manager=VersioningManager())

    with app.app_context():
        assert 4 == len(db.metadata.tables)

        db.create_all()

        from demo.versioned_b import UnversionedArticle, VersionedArticle
        original_name = 'original_name'

        versioned = VersionedArticle()
        unversioned = UnversionedArticle()

        versioned.name = original_name
        unversioned.name = original_name

        db.session.add(versioned)
        db.session.add(unversioned)
        db.session.commit()

        assert unversioned.name == versioned.name

        modified_name = 'modified_name'

        versioned.name = modified_name
        unversioned.name = modified_name
        db.session.commit()

        assert unversioned.name == modified_name
        assert versioned.name == modified_name
        assert versioned.versions[0].name == original_name
        assert versioned.versions[1].name == versioned.name

        versioned.versions[0].revert()
        db.session.commit()

        assert unversioned.name == modified_name
        assert versioned.name == original_name

        versioned.versions[1].revert()
        db.session.commit()
        assert unversioned.name == versioned.name

    with app.app_context():
        db.drop_all()

    remove_versioning(manager=idb.versioning_manager)


def test_versioning_without_versioned_tables(db, app):
    """Test SQLAlchemy-Continuum without versioned tables."""
    app.config['DB_VERSIONING'] = True

    idb = InvenioDB(app, db=db, entry_point_group=None,
                    versioning_manager=VersioningManager())

    with app.app_context():
        assert 'transaction' in db.metadata.tables

    remove_versioning(manager=idb.versioning_manager)
