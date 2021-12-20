# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask.cli import ScriptInfo
from flask_celeryext import FlaskCeleryExt
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User
from invenio_accounts.testutils import create_test_user
from invenio_db import InvenioDB, db
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_records import InvenioRecords
from sqlalchemy_utils.functions import create_database, database_exists
from weko_index_tree.models import Index
from weko_search_ui import WekoSearchUI
from weko_theme import WekoTheme

from invenio_oaiharvester import InvenioOAIHarvester
from invenio_oaiharvester.models import OAIHarvestConfig


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask(__name__, instance_path=instance_path)
    app.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///test.db'),
        TESTING=True,
        INDEX_IMG='indextree/36466818-image.jpg',
        SEARCH_UI_SEARCH_INDEX='tenant1',
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
    )
    FlaskCeleryExt(app)
    InvenioAccounts(app)
    InvenioDB(app)
    InvenioI18N(app)
    InvenioJSONSchemas(app)
    InvenioPIDRelations(app)
    InvenioRecords(app)
    WekoSearchUI(app)
    WekoTheme(app)
    InvenioOAIHarvester(app)

    with app.app_context():
        if str(db.engine.url) != 'sqlite://' and \
           not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            db.drop_all()
        shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.fixture()
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)


@pytest.fixture()
def sample_config(app):
    source_name = "arXiv"
    with app.app_context():
        source = OAIHarvestConfig(
            name=source_name,
            baseurl="http://export.arxiv.org/oai2",
            metadataprefix="arXiv",
            setspecs="physics",
        )
        source.save()
        db.session.commit()
    return source_name


@pytest.fixture()
def sample_record_xml():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response.xml"
    )).read()
    return raw_xml


@pytest.fixture()
def sample_record_xml_utf8():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response_utf8.xml"
    )).read()
    return raw_xml


@pytest.fixture()
def sample_record_xml_oai_dc():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_oai_dc_response.xml"
    )).read()
    return raw_xml


@pytest.fixture()
def sample_empty_set():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_empty_response.xml"
    )).read()
    return raw_xml


@pytest.fixture
def sample_list_xml():
    raw_physics_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response_listrecords_physics.xml"
    )).read()
    return raw_physics_xml


@pytest.fixture
def sample_list_xml_cs():
    raw_cs_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response_listrecords_cs.xml"
    )).read()
    return raw_cs_xml


@pytest.fixture
def sample_jpcoar_list_xml():
    raw_cs_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/oai.xml"
    )).read()
    return raw_cs_xml


@pytest.fixture()
def location(app):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return location
