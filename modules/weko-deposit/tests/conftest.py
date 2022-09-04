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

import os
import json
import shutil
import tempfile
import copy
import uuid
from unittest.mock import patch
from collections import OrderedDict
from elasticsearch import Elasticsearch
import time

import pytest
from flask import Flask
from flask_menu import Menu
from flask_babelex import Babel
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts.testutils import create_test_user
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB, db as db_
from invenio_cache import InvenioCache
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.views import blueprint as invenio_files_rest_blueprint
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_i18n import InvenioI18N
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_rest.utils import PIDConverter
from invenio_search import InvenioSearch
from invenio_search_ui import InvenioSearchUI
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from six import BytesIO
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from weko_admin import WekoAdmin
from weko_items_ui import WekoItemsUI
from weko_records import WekoRecords
# from weko_records_ui import WekoRecordsUI
from weko_search_ui import WekoSearchUI
from weko_search_ui.config import WEKO_SEARCH_MAX_RESULT
from weko_index_tree import WekoIndexTree, WekoIndexTreeREST

from weko_theme import WekoTheme
from weko_groups import WekoGroups
from invenio_pidrelations.models import PIDRelation

from weko_deposit import WekoDeposit, WekoDepositREST
from weko_deposit.api import WekoRecord
from weko_deposit.views import blueprint
from weko_deposit.api import WekoDeposit as aWekoDeposit,WekoIndexer
from weko_deposit.config import WEKO_BUCKET_QUOTA_SIZE, \
    WEKO_DEPOSIT_REST_ENDPOINTS as _WEKO_DEPOSIT_REST_ENDPOINTS, _PID, DEPOSIT_REST_ENDPOINTS as _DEPOSIT_REST_ENDPOINTS
from weko_index_tree.config import WEKO_INDEX_TREE_REST_ENDPOINTS as _WEKO_INDEX_TREE_REST_ENDPOINTS
from invenio_accounts.testutils import login_user_via_session

@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""

    app_ = Flask('testapp', instance_path=instance_path)
    app_.url_map.converters['pid'] = PIDConverter
    # initialize InvenioDeposit first in order to detect any invalid dependency
    # WEKO_DEPOSIT_REST_ENDPOINTS = copy.deepcopy(_DEPOSIT_REST_ENDPOINTS)
    DEPOSIT_REST_ENDPOINTS = copy.deepcopy(_DEPOSIT_REST_ENDPOINTS)
    WEKO_DEPOSIT_REST_ENDPOINTS= copy.deepcopy(_WEKO_DEPOSIT_REST_ENDPOINTS)
    WEKO_DEPOSIT_REST_ENDPOINTS['depid']['rdc_route'] = '/deposits/redirect/<{0}:pid_value>'.format(_PID)
    WEKO_DEPOSIT_REST_ENDPOINTS['depid']['pub_route'] = '/deposits/publish/<{0}:pid_value>'.format(_PID)
    WEKO_INDEX_TREE_REST_ENDPOINTS = copy.deepcopy(_WEKO_INDEX_TREE_REST_ENDPOINTS)
    WEKO_INDEX_TREE_REST_ENDPOINTS['tid']['index_route'] = '/tree/index/<int:index_id>'

    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND='cache',
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",
        REDIS_PORT='6379',
        JSONSCHEMAS_URL_SCHEME='http',
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI',
        #     'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/invenio'),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        DEPOSIT_SEARCH_API='/api/search',
        SECURITY_PASSWORD_HASH='plaintext',
        SECURITY_PASSWORD_SCHEMES=['plaintext'],
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
        OAUTHLIB_INSECURE_TRANSPORT=True,
        OAUTH2_CACHE_TYPE='simple',
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_INDEX='{}-weko-item-v1.0.0'.format(
            'test'),
        SEARCH_UI_SEARCH_INDEX = "{}-weko".format('test'),
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_DEFAULT_DOC_TYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        WEKO_MAX_FILE_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        INDEX_IMG='indextree/36466818-image.jpg',
        WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
        DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
        WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
        WEKO_INDEX_TREE_STYLE_OPTIONS={
            'id': 'weko',
            'widths': ['1', '2', '3', '4', '5', '6', '7', '8',
                       '9', '10', '11']
        },
        WEKO_INDEX_TREE_UPATED=True,
        WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
        I18N_LANGUAGE=[("ja", "Japanese"), ("en", "English")],
        SERVER_NAME = 'TEST_SERVER',
        SEARCH_ELASTIC_HOSTS = 'elasticsearch',
        SEARCH_INDEX_PREFIX = 'test-'
    )
    # with ESTestServer(timeout=30) as server:
    Babel(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioCache(app_)
    InvenioDB(app_)
    InvenioDeposit(app_)
    InvenioFilesREST(app_)
    InvenioJSONSchemas(app_)
    InvenioIndexer(app_)
    InvenioPIDStore(app_)
    InvenioRecords(app_)
    # client = Elasticsearch(['localhost:%s'%server.port])
    # InvenioSearch(app_, client=client)
    InvenioSearch(app_)
    InvenioSearchUI(app_)
    InvenioPIDRelations(app_)
    InvenioI18N(app_)
    WekoRecords(app_)
    WekoItemsUI(app_)
    # WekoRecordsUI(app_)
    WekoAdmin(app_)
    WekoSearchUI(app_)
    WekoTheme(app_)
    WekoGroups(app_)
    WekoIndexTree(app_)
    WekoIndexTreeREST(app_)
    Menu(app_)
    # app_.register_blueprint(blueprint)
    app_.register_blueprint(invenio_files_rest_blueprint) # invenio_files_rest
    # rest_blueprint = create_blueprint(app_, WEKO_DEPOSIT_REST_ENDPOINTS)
    # app_.register_blueprint(rest_blueprint)
    WekoDeposit(app_)
    WekoDepositREST(app_)
    return app_
    


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with open("tests/data/mappings/item-v1.0.0.json","r") as f:
        mapping = json.load(f)
    es = Elasticsearch("http://{}:9200".format(base_app.config['SEARCH_ELASTIC_HOSTS']))
    es.indices.create(index=base_app.config["INDEXER_DEFAULT_INDEX"],body=mapping,ignore=[400, 404])
    es.indices.put_alias(index=base_app.config["INDEXER_DEFAULT_INDEX"], name=base_app.config['SEARCH_UI_SEARCH_INDEX'], ignore=[400, 404])
    with base_app.app_context():
        yield base_app
    es.indices.delete_alias(index=base_app.config["INDEXER_DEFAULT_INDEX"], name=base_app.config['SEARCH_UI_SEARCH_INDEX'], ignore=[400, 404])
    es.indices.delete(index=base_app.config["INDEXER_DEFAULT_INDEX"], ignore=[400, 404])


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


@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()

    location = Location.query.filter_by(name="testloc").count()
    if location != 1:
        loc = Location(
            name='testloc',
            uri=tmppath,
            default=True
        )
        db.session.add(loc)
        db.session.commit()
    else:
        loc = Location.query.filter_by(name='testloc').first()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def bucket(db, location):
    """File system location."""
    bucket = Bucket.create(location)
    db.session.commit()
    return bucket


@pytest.fixture()
def testfile(db, bucket):
    """File system location."""
    obj = ObjectVersion.create(bucket, 'testfile', stream=BytesIO(b'atest'))
    db.session.commit()
    return obj


@pytest.fixture()
def record(app, db):
    """Create a record."""
    metadata = {
        'title': 'fuu'
    }
    record = WekoRecord.create(metadata)
    record.commit()
    db.session.commit()
    return record


@pytest.fixture()
def generic_file(app, record):
    """Add a generic file to the record."""
    stream = BytesIO(b'test example')
    filename = 'generic_file.txt'
    record.files[filename] = stream
    record.files.dumps()
    record.commit()
    db_.session.commit()
    return filename


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client



@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions["invenio-accounts"].datastore
    user_count = User.query.filter_by(email="user@test.org").count()
    if user_count != 1:
        user = create_test_user(email="user@test.org")
        contributor = create_test_user(email="contributor@test.org")
        comadmin = create_test_user(email="comadmin@test.org")
        repoadmin = create_test_user(email="repoadmin@test.org")
        sysadmin = create_test_user(email="sysadmin@test.org")
        generaluser = create_test_user(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")
    else:
        user = User.query.filter_by(email="user@test.org").first()
        contributor = User.query.filter_by(email="contributor@test.org").first()
        comadmin = User.query.filter_by(email="comadmin@test.org").first()
        repoadmin = User.query.filter_by(email="repoadmin@test.org").first()
        sysadmin = User.query.filter_by(email="sysadmin@test.org").first()
        generaluser = User.query.filter_by(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")

    role_count = Role.query.filter_by(name="System Administrator").count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name="System Administrator")
        repoadmin_role = ds.create_role(name="Repository Administrator")
        contributor_role = ds.create_role(name="Contributor")
        comadmin_role = ds.create_role(name="Community Administrator")
        general_role = ds.create_role(name="General")
        originalrole = ds.create_role(name="Original Role")
    else:
        sysadmin_role = Role.query.filter_by(name="System Administrator").first()
        repoadmin_role = Role.query.filter_by(name="Repository Administrator").first()
        contributor_role = Role.query.filter_by(name="Contributor").first()
        comadmin_role = Role.query.filter_by(name="Community Administrator").first()
        general_role = Role.query.filter_by(name="General").first()
        originalrole = Role.query.filter_by(name="Original Role").first()



    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action="superuser-access", user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action="superuser-access", role=sysadmin_role),
            ActionRoles(action="admin-access", role=repoadmin_role),
            ActionRoles(action="schema-access", role=repoadmin_role),
            ActionRoles(action="index-tree-access", role=repoadmin_role),
            ActionRoles(action="indextree-journal-access", role=repoadmin_role),
            ActionRoles(action="item-type-access", role=repoadmin_role),
            ActionRoles(action="item-access", role=repoadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=repoadmin_role),
            ActionRoles(action="files-rest-object-read", role=repoadmin_role),
            ActionRoles(action="search-access", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),
            ActionRoles(action="download-original-pdf-access", role=repoadmin_role),
            ActionRoles(action="author-access", role=repoadmin_role),
            ActionRoles(action="items-autofill", role=repoadmin_role),
            ActionRoles(action="stats-api-access", role=repoadmin_role),
            ActionRoles(action="read-style-action", role=repoadmin_role),
            ActionRoles(action="update-style-action", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),
            ActionRoles(action="admin-access", role=comadmin_role),
            ActionRoles(action="index-tree-access", role=comadmin_role),
            ActionRoles(action="indextree-journal-access", role=comadmin_role),
            ActionRoles(action="item-access", role=comadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=comadmin_role),
            ActionRoles(action="files-rest-object-read", role=comadmin_role),
            ActionRoles(action="search-access", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="download-original-pdf-access", role=comadmin_role),
            ActionRoles(action="author-access", role=comadmin_role),
            ActionRoles(action="items-autofill", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="item-access", role=contributor_role),
            ActionRoles(action="files-rest-bucket-update", role=contributor_role),
            ActionRoles(action="files-rest-object-delete", role=contributor_role),
            ActionRoles(
                action="files-rest-object-delete-version", role=contributor_role
            ),
            ActionRoles(action="files-rest-object-read", role=contributor_role),
            ActionRoles(action="search-access", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="download-original-pdf-access", role=contributor_role),
            ActionRoles(action="author-access", role=contributor_role),
            ActionRoles(action="items-autofill", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
        ]
        db.session.add_all(action_roles)
        ds.add_role_to_user(sysadmin, sysadmin_role)
        ds.add_role_to_user(repoadmin, repoadmin_role)
        ds.add_role_to_user(contributor, contributor_role)
        ds.add_role_to_user(comadmin, comadmin_role)
        ds.add_role_to_user(generaluser, general_role)
        ds.add_role_to_user(originalroleuser, originalrole)
        ds.add_role_to_user(originalroleuser2, originalrole)
        ds.add_role_to_user(originalroleuser2, repoadmin_role)
        

    return [
        {"email": contributor.email, "id": contributor.id, "obj": contributor},
        {"email": repoadmin.email, "id": repoadmin.id, "obj": repoadmin},
        {"email": sysadmin.email, "id": sysadmin.id, "obj": sysadmin},
        {"email": comadmin.email, "id": comadmin.id, "obj": comadmin},
        {"email": generaluser.email, "id": generaluser.id, "obj": sysadmin},
        {
            "email": originalroleuser.email,
            "id": originalroleuser.id,
            "obj": originalroleuser,
        },
        {
            "email": originalroleuser2.email,
            "id": originalroleuser2.id,
            "obj": originalroleuser2,
        },
        {"email": user.email, "id": user.id, "obj": user},
    ]

@pytest.fixture()
def deposit(app, location):
    bucket = Bucket(default_location=1,
                    default_storage_class='S', size=0,
                    quota_size=app.config['WEKO_BUCKET_QUOTA_SIZE'],
                    max_file_size=app.config['WEKO_MAX_FILE_SIZE'],
                    locked=False, deleted=False, location=location)
    with patch('weko_deposit.api.Bucket.create', return_value=bucket):
        deposit = aWekoDeposit.create({})
        return deposit.pid.pid_value

@pytest.fixture()
def db_index(client,users):
    index_metadata = {
            'id': 1,
            'parent': 0,
            'value': 'Index(public_state = True,harvest_public_state = True)'
        }
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        ret = Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(1)
        index.public_state = True
        index.harvest_public_state = True
    
    index_metadata = {
            'id': 2,
            'parent': 0,
            'value': 'Index(public_state = True,harvest_public_state = False)',
        }
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(2)
        index.public_state = True
        index.harvest_public_state = False
    
    index_metadata = {
            'id': 3,
            'parent': 0,
            'value': 'Index(public_state = False,harvest_public_state = True)',
    }
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(3)
        index.public_state = False
        index.harvest_public_state = True
    
    index_metadata = {
            'id': 4,
            'parent': 0,
            'value': 'Index(public_state = False,harvest_public_state = False)',
    }
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(4)
        index.public_state = False
        index.harvest_public_state = False
    

@pytest.fixture()
def es_records(app,db,db_index):
    
    indexer = WekoIndexer()
    indexer.get_es_index()
    results = []
    with app.test_request_context():
        for i in range(1,10):
            jrc = {'degreeGrantor': {'nameIdentifier': ['xxxxxx'], 'degreeGrantorName': ['Degree Grantor Name']}, 'rightsHolder': {'nameIdentifier': ['xxxxxx'], 'rightsHolderName': ['Right Holder Name']}, 'publisher': ['Publisher'], 'accessRights': ['open access'], 'language': ['jpn'], 'sourceTitle': ['Source Title'], 'dateGranted': ['2021-06-30'], 'relation': {'@attributes': {'relationType': [['isVersionOf']]}, 'relatedTitle': ['Related Title'], 'relatedIdentifier': [{'identifierType': 'arXiv', 'value': 'xxxxx'}]}, 'title': ['ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'en_conference paperITEM00000002(public_open_access_simple)'], 'volume': ['1'], 'alternative': ['Alternative Title', 'Alternative Title'], 'fundingReference': {'awardTitle': ['Award Title'], 'funderName': ['Funder Name'], 'awardNumber': ['Award Number'], 'funderIdentifier': ['http://xxx']}, 'description': [{'descriptionType': 'Abstract', 'value': 'Description\nDescription<br/>Description'}, {'descriptionType': 'Abstract', 'value': '概要\n概要\n概要\n概要'}], 'identifier': [{'identifierType': 'URI', 'value': 'http://localhost'}], 'degreeName': ['Degree Name'], 'versiontype': ['AO'], 'rights': ['Rights Information'], 'version': ['Version'], 'issue': ['111'], 'contributor': {'givenName': ['太郎', 'タロウ', 'Taro'], 'familyName': ['情報', 'ジョウホウ', 'Joho'], '@attributes': {'contributorType': [['ContactPerson']]}, 'affiliation': {'nameIdentifier': [], 'affiliationName': []}, 'nameIdentifier': ['xxxxxxx', 'xxxxxxx', 'xxxxxxx'], 'contributorName': ['情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro'], 'contributorAlternative': []}, 'creator': {'familyName': ['情報', 'ジョウホウ', 'Joho', '情報', 'ジョウホウ', 'Joho', '情報', 'ジョウホウ', 'Joho'], 'creatorAlternative': [], 'affiliation': {'nameIdentifier': ['0000000121691048'], 'affiliationName': ['University']}, 'givenName': ['太郎', 'タロウ', 'Taro', '太郎', 'タロウ', 'Taro', '太郎', 'タロウ', 'Taro'], 'nameIdentifier': ['4', 'xxxxxxx', 'xxxxxxx', 'zzzzzzz', 'xxxxxxx', 'xxxxxxx', 'zzzzzzz', 'xxxxxxx', 'xxxxxxx', 'zzzzzzz'], 'creatorName': ['情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro', '情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro', '情報, 太郎', 'ジョウホウ, タロウ', 'Joho, Taro']}, 'apc': ['Unknown'], 'pageStart': ['1'], 'sourceIdentifier': [{'identifierType': 'ISSN', 'value': 'xxxx-xxxx-xxxx'}], 'type': ['conference paper'], 'geoLocation': {'geoLocationPlace': ['Japan']}, 'file': {'URI': [{'value': 'https://weko3.example.org/record/12/files/1KB.pdf'}], 'date': [{'dateType': 'fileDate.fileDateType'}], 'extent': ['1 KB'], 'version': [], 'mimeType': ['text/plain']}, 'temporal': ['Temporal'], 'pageEnd': ['3'], 'date': [{'dateType': 'Available', 'value': '2021-06-30'}], 'subject': [{'subjectScheme': 'Other', 'value': 'Sibject1'}], 'conference': {'conferenceDate': ['2020/12/11'], 'conferenceName': ['Conference Name'], 'conferenceVenue': ['Conference Venue'], 'conferenceCountry': ['JPN'], 'conferenceSponsor': ['Sponsor'], 'conferenceSequence': ['1']}, 'numPages': ['12'], 'control_number': str(i), '_oai': {'id': 'oai:weko3.example.org:000000{:02d}'.format(i), 'sets': ['{}'.format((i%2)+1)]}, '_item_metadata': OrderedDict([('item_1617186331708', {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'ja_conference paperITEM00000002(public_open_access_open_access_simple)', 'subitem_1551255648112': 'ja'}, {'subitem_1551255647225': 'en_conference paperITEM00000002(public_open_access_simple)', 'subitem_1551255648112': 'en'}]}), ('item_1617186385884', {'attribute_name': 'Alternative Title', 'attribute_value_mlt': [{'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'en'}, {'subitem_1551255720400': 'Alternative Title', 'subitem_1551255721061': 'ja'}]}), ('item_1617186419668', {'attribute_name': 'Creator', 'attribute_type': 'creator', 'attribute_value_mlt': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI', 'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048'}], 'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}]}], 'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '4', 'nameIdentifierScheme': 'WEKO'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}]}), ('item_1617186476635', {'attribute_name': 'Access Rights', 'attribute_value_mlt': [{'subitem_1522299639480': 'open access', 'subitem_1600958577026': 'http://purl.org/coar/access_right/c_abf2'}]}), ('item_1617186499011', {'attribute_name': 'Rights', 'attribute_value_mlt': [{'subitem_1522650717957': 'ja', 'subitem_1522650727486': 'http://localhost', 'subitem_1522651041219': 'Rights Information'}]}), ('item_1617186609386', {'attribute_name': 'Subject', 'attribute_value_mlt': [{'subitem_1522299896455': 'ja', 'subitem_1522300014469': 'Other', 'subitem_1522300048512': 'http://localhost/', 'subitem_1523261968819': 'Sibject1'}]}), ('item_1617186626617', {'attribute_name': 'Description', 'attribute_value_mlt': [{'subitem_description': 'Description\nDescription<br/>Description', 'subitem_description_language': 'en', 'subitem_description_type': 'Abstract'}, {'subitem_description': '概要\n概要\n概要\n概要', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}]}), ('item_1617186643794', {'attribute_name': 'Publisher', 'attribute_value_mlt': [{'subitem_1522300295150': 'en', 'subitem_1522300316516': 'Publisher'}]}), ('item_1617186660861', {'attribute_name': 'Date', 'attribute_value_mlt': [{'subitem_1522300695726': 'Available', 'subitem_1522300722591': '2021-06-30'}]}), ('item_1617186702042', {'attribute_name': 'Language', 'attribute_value_mlt': [{'subitem_1551255818386': 'jpn'}]}), ('item_1617186783814', {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_identifier_type': 'URI', 'subitem_identifier_uri': 'http://localhost'}]}), ('item_1617186859717', {'attribute_name': 'Temporal', 'attribute_value_mlt': [{'subitem_1522658018441': 'en', 'subitem_1522658031721': 'Temporal'}]}), ('item_1617186882738', {'attribute_name': 'Geo Location', 'attribute_value_mlt': [{'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Japan'}]}]}), ('item_1617186901218', {'attribute_name': 'Funding Reference', 'attribute_value_mlt': [{'subitem_1522399143519': {'subitem_1522399281603': 'ISNI', 'subitem_1522399333375': 'http://xxx'}, 'subitem_1522399412622': [{'subitem_1522399416691': 'en', 'subitem_1522737543681': 'Funder Name'}], 'subitem_1522399571623': {'subitem_1522399585738': 'Award URI', 'subitem_1522399628911': 'Award Number'}, 'subitem_1522399651758': [{'subitem_1522721910626': 'en', 'subitem_1522721929892': 'Award Title'}]}]}), ('item_1617186920753', {'attribute_name': 'Source Identifier', 'attribute_value_mlt': [{'subitem_1522646500366': 'ISSN', 'subitem_1522646572813': 'xxxx-xxxx-xxxx'}]}), ('item_1617186941041', {'attribute_name': 'Source Title', 'attribute_value_mlt': [{'subitem_1522650068558': 'en', 'subitem_1522650091861': 'Source Title'}]}), ('item_1617186959569', {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '1'}]}), ('item_1617186981471', {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '111'}]}), ('item_1617186994930', {'attribute_name': 'Number of Pages', 'attribute_value_mlt': [{'subitem_1551256248092': '12'}]}), ('item_1617187024783', {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '1'}]}), ('item_1617187045071', {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '3'}]}), ('item_1617187112279', {'attribute_name': 'Degree Name', 'attribute_value_mlt': [{'subitem_1551256126428': 'Degree Name', 'subitem_1551256129013': 'en'}]}), ('item_1617187136212', {'attribute_name': 'Date Granted', 'attribute_value_mlt': [{'subitem_1551256096004': '2021-06-30'}]}), ('item_1617187187528', {'attribute_name': 'Conference', 'attribute_value_mlt': [{'subitem_1599711633003': [{'subitem_1599711636923': 'Conference Name', 'subitem_1599711645590': 'ja'}], 'subitem_1599711655652': '1', 'subitem_1599711660052': [{'subitem_1599711680082': 'Sponsor', 'subitem_1599711686511': 'ja'}], 'subitem_1599711699392': {'subitem_1599711704251': '2020/12/11', 'subitem_1599711712451': '1', 'subitem_1599711727603': '12', 'subitem_1599711731891': '2000', 'subitem_1599711735410': '1', 'subitem_1599711739022': '12', 'subitem_1599711743722': '2020', 'subitem_1599711745532': 'ja'}, 'subitem_1599711758470': [{'subitem_1599711769260': 'Conference Venue', 'subitem_1599711775943': 'ja'}], 'subitem_1599711788485': [{'subitem_1599711798761': 'Conference Place', 'subitem_1599711803382': 'ja'}], 'subitem_1599711813532': 'JPN'}]}), ('item_1617258105262', {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]}), ('item_1617265215918', {'attribute_name': 'Version Type', 'attribute_value_mlt': [{'subitem_1522305645492': 'AO', 'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}]}), ('item_1617349709064', {'attribute_name': 'Contributor', 'attribute_value_mlt': [{'contributorMails': [{'contributorMail': 'wekosoftware@nii.ac.jp'}], 'contributorNames': [{'contributorName': '情報, 太郎', 'lang': 'ja'}, {'contributorName': 'ジョウホウ, タロウ', 'lang': 'ja-Kana'}, {'contributorName': 'Joho, Taro', 'lang': 'en'}], 'contributorType': 'ContactPerson', 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/'}]}]}), ('item_1617349808926', {'attribute_name': 'Version', 'attribute_value_mlt': [{'subitem_1523263171732': 'Version'}]}), ('item_1617351524846', {'attribute_name': 'APC', 'attribute_value_mlt': [{'subitem_1523260933860': 'Unknown'}]}), ('item_1617353299429', {'attribute_name': 'Relation', 'attribute_value_mlt': [{'subitem_1522306207484': 'isVersionOf', 'subitem_1522306287251': {'subitem_1522306382014': 'arXiv', 'subitem_1522306436033': 'xxxxx'}, 'subitem_1523320863692': [{'subitem_1523320867455': 'en', 'subitem_1523320909613': 'Related Title'}]}]}), ('item_1617605131499', {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain', 'mimetype': 'application/pdf', 'url': {'url': 'https://localhost:8443/record/{}/files/1KB.pdf'.format(i)}, 'version_id': '08725856-0ded-4b39-8231-394a80b297df'}]}), ('item_1617610673286', {'attribute_name': 'Rights Holder', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifier': 'xxxxxx', 'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/'}], 'rightHolderNames': [{'rightHolderLanguage': 'ja', 'rightHolderName': 'Right Holder Name'}]}]}), ('item_1617620223087', {'attribute_name': 'Heading', 'attribute_value_mlt': [{'subitem_1565671149650': 'ja', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheading'}, {'subitem_1565671149650': 'en', 'subitem_1565671169640': 'Banner Headline', 'subitem_1565671178623': 'Subheding'}]}), ('item_1617944105607', {'attribute_name': 'Degree Grantor', 'attribute_value_mlt': [{'subitem_1551256015892': [{'subitem_1551256027296': 'xxxxxx', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': 'Degree Grantor Name', 'subitem_1551256047619': 'en'}]}]}), ('pubdate', {'attribute_name': 'PubDate', 'attribute_value': '2021-08-06'}), ('item_title', 'ja_conference paperITEM00000002(public_open_access_open_access_simple)'), ('item_type_id', '1'), ('control_number', '{}'.format(i)), ('author_link', ['4']), ('weko_shared_id', -1), ('owner', '1'), ('publish_date', '2021-08-06'), ('title', ['ja_conference paperITEM00000002(public_open_access_open_access_simple)']), ('relation_version_is_last', True), ('path', ['{}'.format((i%2)+1)]), ('publish_status', '0')]), 'itemtype': 'デフォルトアイテムタイプ（フル）', 'publish_date': '2021-08-06', 'author_link': ['4'], 'weko_creator_id': '1', 'weko_shared_id': -1, 'path': ['{}'.format((i%2)+1)], 'publish_status': '0', '_created': '2022-08-27T06:05:51.306953+00:00', '_updated': '2022-09-04T06:56:08.339432+00:00', 'content': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': '1KB.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'text/plain', 'mimetype': 'application/pdf', 'url': {'url': 'https://localhost:8443/record/{}/files/1KB.pdf'.format(i)}, 'version_id': '08725856-0ded-4b39-8231-394a80b297df', 'file': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=='}]}
            revision_id=1
            skip_files=False
            record = WekoRecord.create(jrc)
            record.commit()
            item_id = record.id
            recid = PersistentIdentifier.create('recid', jrc["control_number"],object_type='rec', object_uuid=item_id,status=PIDStatus.REGISTERED)
            depid = PersistentIdentifier.create('depid', jrc["control_number"],object_type='rec', object_uuid=item_id,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(recid,depid,3)
            db.session.add(rel)
            parent = PersistentIdentifier.create('parent', "parent:{}".format(jrc["control_number"]),object_type='rec', object_uuid=item_id,status=PIDStatus.REGISTERED)
            rel2 = PIDRelation.create(parent,recid,2,0)
            db.session.add(rel2)
            db.session.commit()
            indexer.upload_metadata(jrc,item_id,revision_id,skip_files)
            results.append({'metadata':jrc,'item_id':item_id,'record':record,'recid':recid,'depid':depid})

    time.sleep(3)
    return indexer, results




