# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
# from .signals import secret_key_changed

"""Invenio-DB utility functions."""

from flask import current_app
from sqlalchemy.engine import reflection
from werkzeug.local import LocalProxy

from .shared import db

_db = LocalProxy(lambda: current_app.extensions['sqlalchemy'].db)


def rebuild_encrypted_properties(old_key, model, properties):
    """Rebuild a model's EncryptedType properties when the SECRET_KEY is changed.

    :param old_key: old SECRET_KEY.
    :param model: the affected db model.
    :param properties: list of properties to rebuild.
    """
    inspector = reflection.Inspector.from_engine(db.engine)
    primary_key_names = inspector.get_primary_keys(model.__tablename__)

    new_secret_key = current_app.secret_key
    db.session.expunge_all()
    try:
        with db.session.begin_nested():
            current_app.secret_key = old_key
            db_columns = []
            for primary_key in primary_key_names:
                db_columns.append(getattr(model, primary_key))
            for prop in properties:
                db_columns.append(getattr(model, prop))
            old_rows = db.session.query(*db_columns).all()
    except Exception as e:
        current_app.logger.error(
            'Exception occurred while reading encrypted properties. '
            'Try again before starting the server with the new secret key.')
        raise e
    finally:
        current_app.secret_key = new_secret_key
        db.session.expunge_all()

    for old_row in old_rows:
        primary_keys, old_entries = old_row[:len(primary_key_names)], \
                                    old_row[len(primary_key_names):]
        primary_key_fields = dict(zip(primary_key_names, primary_keys))
        update_values = dict(zip(properties, old_entries))
        model.query.filter_by(**primary_key_fields).\
            update(update_values)
    db.session.commit()


def create_alembic_version_table():
    """Create alembic_version table."""
    alembic = current_app.extensions['invenio-db'].alembic
    if not alembic.migration_context._has_version_table():
        alembic.migration_context._ensure_version_table()
        for head in alembic.script_directory.revision_map._real_heads:
            alembic.migration_context.stamp(alembic.script_directory, head)


def drop_alembic_version_table():
    """Drop alembic_version table."""
    if _db.engine.dialect.has_table(_db.engine, 'alembic_version'):
        alembic_version = _db.Table('alembic_version', _db.metadata,
                                    autoload_with=_db.engine)
        alembic_version.drop(bind=_db.engine)


def versioning_model_classname(manager, model):
    """Get the name of the versioned model class."""
    if manager.options.get('use_module_name', True):
        return '%s%sVersion' % (
            model.__module__.title().replace('.', ''), model.__name__)
    else:
        return '%sVersion' % (model.__name__,)


def versioning_models_registered(manager, base):
    """Return True if all versioning models have been registered."""
    declared_models = base._decl_class_registry.keys()
    return all(versioning_model_classname(manager, c) in declared_models
               for c in manager.pending_classes)
