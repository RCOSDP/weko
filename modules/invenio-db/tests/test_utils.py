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
from mock import patch
from sqlalchemy_continuum import remove_versioning
from sqlalchemy_utils.types import EncryptedType
from test_db import _mock_entry_points

from invenio_db import InvenioDB
from invenio_db.utils import rebuild_encrypted_properties, \
    versioning_model_classname, versioning_models_registered


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
    assert versioning_model_classname(manager, FooClass) == \
        'Test_UtilsFooClassVersion'
    manager.options['use_module_name'] = False
    assert versioning_model_classname(
        manager, FooClass) == 'FooClassVersion'
    assert versioning_models_registered(manager, db.Model)
    remove_versioning(manager=manager)
