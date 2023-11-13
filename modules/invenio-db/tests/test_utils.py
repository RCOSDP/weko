# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test DB utilities."""

import pytest
import sqlalchemy as sa
from flask import current_app
from mock import patch
from sqlalchemy_continuum import remove_versioning
from sqlalchemy_utils.types import EncryptedType

from invenio_db import InvenioDB
from invenio_db.utils import rebuild_encrypted_properties, \
    versioning_model_classname, versioning_models_registered,\
        create_alembic_version_table,drop_alembic_version_table

# .tox/c1/bin/pytest --cov=invenio_db tests/test_utils.py::test_rebuild_encrypted_properties -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_rebuild_encrypted_properties(db, app):
    old_secret_key = "SECRET_KEY_1"
    new_secret_key = "SECRET_KEY_2"
    app.secret_key = old_secret_key

    def _secret_key():
        return app.config.get('SECRET_KEY').encode('utf-8')

    class Demo(db.Model):
        __tablename__ = 'demo'
        pk = db.Column(sa.Integer, primary_key=True)
        et = db.Column(
            EncryptedType(type_in=db.Unicode, key=_secret_key), nullable=False
        )

    InvenioDB(app, entry_point_group=False, db=db)

    with app.app_context():
        db.create_all()
        d1 = Demo(et="something")
        db.session.add(d1)
        db.session.commit()

    app.secret_key = new_secret_key

    with app.app_context():
        with pytest.raises(ValueError):
            db.session.query(Demo).all()
        with pytest.raises(AttributeError):
            rebuild_encrypted_properties(old_secret_key, Demo, ['nonexistent'])
        assert app.secret_key == new_secret_key

    with app.app_context():
        with pytest.raises(ValueError):
            db.session.query(Demo).all()
        rebuild_encrypted_properties(old_secret_key, Demo, ['et'])
        d1_after = db.session.query(Demo).first()
        assert d1_after.et == "something"

    with app.app_context():
        db.drop_all()


def test_versioning_model_classname(db, app):
    """Test the versioning model utilities."""
    class FooClass(db.Model):
        __versioned__ = {}
        pk = db.Column(db.Integer, primary_key=True)

    app.config['DB_VERSIONING'] = True
    idb = InvenioDB(app)
    manager = idb.versioning_manager
    manager.options['use_module_name'] = True
    result = versioning_model_classname(manager, FooClass)
    assert  result== 'TestsTest_UtilsFooClassVersion'
    manager.options['use_module_name'] = False
    assert versioning_model_classname(
        manager, FooClass) == 'FooClassVersion'
    assert versioning_models_registered(manager, db.Model)
    remove_versioning(manager=manager)

# .tox/c1/bin/pytest --cov=invenio_db tests/test_utils.py::test_versioning_models_registered -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_versioning_models_registered(db, app, mock_entry_points):
    app.config['DB_VERSIONING'] = True
    idb = InvenioDB(app, db=db)
    manager = idb.versioning_manager
    result = versioning_models_registered(manager, db.Model)
    assert result == True
    remove_versioning(manager=manager)

# .tox/c1/bin/pytest --cov=invenio_db tests/test_utils.py::test_create_alembic_version_table -v -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
@pytest.mark.parametrize("has_version_table",[True,False])
def test_create_alembic_version_table(db, app, has_version_table):
    idb = InvenioDB(app)
    with patch("alembic.runtime.migration.MigrationContext._has_version_table",return_value=has_version_table):
        create_alembic_version_table()
    
    alembic = current_app.extensions['invenio-db'].alembic
    assert alembic.migration_context._has_version_table() != has_version_table

# .tox/c1/bin/pytest --cov=invenio_db tests/test_utils.py::test_drop_alembic_version_table -v -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_drop_alembic_version_table(app, db,mock_entry_points):
    # not exist alembic_version
    idb = InvenioDB(app)
    drop_alembic_version_table()
    
    # exist alembic_version
    idb = InvenioDB(app,db=db)
    alembic = current_app.extensions['invenio-db'].alembic
    alembic.migration_context._ensure_version_table()
    drop_alembic_version_table()