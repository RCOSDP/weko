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

from datetime import datetime, timedelta
import os
import sys
import shutil
import uuid
import json
import tempfile
from invenio_accounts.utils import jwt_create_token
from invenio_oauth2server.ext import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.models import Client, Token
from mock import patch

import pytest
from elasticsearch_dsl import response, Search
from sqlalchemy_utils.functions import create_database, database_exists
from flask import Flask
from flask_babelex import Babel
from flask_menu import Menu

from invenio_i18n import InvenioI18N
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user
from invenio_accounts.models import User, Role
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest.models import Location
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch, current_search_client

from weko_accounts import WekoAccounts
from weko_admin.models import AdminSettings
from weko_deposit import WekoDeposit
from weko_itemtypes_ui import WekoItemtypesUI
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_logging.audit import WekoLoggingUserActivity
from weko_search_ui import WekoSearchUI
from weko_records_ui import WekoRecordsUI
from weko_records_ui.config import WEKO_PERMISSION_SUPER_ROLE_USER, WEKO_PERMISSION_ROLE_COMMUNITY, EMAIL_DISPLAY_FLG

from weko_records import WekoRecords
from weko_records.api import ItemTypes, Mapping
from weko_records.config import WEKO_ITEMTYPE_EXCLUDED_KEYS
from weko_records.models import ItemTypeName, OaStatus, SiteLicenseInfo, FeedbackMailList, ItemReference, ItemTypeProperty, ItemTypeJsonldMapping

from tests.helpers import json_data, create_record

sys.path.append(os.path.dirname(__file__))

@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.logger.setLevel('DEBUG')
    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', 'elasticsearch'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
        JSONSCHEMAS_HOST='inveniosoftware.org',
        THEME_SITEURL="https://localhost",
        WEKO_ITEMTYPE_EXCLUDED_KEYS=WEKO_ITEMTYPE_EXCLUDED_KEYS,
        INDEX_IMG='indextree/36466818-image.jpg',
        SEARCH_UI_SEARCH_INDEX='test-weko',
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format('test'),
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
        WEKO_PERMISSION_ROLE_COMMUNITY=WEKO_PERMISSION_ROLE_COMMUNITY,
        EMAIL_DISPLAY_FLG=EMAIL_DISPLAY_FLG,
        WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME='jpcoar_mapping',
        WEKO_SCHEMA_JPCOAR_V2_NAMEIDSCHEME_REPLACE = {'e-Rad':'e-Rad_Researcher'},
        WEKO_RECORDS_REST_ENDPOINTS = {
            'oa_status_callback': {
                'route': '/<string:version>/oa_status/callback',
                'default_media_type': 'application/json',
            }
        },
        WEKO_RECORDS_API_LIMIT_RATE_DEFAULT = ['100 per minute']
    )

    WekoRecords(app_)
    Babel(app_)
    Menu(app_)
    InvenioI18N(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioDB(app_)
    InvenioJSONSchemas(app_)
    InvenioSearch(app_)
    InvenioIndexer(app_)
    InvenioPIDStore(app_)
    InvenioPIDRelations(app_)
    InvenioRecords(app_)
    InvenioOAuth2Server(app_)
    InvenioOAuth2ServerREST(app_)
    WekoDeposit(app_)
    WekoItemtypesUI(app_)
    WekoLoggingUserActivity(app_)
    WekoSearchUI(app_)
    WekoRecordsUI(app_)
    WekoAccounts(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(headers=[('Accept-Language','en')]):
        yield app

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def location(app):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db_.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db_.session.add(loc)
    db_.session.commit()
    return location


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
    db.session.commit()
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id, group_id=comadmin_role.id)
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
def user():
    """Create a example user."""
    return create_test_user(email='test@test.org')

@pytest.fixture()
def action_data(db):
    from weko_workflow.models import Action, ActionStatus
    action_datas=dict()
    with open('tests/data/actions.json', 'r') as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)
    db.session.commit()

    actionstatus_datas = dict()
    with open('tests/data/action_status.json') as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)
    db.session.commit()
    return actions_db, actionstatus_db

@pytest.fixture()
def db_register(app, db, users, records, action_data, item_type):
    from weko_workflow.models import Action, FlowDefine, FlowAction, WorkFlow, Activity, ActivityAction, ActionFeedbackMail,ActivityHistory
    from datetime import datetime
    from weko_authors.models import Authors
    from weko_admin.models import Identifier

    _pid = records[0][0].object_uuid
    _pid2 = records[1][0].object_uuid
    flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()
    flow_action1 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    with db.session.begin_nested():
        db.session.add(flow_action1)
    db.session.commit()
    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow1',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    activity = Activity(activity_id='1',workflow_id=1, flow_id=flow_define.id,
                item_id=_pid,
                action_id=1, activity_login_user=1,
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test', shared_user_id=-1, extra_info={},
                action_order=1,
                temp_data="{\"metainfo\": {\"pubdate\": \"2025-03-13\", \"item_30002_title0\": \
                [{\"subitem_title\": \"test\", \"subitem_title_language\": \"ja\"}], \
                \"item_30002_alternative_title1\": [{}], \"item_30002_creator2\": \
                [{\"nameIdentifiers\": [{\"nameIdentifier\": \"11\", \"nameIdentifierScheme\":\
                \"WEKO\", \"nameIdentifierURI\": \"\"}], \"creatorNames\": [{\"creatorName\": \
                \"test, jiro\", \"creatorNameLang\": \"ja\"}], \"familyNames\": [{\"familyName\":\
                \"test\", \"familyNameLang\": \"ja\"}], \"givenNames\": [{\"givenName\": \"jiro\", \
                \"givenNameLang\": \"ja\"}], \"creatorAlternatives\": [{}], \"creatorAffiliations\":\
                [{\"affiliationNames\": [], \"affiliationNameIdentifiers\": []}], \"creatorMails\": [{}]},\
                {\"nameIdentifiers\": [{\"nameIdentifierScheme\": \"WEKO\", \"nameIdentifier\": \"111\",\
                \"nameIdentifierURI\": \"\"}, {\"nameIdentifierScheme\": \"ORCID\", \"nameIdentifier\": \"111\", \"nameIdentifierURI\": \"https://orcid.org/111\"}], \"creatorNames\": [{}], \"familyNames\": [{}], \"givenNames\": [{}], \"creatorAlternatives\": [{}], \"creatorAffiliations\": [{\"affiliationNameIdentifiers\": [{}], \"affiliationNames\": [{}]}], \"creatorMails\": [{}]}], \"item_30002_contributor3\": [{\"nameIdentifiers\": [{}], \"contributorNames\": [{}], \"familyNames\": [{}], \"givenNames\": [{}], \"contributorAlternatives\": [{}], \"contributorAffiliations\": [{\"contributorAffiliationNameIdentifiers\": [{}], \"contributorAffiliationNames\": [{}]}], \"contributorMails\": [{}]}], \"item_30002_rights6\": [{}], \"item_30002_rights_holder7\": [{\"nameIdentifiers\": [{}], \"rightHolderNames\": [{}]}], \"item_30002_subject8\": [{}], \"item_30002_description9\": [{}], \"item_30002_publisher10\": [{}], \"item_30002_date11\": [{}], \"item_30002_language12\": [{}], \"item_30002_identifier16\": [{}], \"item_30002_relation18\": [{\"subitem_relation_name\": [{}]}], \"item_30002_temporal19\": [{}], \"item_30002_geolocation20\": [{\"subitem_geolocation_place\": [{}]}], \"item_30002_funding_reference21\": [{\"subitem_funder_names\": [{}], \"subitem_funding_streams\": [{}], \"subitem_award_titles\": [{}]}], \"item_30002_source_identifier22\": [{}], \"item_30002_source_title23\": [{}], \"item_30002_degree_name31\": [{}], \"item_30002_degree_grantor33\": [{\"subitem_degreegrantor_identifier\": [{}], \"subitem_degreegrantor\": [{}]}], \"item_30002_conference34\": [{\"subitem_conference_names\": [{}], \"subitem_conference_sponsors\": [{}], \"subitem_conference_venues\": [{}], \"subitem_conference_places\": [{}]}], \"item_30002_file35\": [{\"filesize\": [{}], \"fileDate\": [{}]}], \"item_30002_heading36\": [{}], \"item_30002_holding_agent_name37\": [{\"holding_agent_names\": [{}]}], \"item_30002_original_language43\": [{}], \"item_30002_dcterms_extent46\": [{\"publisher_names\": [{}], \"publisher_descriptions\": [{}], \"publisher_locations\": [{}], \"publication_places\": [{}]}], \"item_30002_publisher_information45\": [{}], \"item_30002_catalog39\": [{\"catalog_contributors\": [{\"contributor_names\": [{}]}], \"catalog_identifiers\": [{}], \"catalog_titles\": [{}], \"catalog_subjects\": [{}], \"catalog_licenses\": [{}], \"catalog_rights\": [{}], \"catalog_access_rights\": [{}]}], \"item_30002_jpcoar_format40\": [{}], \"item_30002_volume_title44\": [{}], \"item_30002_edition41\": [{}], \"item_30002_dcterms_date38\": [{}], \"item_30002_bibliographic_information29\": {\"bibliographic_titles\": [{}]}, \"item_30002_resource_type13\": {\"resourcetype\": \"data paper\", \"resourceuri\": \"http://purl.org/coar/resource_type/c_beb9\"}, \"shared_user_id\": -1}, \"files\": [], \"endpoints\": {\"initialization\": \"/api/deposits/items\"}, \
                \"weko_link\": {\"1\": \"11\"}}"
                )
    activity_without_weko_link = Activity(activity_id='2',workflow_id=1, flow_id=flow_define.id,
                item_id=_pid2,
                action_id=1, activity_login_user=1,
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test', shared_user_id=-1, extra_info={},
                action_order=1,
                temp_data="{\"metainfo\": {\"pubdate\": \"2025-03-13\", \"item_30002_title0\": \
                [{\"subitem_title\": \"test\", \"subitem_title_language\": \"ja\"}], \
                \"item_30002_alternative_title1\": [{}], \"item_30002_creator2\": \
                [{\"nameIdentifiers\": [{\"nameIdentifier\": \"11\", \"nameIdentifierScheme\":\
                \"WEKO\", \"nameIdentifierURI\": \"\"}], \"creatorNames\": [{\"creatorName\": \
                \"test, jiro\", \"creatorNameLang\": \"ja\"}], \"familyNames\": [{\"familyName\":\
                \"test\", \"familyNameLang\": \"ja\"}], \"givenNames\": [{\"givenName\": \"jiro\", \
                \"givenNameLang\": \"ja\"}], \"creatorAlternatives\": [{}], \"creatorAffiliations\":\
                [{\"affiliationNames\": [], \"affiliationNameIdentifiers\": []}], \"creatorMails\": [{}]},\
                {\"nameIdentifiers\": [{\"nameIdentifierScheme\": \"WEKO\", \"nameIdentifier\": \"111\",\
                \"nameIdentifierURI\": \"\"}, {\"nameIdentifierScheme\": \"ORCID\", \"nameIdentifier\": \"111\", \"nameIdentifierURI\": \"https://orcid.org/111\"}], \"creatorNames\": [{}], \"familyNames\": [{}], \"givenNames\": [{}], \"creatorAlternatives\": [{}], \"creatorAffiliations\": [{\"affiliationNameIdentifiers\": [{}], \"affiliationNames\": [{}]}], \"creatorMails\": [{}]}], \"item_30002_contributor3\": [{\"nameIdentifiers\": [{}], \"contributorNames\": [{}], \"familyNames\": [{}], \"givenNames\": [{}], \"contributorAlternatives\": [{}], \"contributorAffiliations\": [{\"contributorAffiliationNameIdentifiers\": [{}], \"contributorAffiliationNames\": [{}]}], \"contributorMails\": [{}]}], \"item_30002_rights6\": [{}], \"item_30002_rights_holder7\": [{\"nameIdentifiers\": [{}], \"rightHolderNames\": [{}]}], \"item_30002_subject8\": [{}], \"item_30002_description9\": [{}], \"item_30002_publisher10\": [{}], \"item_30002_date11\": [{}], \"item_30002_language12\": [{}], \"item_30002_identifier16\": [{}], \"item_30002_relation18\": [{\"subitem_relation_name\": [{}]}], \"item_30002_temporal19\": [{}], \"item_30002_geolocation20\": [{\"subitem_geolocation_place\": [{}]}], \"item_30002_funding_reference21\": [{\"subitem_funder_names\": [{}], \"subitem_funding_streams\": [{}], \"subitem_award_titles\": [{}]}], \"item_30002_source_identifier22\": [{}], \"item_30002_source_title23\": [{}], \"item_30002_degree_name31\": [{}], \"item_30002_degree_grantor33\": [{\"subitem_degreegrantor_identifier\": [{}], \"subitem_degreegrantor\": [{}]}], \"item_30002_conference34\": [{\"subitem_conference_names\": [{}], \"subitem_conference_sponsors\": [{}], \"subitem_conference_venues\": [{}], \"subitem_conference_places\": [{}]}], \"item_30002_file35\": [{\"filesize\": [{}], \"fileDate\": [{}]}], \"item_30002_heading36\": [{}], \"item_30002_holding_agent_name37\": [{\"holding_agent_names\": [{}]}], \"item_30002_original_language43\": [{}], \"item_30002_dcterms_extent46\": [{\"publisher_names\": [{}], \"publisher_descriptions\": [{}], \"publisher_locations\": [{}], \"publication_places\": [{}]}], \"item_30002_publisher_information45\": [{}], \"item_30002_catalog39\": [{\"catalog_contributors\": [{\"contributor_names\": [{}]}], \"catalog_identifiers\": [{}], \"catalog_titles\": [{}], \"catalog_subjects\": [{}], \"catalog_licenses\": [{}], \"catalog_rights\": [{}], \"catalog_access_rights\": [{}]}], \"item_30002_jpcoar_format40\": [{}], \"item_30002_volume_title44\": [{}], \"item_30002_edition41\": [{}], \"item_30002_dcterms_date38\": [{}], \"item_30002_bibliographic_information29\": {\"bibliographic_titles\": [{}]}, \"item_30002_resource_type13\": {\"resourcetype\": \"data paper\", \"resourceuri\": \"http://purl.org/coar/resource_type/c_beb9\"}, \"shared_user_id\": -1}, \"files\": [], \"endpoints\": {\"initialization\": \"/api/deposits/items\"}}"
                )
    with db.session.begin_nested():
        db.session.add(workflow)
        db.session.add(activity)
        db.session.add(activity_without_weko_link)
    db.session.commit()

    activity_action = ActivityAction(activity_id=activity.activity_id,
                                     action_id=1,action_status="M",
                                     action_handler=1, action_order=1)
    activity_item2_feedbackmail = ActionFeedbackMail(activity_id='3',
                                action_id=3,
                                feedback_maillist=None
                                )
    activity_item3_feedbackmail = ActionFeedbackMail(activity_id='4',
                                action_id=3,
                                feedback_maillist=[{"email": "test@org", "author_id": ""}]
                                )
    activity_item4_feedbackmail = ActionFeedbackMail(activity_id='5',
                                action_id=3,
                                feedback_maillist=[{"email": "test@org", "author_id": "1"}]
                                )
    activity_item5_feedbackmail = ActionFeedbackMail(activity_id='6',
                                action_id=3,
                                feedback_maillist=[{"email": "test1@org", "author_id": "2"}]
                                )
    activity_item5_Authors = Authors(id=1,json={'affiliationInfo': [{'affiliationNameInfo': [{'affiliationName': '', 'affiliationNameLang': 'ja', 'affiliationNameShowFlg': 'true'}], 'identifierInfo': [{'affiliationId': 'aaaa', 'affiliationIdType': '1', 'identifierShowFlg': 'true'}]}], 'authorIdInfo': [{'authorId': '1', 'authorIdShowFlg': 'true', 'idType': '1'}, {'authorId': '1', 'authorIdShowFlg': 'true', 'idType': '2'}], 'authorNameInfo': [{'familyName': '一', 'firstName': '二', 'fullName': '一\u3000二 ', 'language': 'ja-Kana', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'emailInfo': [{'email': 'test@org'}], 'gather_flg': 0, 'id': {'_id': 'HZ9iXYMBnq6bEezA2CK3', '_index': 'tenant1-authors-author-v1.0.0', '_primary_term': 29, '_seq_no': 0, '_shards': {'failed': 0, 'successful': 1, 'total': 2}, '_type': 'author-v1.0.0', '_version': 1, 'result': 'created'}, 'is_deleted': 'false', 'pk_id': '1'})
    activity_item6_feedbackmail = ActionFeedbackMail(activity_id='7',
                                action_id=3,
                                feedback_maillist={"email": "test1@org", "author_id": "2"}
                                )
    with db.session.begin_nested():
        db.session.add(activity_action)
        db.session.add(activity_item2_feedbackmail)
        db.session.add(activity_item3_feedbackmail)
        db.session.add(activity_item4_feedbackmail)
        db.session.add(activity_item5_feedbackmail)
        db.session.add(activity_item5_Authors)
        db.session.add(activity_item6_feedbackmail)
    db.session.commit()

    activity_03 = Activity(activity_id='A-00000003-00000', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item5', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    with db.session.begin_nested():
        db.session.add(activity_03)

    activity_action03_1 = ActivityAction(activity_id=activity_03.activity_id,
                                            action_id=1,action_status="M",action_comment="",
                                            action_handler=1, action_order=1)
    activity_action03_2 = ActivityAction(activity_id=activity_03.activity_id,
                                            action_id=3,action_status="F",action_comment="",
                                            action_handler=0, action_order=2)
    with db.session.begin_nested():
        db.session.add(activity_action03_1)
        db.session.add(activity_action03_2)
    db.session.commit()

    history = ActivityHistory(
        activity_id=activity.activity_id,
        action_id=activity.action_id,
        action_order=activity.action_order,
    )
    with db.session.begin_nested():
        db.session.add(history)
    db.session.commit()
    doi_identifier = Identifier(id=1, repository='Root Index',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
        jalc_doi='123',jalc_crossref_doi='1234',jalc_datacite_doi='12345',ndl_jalc_doi='123456',suffix='def',
        created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
    )
    doi_identifier2 = Identifier(id=2, repository='test',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
        jalc_doi=None,jalc_crossref_doi=None,jalc_datacite_doi=None,ndl_jalc_doi=None,suffix=None,
        created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
        )
    with db.session.begin_nested():
        db.session.add(doi_identifier)
        db.session.add(doi_identifier2)
    db.session.commit()
    return {'flow_define':flow_define,
            'item_type':item_type,
            'workflow':workflow,
            'action_feedback_mail':activity_item3_feedbackmail,
            'action_feedback_mail1':activity_item4_feedbackmail,
            'action_feedback_mail2':activity_item5_feedbackmail,
            'action_feedback_mail3':activity_item6_feedbackmail,
            "activities":[activity]}



@pytest.fixture()
def db_index(app, db):
    index_metadata = {
        'id': 1,
        'parent': 0,
        'value': 'IndexA',
    }
    index_metadata_deleted = {
        'id': 99,
        'parent': 0,
        'value': 'Deleted Index',
    }

    app.config['WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER'] = 5
    with app.app_context():
        user = create_test_user('test@example.org')
        with patch("flask_login.utils._get_user", return_value=user):
            Indexes.create(0, index_metadata)
            Indexes.create(0, index_metadata_deleted)
            Indexes.delete(99, True)
            db.session.commit()


@pytest.fixture()
def esindex(app):
    current_search_client.indices.delete(index="test-*")
    with open("tests/data/item-v1.0.0.json", "r") as f:
        mapping = json.load(f)
    try:
        current_search_client.indices.create(
            "test-weko-item-v1.0.0", body=mapping
        )
        current_search_client.indices.put_alias(
            index="test-weko-item-v1.0.0", name="test-weko"
        )
    except:
        current_search_client.indices.create("test-weko-items", body=mapping)
        current_search_client.indices.put_alias(
            index="test-weko-items", name="test-weko"
        )

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="test-*")


@pytest.fixture()
def item_type(app, db):
    _item_type_name = ItemTypeName(name='test')

    _render = {
        'meta_fix': {},
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {
                        'type': 'string',
                        'title': 'item_1',
                        'format': 'text'
                    }
                }
            }
        },
        'table_row': ['item_1']
    }

    _schema = {
        'properties': {
            'item_1': {
                'type': 'string',
                'title': 'item_1',
                'format': 'text'
            }
        }
    }

    return ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema=_schema,
        render=_render,
        tag=1
    )

@pytest.fixture()
def item_type_mapping(app, db):
    _mapping = {
        'item_1': {
            'jpcoar_mapping': {
                'item': {
                    '@value': 'interim'
                }
            }
        }
    }
    return Mapping.create(1, _mapping)

@pytest.fixture()
def item_type2(app, db):
    _item_type_name = ItemTypeName(name='test2')

    _render = {
        'meta_fix': {},
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {
                        'type': 'string',
                        'title': 'item_1',
                        'format': 'text'
                    }
                }
            }
        },
        'table_row': ['1']
    }

    _schema = {
        'properties': {
            'item_1': {
                'type': 'string',
                'title': 'item_1',
                'format': 'text'
            }
        }
    }

    return ItemTypes.create(
        name='test2',
        item_type_name=_item_type_name,
        schema=_schema,
        render=_render,
        tag=1
    )

@pytest.fixture()
def item_type_mapping2(app, db):
    _mapping = {
        'item_1': {
            'jpcoar_mapping': {
                'item': {
                    '@value': 'interim'
                }
            }
        }
    }
    return Mapping.create(2, _mapping)

@pytest.fixture()
def item_type_property(app, db):
    """Create item type property."""

    _schema = {
        "type": "object",
        "format": "object",
        "properties": {
            "subitem_value": {
                "type": "string",
                "title": "タイトル",
                "format": "text",
            }
        }
    }

    _form = {
        "key": "parentkey",
        "type": "fieldset",
        "items": [
            {
                "key": "parentkey.subitem_value",
                "type": "text",
                "title": "タイトル",
            },
        ],
    }

    _forms = {
        "add": "New",
        "key": "parentkey",
        "items": [
            {
                "key": "parentkey[].subitem_value",
                "type": "text",
                "title": "タイトル",
            },
        ],
        "style": {
            "add": "btn-success"
        },
    }

    item_type_property1 = ItemTypeProperty(
        id = 1000,
        name='title',
        schema=_schema,
        form=_form,
        forms=_forms,
        sort = 1,
    )

    db.session.add(item_type_property1)
    db.session.commit()

    return item_type_property1

@pytest.fixture()
def item_type_with_form(app, db, item_type_property):
    _item_type_name = ItemTypeName(name='test')

    prop_schema = item_type_property.schema
    prop_form = item_type_property.form
    prop_forms = item_type_property.forms

    _default_settings = {
        "isHide": False,
        "required": False,
        "isShowList": False,
        "isNonDisplay": False,
        "isSpecifyNewline": False
    }

    _schema = {
        "type": "object",
        'properties': {
            "pubdate": {
                "type": "string",
                "title": "PubDate",
                "format": "datetime"
            },
            "item_3_form": {
                "type": "array",
                "items": prop_schema,
                "title": "item3",
                "maxItems": 9999,
                "minItems": 1
            },
            "item_4_form": prop_schema,
            "item_5_form": {
                "type": "array",
                "items": prop_schema,
                "title": "item5",
                "properties": {},
                "format": "sample",
            },
        }
    }

    form_item3 = json.loads(json.dumps(prop_forms, ensure_ascii=False).replace("parentkey", "item_3_form"))
    form_item3.update(_default_settings)
    [props.update(_default_settings) for props in form_item3['items']]

    form_item4 = json.loads(json.dumps(prop_form, ensure_ascii=False).replace("parentkey", "item_4_form"))
    form_item4.update(_default_settings)
    [props.update(_default_settings) for props in form_item4['items']]

    form_item5 = json.loads(json.dumps(prop_forms, ensure_ascii=False).replace("parentkey", "item_5_form"))
    form_item5.update(_default_settings)
    [props.update(_default_settings) for props in form_item3['items']]

    _form = [
        {
            "key": "pubdate",
            "type": "template",
            "title": "PubDate",
            "format": "yyyy-MM-dd",
            "required": True,
            "title_i18n": {
                "en": "PubDate",
                "ja": "公開日"
            },
            "templateUrl": "/static/templates/weko_deposit/datepicker.html"
        },
        form_item3,
        form_item4,
    ]

    _render = {
        'meta_fix': {},
        'meta_list': {
            "item_3_form": {
                "title": "Title",
                "option": {
                    "crtf": True,
                    "hidden": False,
                    "multiple": True,
                    "required": True,
                    "showlist": True
                },
                "input_type": "cus_1000",
                "title_i18n": {
                    "en": "Title",
                    "ja": "タイトル"
                },
                "input_value": "",
                "input_maxItems": "9999",
                "input_minItems": "1"
            },
            "item_4_form": {
                "title": "Title2",
                "option": {
                    "crtf": True,
                    "hidden": False,
                    "multiple": False,
                    "required": True,
                    "showlist": True
                },
                "input_type": "cus_1000",
                "title_i18n": {
                    "en": "Title2",
                    "ja": "タイトル2"
                },
                "input_value": "",
                "input_maxItems": "9999",
                "input_minItems": "1"
            },
            "item_5_form": {
                "title": "Title",
                "option": {
                    "crtf": True,
                    "hidden": False,
                    "multiple": True,
                    "required": True,
                    "showlist": True
                },
                "input_type": "cus_1000",
                "title_i18n": {
                    "en": "Title3",
                    "ja": "タイトル3"
                },
                "input_value": "",
                "input_maxItems": "9999",
                "input_minItems": "1"
            },
        },
        'table_row_map': {
            'schema': _schema
        },
        'table_row': ['item_1', 'item_2'],
        "table_row_map": {
            "schema": _schema,
            "form": _form
        },
        "schemaeditor": {
            "schema": _schema,
        }
    }

    return ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema=_schema,
        form=_form,
        render=_render,
        tag=1
    )

@pytest.fixture()
def item_type_mapping_with_form(app, db, item_type_with_form):
    _mapping = {
        'item_1': {
            'jpcoar_mapping': {
                'item': {
                    '@value': 'interim'
                }
            }
        }
    }
    return Mapping.create(item_type_with_form.id, _mapping)


@pytest.fixture()
def mock_execute():
    def factory(data):
        if isinstance(data, str):
            data = json_data(data)
        dummy = response.Response(Search(), data)
        return dummy
    return factory


@pytest.fixture()
def records(db):
    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()
    yield result


@pytest.fixture()
def admin_settings(app, db):
    setting = AdminSettings(
        name="items_display_settings",
        settings={"items_display_email": True, "items_search_author": "name"}
    )

    with db.session.begin_nested():
        db.session.add(setting)


@pytest.fixture()
def site_license_info(app, db):
    record = SiteLicenseInfo(
        organization_id=1,
        organization_name='test',
        domain_name='domain',
        mail_address='nii@nii.co.jp',
        receive_mail_flag='F')
    with db.session.begin_nested():
        db.session.add(record)
    return record

@pytest.fixture
def identifiers():
    identifier = ['oai:weko3.example.org:00000965']
    return identifiers

@pytest.fixture
def k_v():
    k_v = [
        {
            'id': 'date_range1',
            'mapping': [],
            'contents': '',
            'inputType': 'dateRange',
            'input_Type': 'range',
            'item_value': {
                '1': {
                    'path': {'gte': '', 'lte': ''},
                    'path_type': {'gte': 'json', 'lte': 'json'}
                },
                '12': {
                    'path': {
                        'gte': '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211',
                        'lte': '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211'
                    },
                    'path_type': {'gte': 'json', 'lte': 'json'}
                }
            },
            'mappingFlg': False,
            'inputVal_to': '',
            'mappingName': '',
            'inputVal_from': '',
            'contents_value': {'en': 'date_EN_1', 'ja': 'date_JA_1'},
            'useable_status': True,
            'default_display': True
        },
        {
            "id": "text3",
            "mapping": [],
            "contents": "",
            "inputVal": "",
            "inputType": "text",
            "input_Type": "text",
            "item_value":  {
                "1": {
                    "path": "",
                    "path_type": "json"
                },
                "12": {
                    "path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890",
                    "path_type": "json"
                },
                "20": {
                    "path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890",
                    "path_type": "json"
                }
            },
            "mappingFlg": False,
            "mappingName": "",
            "contents_value": {"en": "Summary", "ja": "概要"},
            "useable_status": True,
            "default_display": True
        }
    ]
    return k_v

@pytest.fixture
def jsonpath():
    return [
        '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108',
        '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211',
        '$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890',
        '$.item_1551264846237.attribute_value_mlt[1:3].subitem_1551255577890'
    ]

@pytest.fixture
def meta():
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "meta00.json"
    )
    with open(filepath, encoding="utf-8") as f:
            input_data = json.load(f)
    return input_data

@pytest.fixture
def db_ItemReference(db):
    ir = ItemReference(
        src_item_pid="1",
        dst_item_pid="2",
        reference_type="reference_type"
    )
    with db.session.begin_nested():
        db.session.add(ir)

    return ir

@pytest.fixture
def k_v_with_c():
    k_v_with_c = [
        {
            "id": "date_range1",
            "mapping": [],
            "contents": "",
            "inputType": "dateRange",
            "input_Type": "range",
            "item_value": {
            "1": {
                "path": {
                "gte": "",
                "lte": ""
                },
                "path_type": {
                "gte": "json",
                "lte": "json"
                }
            },
            "12": {
                "path": {
                "gte": "$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211",
                "lte": "$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211"
                },
                "path_type": {
                "gte": "json",
                "lte": "json"
                }
            },
            "20": {
                "path": {
                "gte": "$.item_1602145192334.attribute_value_mlt[1].subitem_1602144573160",
                "lte": "$.item_1602145192334.attribute_value_mlt[0].subitem_1602144573160"
                },
                "path_type": {
                "gte": "json",
                "lte": "json"
                }
            }
            },
            "mappingFlg": False,
            "inputVal_to": "",
            "mappingName": "",
            "inputVal_from": "",
            "contents_value": {
            "en": "Time Period(s)",
            "ja": "対象時期"
            },
            "useable_status": True,
            "default_display": True
        },
        {
            "id": "text1",
            "mapping": [],
            "contents": "",
            "inputVal": "",
            "inputType": "text",
            "input_Type": "text",
            "item_value": {
            "1": {
                "path": "aaaa",
                "path_type": "json",
                "condition_path": "TEST",
                "condition_value": "TEST"
            },
            "12": {
                "path": "$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108",
                "path_type": "json",
                "condition_path": "$.item_1551264418667.attribute_value_mlt[*].subitem_1551257036415",
                "condition_value": "Distributor"
            },
            "20": {
                "path": "",
                "path_type": "json"
            }
            },
            "mappingFlg": False,
            "mappingName": "",
            "contents_value": {
            "en": "Distributor",
            "ja": "配布者"
            },
            "useable_status": True,
            "default_display": True
        },
        {
            "id": "text3",
            "mapping": [],
            "contents": "",
            "inputVal": "",
            "inputType": "text",
            "input_Type": "text",
            "item_value": {
            "1": {
                "path": "",
                "path_type": "json"
            },
            "12": {
                "path": "$.item_1636460428217.attribute_value_mlt[*].subitem_1522657697257",
                "path_type": "json",
                "condition_path": "$.item_1636460428217.attribute_value_mlt[*].subitem_1522657647525",
                "condition_value": "Abstract"
            },
            "20": {
                "path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890",
                "path_type": "json"
            }
            },
            "mappingFlg": False,
            "mappingName": "",
            "contents_value": {
            "en": "Summary",
            "ja": "概要"
            },
            "useable_status": True,
            "default_display": True
        },
        {
            "id": "text10",
            "mapping": [],
            "contents": "",
            "inputVal": "",
            "inputType": "text",
            "input_Type": "text",
            "item_value": {
            "1": {
                "path": "",
                "path_type": "json"
            },
            "12": {
                "path": "$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108",
                "path_type": "json",
                "condition_path": "$.item_1551264418667.attribute_value_mlt[*].subitem_1551257036415",
                "condition_value": "Other"
            },
            "20": {
                "path": "$.item_1602147887655.attribute_value_mlt[*].subitem_1602143328410",
                "path_type": "json"
            }
            },
            "mappingFlg": False,
            "mappingName": "",
            "contents_value": {
            "en": "Provider",
            "ja": "所蔵者・寄託者"
            },
            "useable_status": True,
            "default_display": True
        },
        {
            "id": "text11",
            "mapping": [],
            "contents": "",
            "inputVal": "",
            "inputType": "text",
            "input_Type": "text",
            "item_value": {
            "1": {
                "path": "",
                "path_type": "json"
            },
            "12": {
                "path": "$.item_1636460428217.attribute_value_mlt[*].subitem_1522657697257",
                "path_type": "json",
                "condition_path": "$.item_1636460428217.attribute_value_mlt[*].subitem_1522657647525",
                "condition_value": "Other"
            },
            "20": {
                "path": "$.item_1588260046718.attribute_value_mlt[*].subitem_1591178807921",
                "path_type": "json"
            }
            },
            "mappingFlg": False,
            "mappingName": "",
            "contents_value": {
            "en": "Data Type",
            "ja": "データタイプ"
            },
            "useable_status": False,
            "default_display": False
        }
    ]
    return k_v_with_c

@pytest.fixture
def meta01():
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "data",
        "meta01.json"
    )
    with open(filepath, encoding="utf-8") as f:
            input_data = json.load(f)
    return input_data

@pytest.fixture
def db_OaStatus(db):
    oa_status = OaStatus(
        oa_article_id=1,
        oa_status="Unprocessed",
        weko_item_pid="20000001"
    )
    with db.session.begin_nested():
        db.session.add(oa_status)

    return oa_status

@pytest.fixture
def tokens(app,users,db):
    scopes = [
        "oa_status:update",
        ""
    ]
    tokens = []

    for i, scope in enumerate(scopes):
        user = users[i]
        user_id = str(user["id"])

        test_client = Client(
            client_id=f"dev{user_id}",
            client_secret=f"dev{user_id}",
            name="Test name",
            description="test description",
            is_confidential=False,
            user_id=user_id,
            _default_scopes="deposit:write"
        )
        test_token = Token(
            client=test_client,
            user_id=user_id,
            token_type="bearer",
            access_token=jwt_create_token(user_id=user_id),
            expires=datetime.now() + timedelta(hours=10),
            is_personal=False,
            is_internal=True,
            _scopes=scope
        )

        db.session.add(test_client)
        db.session.add(test_token)

        tokens.append({"token":test_token, "client":test_client, "scope":scope})

    db.session.commit()

    return tokens


@pytest.fixture
def sword_mapping(db, item_type):
    sword_mapping = []
    for i in range(1, 4):
        obj = ItemTypeJsonldMapping(
            name=f"test{i}",
            mapping=json_data("data/jsonld_mapping.json"),
            item_type_id=item_type.model.id,
            is_deleted=False
        )
        with db.session.begin_nested():
            db.session.add(obj)

        sword_mapping.append({
            "id": obj.id,
            "sword_mapping": obj,
            "name": obj.name,
            "mapping": obj.mapping,
            "item_type_id": obj.item_type_id,
            "version_id": obj.version_id,
            "is_deleted": obj.is_deleted
        })

    db.session.commit()

    return sword_mapping
