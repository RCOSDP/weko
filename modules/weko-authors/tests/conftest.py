# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Pytest configuration."""
import os,sys
import shutil
import tempfile
import json
import uuid
from os.path import dirname, join

from elasticsearch import Elasticsearch
from sqlalchemy import inspect

import pytest
from flask import Flask, url_for, Response
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user, login_user_via_session

from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_communities.models import Community
from invenio_db import InvenioDB, db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location, FileInstance
from invenio_indexer import InvenioIndexer
from invenio_search import InvenioSearch,RecordsSearch
from weko_search_ui import WekoSearchUI
from weko_index_tree.models import Index

from weko_authors.views import blueprint_api
from weko_authors import WekoAuthors
from weko_authors.models import Authors, AuthorsPrefixSettings, AuthorsAffiliationSettings
from weko_theme import WekoTheme
import weko_authors.mappings.v2

sys.path.append(os.path.dirname(__file__))

class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = 'records'
        doc_types = None

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'excludes': ['_access']}})


@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


class MockEs():
    def __init__(self,**keywargs):
        self.indices = self.MockIndices()
        self.es = Elasticsearch()
        self.cluster = self.MockCluster()
    def index(self, id="",version="",version_type="",index="",doc_type="",body="",**arguments):
        pass
    def delete(self,id="",index="",doc_type="",**kwargs):
        return Response(response=json.dumps({}),status=500)
    @property
    def transport(self):
        return self.es.transport
    class MockIndices():
        def __init__(self,**keywargs):
            self.mapping = dict()
        def delete(self,index="", ignore=""):
            pass
        def delete_template(self,index=""):
            pass
        def create(self,index="",body={},ignore=""):
            self.mapping[index] = body
        def put_alias(self,index="", name="", ignore=""):
            pass
        def put_template(self,name="", body={}, ignore=""):
            pass
        def refresh(self,index=""):
            pass
        def exists(self, index="", **kwargs):
            if index in self.mapping:
                return True
            else:
                return False
        def flush(self,index="",wait_if_ongoing=""):
            pass
        def delete_alias(self, index="", name="",ignore=""):
            pass
        
        # def search(self,index="",doc_type="",body={},**kwargs):
        #     pass
    class MockCluster():
        def __init__(self,**kwargs):
            pass
        def health(self, wait_for_status="", request_timeout=0):
            pass


@pytest.fixture()
def base_app(request, instance_path,search_class):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SERVER_NAME='app',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
           'SQLALCHEMY_DATABASE_URI',
           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        INDEX_IMG='indextree/36466818-image.jpg',
        SEARCH_UI_SEARCH_INDEX='test-weko',
        WEKO_AUTHORS_ES_INDEX_NAME='test-authors',
        WEKO_AUTHORS_AFFILIATION_IDENTIFIER_ITEM_OTHER=4,
        WEKO_AUTHORS_LIST_SCHEME_AFFILIATION=[
            'ISNI', 'GRID', 'Ringgold', 'kakenhi', 'Other'],
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        SEARCH_ELASTIC_HOSTS=os.environ.get("INVENIO_ELASTICSEARCH_HOST"),
        SEARCH_INDEX_PREFIX="{}-".format('test'),
        SEARCH_CLIENT_CONFIG=dict(timeout=120, max_retries=10),
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioCache(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioIndexer(app_)
    InvenioFilesREST(app_)
    if hasattr(request, 'param'):
        if 'is_es' in request.param:
            search = InvenioSearch(app_)
    else:
        search = InvenioSearch(app_, client=MockEs())
        search.register_mappings(search_class.Meta.index, 'mock_module.mapping')
    WekoTheme(app_)
    WekoAuthors(app_)
    WekoSearchUI(app_)

    # app_.register_blueprint(blueprint)
    app_.register_blueprint(blueprint_api, url_prefix='/api/authors')
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
    # drop_database(str(db_.engine.url))


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client

from invenio_search import current_search_client
@pytest.fixture()
def esindex(app):
    current_search_client.indices.delete(index='test-*')
    with open("tests/mock_module/mapping/v6/authors/author-v1.0.0.json","r") as f:
        mapping = json.load(f)
    with app.test_request_context():
        current_search_client.indices.create("test-authors-author-v1.0.0",body=mapping)
        current_search_client.indices.put_alias(index="test-authors-author-v1.0.0", name=app.config["WEKO_AUTHORS_ES_INDEX_NAME"])

    yield current_search_client

    with app.test_request_context():
        current_search_client.indices.delete_alias(index="test-authors-author-v1.0.0", name=app.config["WEKO_AUTHORS_ES_INDEX_NAME"])
        current_search_client.indices.delete(index="test-authors-author-v1.0.0", ignore=[400, 404])


@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user_count = User.query.filter_by(email='user@test.org').count()
    if user_count != 1:
        user = create_test_user(email='user@test.org')
        contributor = create_test_user(email='contributor@test.org')
        comadmin = create_test_user(email='comadmin@test.org')
        repoadmin = create_test_user(email='repoadmin@test.org')
        sysadmin = create_test_user(email='sysadmin@test.org')
        generaluser = create_test_user(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = create_test_user(email='student@test.org')
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = User.query.filter_by(email='student@test.org').first()
        
    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        repoadmin_role = ds.create_role(name='Repository Administrator')
        contributor_role = ds.create_role(name='Contributor')
        comadmin_role = ds.create_role(name='Community Administrator')
        general_role = ds.create_role(name='General')
        originalrole = ds.create_role(name='Original Role')
        studentrole = ds.create_role(name='Student')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
        contributor_role = Role.query.filter_by(name='Contributor').first()
        comadmin_role = Role.query.filter_by(name='Community Administrator').first()
        general_role = Role.query.filter_by(name='General').first()
        originalrole = Role.query.filter_by(name='Original Role').first()
        studentrole = Role.query.filter_by(name='Student').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)
    ds.add_role_to_user(student,studentrole)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action='superuser-access', role=sysadmin_role),
            ActionRoles(action='admin-access', role=repoadmin_role),
            ActionRoles(action='schema-access', role=repoadmin_role),
            ActionRoles(action='index-tree-access', role=repoadmin_role),
            ActionRoles(action='indextree-journal-access', role=repoadmin_role),
            ActionRoles(action='item-type-access', role=repoadmin_role),
            ActionRoles(action='item-access', role=repoadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=repoadmin_role),
            ActionRoles(action='files-rest-object-read', role=repoadmin_role),
            ActionRoles(action='search-access', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),
            ActionRoles(action='download-original-pdf-access', role=repoadmin_role),
            ActionRoles(action='author-access', role=repoadmin_role),
            ActionRoles(action='items-autofill', role=repoadmin_role),
            ActionRoles(action='stats-api-access', role=repoadmin_role),
            ActionRoles(action='read-style-action', role=repoadmin_role),
            ActionRoles(action='update-style-action', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),

            ActionRoles(action='admin-access', role=comadmin_role),
            ActionRoles(action='index-tree-access', role=comadmin_role),
            ActionRoles(action='indextree-journal-access', role=comadmin_role),
            ActionRoles(action='item-access', role=comadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=comadmin_role),
            ActionRoles(action='files-rest-object-read', role=comadmin_role),
            ActionRoles(action='search-access', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='download-original-pdf-access', role=comadmin_role),
            ActionRoles(action='author-access', role=comadmin_role),
            ActionRoles(action='items-autofill', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),

            ActionRoles(action='item-access', role=contributor_role),
            ActionRoles(action='files-rest-bucket-update', role=contributor_role),
            ActionRoles(action='files-rest-object-delete', role=contributor_role),
            ActionRoles(action='files-rest-object-delete-version', role=contributor_role),
            ActionRoles(action='files-rest-object-read', role=contributor_role),
            ActionRoles(action='search-access', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='download-original-pdf-access', role=contributor_role),
            ActionRoles(action='author-access', role=contributor_role),
            ActionRoles(action='items-autofill', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
        ]
        db.session.add_all(action_roles)
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
    db.session.commit()

    return [
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': generaluser},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
        {'email': student.email,'id': student.id, 'obj': student}
    ]


@pytest.fixture()
def create_author(app, db, esindex):
    def _create_author(data, next_id):
        data["pk_id"] = str(next_id)
        es_data = json.loads(json.dumps(data))
        es_id = uuid.uuid4()
        data["id"] = str(es_id)
        with db.session.begin_nested():
            author = Authors(id=next_id, json=data)
            db.session.add(author)
        db.session.commit()
            
        current_search_client.index(
            index=app.config["WEKO_AUTHORS_ES_INDEX_NAME"],
            doc_type=app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
            id=es_id,
            body=es_data,
            refresh='true')
        return es_id

    # Return new author's id
    return _create_author


def user():
    """Create a example user."""
    return create_test_user(email='test@test.org')


def object_as_dict(obj):
    """Make a dict from SQLAlchemy object."""
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


@pytest.fixture()
def authors(app,db,esindex):
    datas = json_data("data/author.json")
    returns = list()
    for data in datas:
        returns.append(Authors(
            gather_flg=0,
            is_deleted=False,
            json=data
        ))
        es_id = data["id"]
        es_data = json.loads(json.dumps(data))
        es_data["id"]=""
        current_search_client.index(
            index=app.config["WEKO_AUTHORS_ES_INDEX_NAME"],
            doc_type=app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
            id=es_id,
            body=es_data,
            refresh='true')
    
    db.session.add_all(returns)
    db.session.commit()
    return returns


@pytest.fixture()
def location(app,db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc


@pytest.fixture()
def authors_prefix_settings(db):
    apss = list()
    apss.append(AuthorsPrefixSettings(name="WEKO",scheme="WEKO"))
    apss.append(AuthorsPrefixSettings(name="ORCID",scheme="ORCID",url="https://orcid.org/##"))
    apss.append(AuthorsPrefixSettings(name="CiNii",scheme="CiNii",url="https://ci.nii.ac.jp/author/##"))
    apss.append(AuthorsPrefixSettings(name="KAKEN2",scheme="KAKEN2",url="https://nrid.nii.ac.jp/nrid/##"))
    apss.append(AuthorsPrefixSettings(name="ROR",scheme="ROR",url="https://ror.org/##"))
    db.session.add_all(apss)
    db.session.commit()
    return apss

@pytest.fixture()
def authors_affiliation_settings(db):
    aass = list()
    aass.append(AuthorsAffiliationSettings(name="ISNI",scheme="ISNI",url="http://www.isni.org/isni/##"))
    aass.append(AuthorsAffiliationSettings(name="GRID",scheme="GRID",url="https://www.grid.ac/institutes/##"))
    aass.append(AuthorsAffiliationSettings(name="Ringgold",scheme="Ringgold"))
    aass.append(AuthorsAffiliationSettings(name="kakenhi",scheme="kakenhi"))
    db.session.add_all(aass)
    db.session.commit()
    
    return aass

@pytest.fixture()
def file_instance(db):
    file = FileInstance(
        uri="/var/tmp/test_dir",
        storage_class="S",
        size=18,
    )
    db.session.add(file)
    db.session.commit()