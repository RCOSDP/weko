# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

import os
import shutil
import tempfile
import pytest

from flask import Flask
from flask_babel import Babel
from flask_celeryext import FlaskCeleryExt
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_pidstore import InvenioPIDStore
from invenio_celery import InvenioCelery
from invenio_i18n import InvenioI18N
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DropConstraint, DropSequence, DropTable
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_records import InvenioRecords
from invenio_records.api import Record
from invenio_records.systemfields import SystemFieldsMixin

pytest_plugins = ("celery.contrib.pytest",)


@compiles(DropTable, "postgresql")
def _compile_drop_table(element, compiler, **kwargs):
    return compiler.visit_drop_table(element) + " CASCADE"


@compiles(DropConstraint, "postgresql")
def _compile_drop_constraint(element, compiler, **kwargs):
    return compiler.visit_drop_constraint(element) + " CASCADE"


@compiles(DropSequence, "postgresql")
def _compile_drop_sequence(element, compiler, **kwargs):
    return compiler.visit_drop_sequence(element) + " CASCADE"


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture(scope='function')
def base_app(instance_path):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update({
        "CELERY_ALWAYS_EAGER": True,
        "CELERY_CACHE_BACKEND": "memory",
        "CELERY_EAGER_PROPAGATES_EXCEPTIONS": True,
        "CELERY_RESULT_BACKEND": "cache",
        "SECRET_KEY": "CHANGE_ME",
        "SECURITY_PASSWORD_SALT": "CHANGE_ME_ALSO",
        "SQLALCHEMY_DATABASE_URI": os.getenv('SQLALCHEMY_DATABASE_URI',
                                            'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        "SQLALCHEMY_TRACK_MODIFICATIONS": True,
        "TESTING": True,
    })
    FlaskCeleryExt(app_)
    InvenioCelery(app_)
    InvenioDB(app_)
    InvenioPIDStore(app_)
    InvenioI18N(app_)

    return app_

@pytest.yield_fixture(scope='function')
def app(base_app):
    """Flask application fixture with InvenioStats."""
    InvenioRecords(base_app)
    Babel(base_app)
    with base_app.app_context():
        yield base_app


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture for use with pytest-invenio."""

    def _create_app(**config):
        app_ = Flask(
            __name__,
            instance_path=instance_path,
        )
        app_.config.update(config)
        InvenioCelery(app_)
        InvenioDB(app_)
        InvenioRecords(app_)
        InvenioI18N(app_)
        return app_

    return _create_app


@pytest.fixture()
def db(app):
    with app.app_context():
        """Database fixture.

        Recreate db at each test that requires it.
        """
        if not database_exists(str(db_.engine.url)):
            create_database(str(db_.engine.url))
        db_.create_all()
        yield db_
        db_.session.remove()
        db_.drop_all()


@pytest.fixture()
def languages(db):
    """Languages fixture."""

    class Language(Record, SystemFieldsMixin):
        pass

    languages_data = (
        {
            "title": "English",
            "iso": "en",
            "information": {"native_speakers": "400 million", "ethnicity": "English"},
        },
        {
            "title": "French",
            "iso": "fr",
            "information": {"native_speakers": "76.8 million", "ethnicity": "French"},
        },
        {
            "title": "Spanish",
            "iso": "es",
            "information": {"native_speakers": "489 million", "ethnicity": "Spanish"},
        },
        {
            "title": "Italian",
            "iso": "it",
            "information": {"native_speakers": "67 million", "ethnicity": "Italians"},
        },
        {
            "title": "Old English",
            "iso": "oe",
            "information": {
                "native_speakers": "400 million",
                "ethnicity": ["English", "Old english"],
            },
        },
    )

    languages = {}
    for lang in languages_data:
        lang_rec = Language.create(lang)
        languages[lang["iso"]] = lang_rec
    db.session.commit()
    return Language, languages
