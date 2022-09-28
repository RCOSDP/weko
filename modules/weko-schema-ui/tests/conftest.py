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

import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from os.path import dirname, exists, join

import pytest
from click.testing import CliRunner
from flask import Blueprint, Flask
from flask_assets import assets
from flask_babelex import Babel
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_accounts.views.settings import blueprint as invenio_accounts_blueprint
from invenio_admin import InvenioAdmin
from invenio_admin.views import blueprint as invenio_admin_blueprint
from invenio_assets import InvenioAssets
from invenio_assets.cli import collect, npm
from invenio_cache import InvenioCache
from invenio_communities import InvenioCommunities
from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_rest import InvenioREST
from invenio_stats import InvenioStats
from invenio_theme import InvenioTheme
from sqlalchemy_utils.functions import create_database, database_exists
from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime
from weko_deposit import WekoDeposit
from weko_index_tree import WekoIndexTree
from weko_items_ui import WekoItemsUI
from weko_items_ui.views import blueprint as weko_items_ui_blueprint
from weko_items_ui.views import blueprint_api as weko_items_ui_blueprint_api
from weko_records import WekoRecords
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_records_ui import WekoRecordsUI
from weko_search_ui import WekoSearchREST, WekoSearchUI
from weko_theme import WekoTheme
from weko_theme.views import blueprint as weko_theme_blueprint
from weko_user_profiles.models import UserProfile
from weko_workflow import WekoWorkflow
from weko_workflow.models import Action, ActionStatus, Activity, FlowAction, FlowDefine, WorkFlow
from weko_workflow.views import workflow_blueprint as weko_workflow_blueprint
from werkzeug.local import LocalProxy

from tests.helpers import create_record, json_data

# from weko_schema_ui import WekoSchemaREST
from weko_schema_ui.rest import create_blueprint
from weko_schema_ui.models import OAIServerSchema


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
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_TYPE = 'redis' ,
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST = os.environ.get('INVENIO_REDIS_HOST'),
        REDIS_PORT = '6379',
        WEKO_SCHEMA_CACHE_PREFIX = 'cache_{schema_name}',
        WEKO_SCHEMA_REST_ENDPOINTS = {
            'depid': {
                'pid_type': 'depid',
                'pid_minter': 'deposit',
                'pid_fetcher': 'deposit',
                'record_class': 'weko_schema_ui.api:WekoSchema',
                'record_serializers': {
                    'application/json': ('invenio_records_rest.serializers'
                                         ':json_v1_response'),
                },
                'schemas_route': '/schemas/',
                'schema_route': '/schemas/<pid_value>',
                'schemas_put_route': '/schemas/put/<pid_value>/<path:key>',
                # 'schemas_formats_route': '/schemas/formats/',
                'default_media_type': 'application/json',
                'max_result_window': 10000,
            },
        },
        WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER = '{0}/data/xsd/'
    )
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioDB(app_)
    InvenioCache(app_)
    InvenioPIDStore(app_)
    Babel(app_)
    
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def client_rest(app):
    app.register_blueprint(create_blueprint(app.config['WEKO_SCHEMA_REST_ENDPOINTS']))
    with app.test_client() as client:
        yield client


@pytest.fixture()
def db(app):
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()



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
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')

    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        repoadmin_role = ds.create_role(name='Repository Administrator')
        contributor_role = ds.create_role(name='Contributor')
        comadmin_role = ds.create_role(name='Community Administrator')
        general_role = ds.create_role(name='General')
        originalrole = ds.create_role(name='Original Role')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
        contributor_role = Role.query.filter_by(name='Contributor').first()
        comadmin_role = Role.query.filter_by(name='Community Administrator').first()
        general_role = Role.query.filter_by(name='General').first()
        originalrole = Role.query.filter_by(name='Original Role').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)
    
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
        
    return [
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': sysadmin},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
    ]

@pytest.fixture()
def db_oaischema(app, db):
    schema_name='jpcoar_mapping'
    form_data={"name": "jpcoar", "file_name": "jpcoar_scm.xsd", "root_name": "jpcoar"}
    xsd = "{\"dc:title\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 1, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"dcterms:alternative\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:creator\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"jpcoar:nameIdentifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"nameIdentifierScheme\", \"ref\": null, \"restriction\": {\"enumeration\": [\"e-Rad\", \"NRID\", \"ORCID\", \"ISNI\", \"VIAF\", \"AID\", \"kakenhi\", \"Ringgold\", \"GRID\"]}}, {\"use\": \"optional\", \"name\": \"nameIdentifierURI\", \"ref\": null}]}}, \"jpcoar:creatorName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:familyName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:givenName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:creatorAlternative\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:affiliation\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"jpcoar:nameIdentifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"nameIdentifierScheme\", \"ref\": null, \"restriction\": {\"enumeration\": [\"e-Rad\", \"NRID\", \"ORCID\", \"ISNI\", \"VIAF\", \"AID\", \"kakenhi\", \"Ringgold\", \"GRID\"]}}, {\"use\": \"optional\", \"name\": \"nameIdentifierURI\", \"ref\": null}]}}, \"jpcoar:affiliationName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}}}, \"jpcoar:contributor\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"contributorType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"ContactPerson\", \"DataCollector\", \"DataCurator\", \"DataManager\", \"Distributor\", \"Editor\", \"HostingInstitution\", \"Producer\", \"ProjectLeader\", \"ProjectManager\", \"ProjectMember\", \"RegistrationAgency\", \"RegistrationAuthority\", \"RelatedPerson\", \"Researcher\", \"ResearchGroup\", \"Sponsor\", \"Supervisor\", \"WorkPackageLeader\", \"Other\"]}}]}, \"jpcoar:nameIdentifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"nameIdentifierScheme\", \"ref\": null, \"restriction\": {\"enumeration\": [\"e-Rad\", \"NRID\", \"ORCID\", \"ISNI\", \"VIAF\", \"AID\", \"kakenhi\", \"Ringgold\", \"GRID\"]}}, {\"use\": \"optional\", \"name\": \"nameIdentifierURI\", \"ref\": null}]}}, \"jpcoar:contributorName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:familyName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:givenName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:contributorAlternative\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:affiliation\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"jpcoar:nameIdentifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"nameIdentifierScheme\", \"ref\": null, \"restriction\": {\"enumeration\": [\"e-Rad\", \"NRID\", \"ORCID\", \"ISNI\", \"VIAF\", \"AID\", \"kakenhi\", \"Ringgold\", \"GRID\"]}}, {\"use\": \"optional\", \"name\": \"nameIdentifierURI\", \"ref\": null}]}}, \"jpcoar:affiliationName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}}}, \"dcterms:accessRights\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"rdf:resource\", \"ref\": \"rdf:resource\"}], \"restriction\": {\"enumeration\": [\"embargoed access\", \"metadata only access\", \"open access\", \"restricted access\"]}}}, \"rioxxterms:apc\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"restriction\": {\"enumeration\": [\"Paid\", \"Partially waived\", \"Fully waived\", \"Not charged\", \"Not required\", \"Unknown\"]}}}, \"dc:rights\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"rdf:resource\", \"ref\": \"rdf:resource\"}, {\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:rightsHolder\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"jpcoar:nameIdentifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"nameIdentifierScheme\", \"ref\": null, \"restriction\": {\"enumeration\": [\"e-Rad\", \"NRID\", \"ORCID\", \"ISNI\", \"VIAF\", \"AID\", \"kakenhi\", \"Ringgold\", \"GRID\"]}}, {\"use\": \"optional\", \"name\": \"nameIdentifierURI\", \"ref\": null}]}}, \"jpcoar:rightsHolderName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}}, \"jpcoar:subject\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}, {\"use\": \"optional\", \"name\": \"subjectURI\", \"ref\": null}, {\"use\": \"required\", \"name\": \"subjectScheme\", \"ref\": null, \"restriction\": {\"enumeration\": [\"BSH\", \"DDC\", \"LCC\", \"LCSH\", \"MeSH\", \"NDC\", \"NDLC\", \"NDLSH\", \"Sci-Val\", \"UDC\", \"Other\"]}}]}}, \"datacite:description\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}, {\"use\": \"required\", \"name\": \"descriptionType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"Abstract\", \"Methods\", \"TableOfContents\", \"TechnicalInfo\", \"Other\"]}}]}}, \"dc:publisher\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"datacite:date\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"dateType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"Accepted\", \"Available\", \"Collected\", \"Copyrighted\", \"Created\", \"Issued\", \"Submitted\", \"Updated\", \"Valid\"]}}]}}, \"dc:language\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"restriction\": {\"patterns\": [\"^[a-z]{3}$\"]}}}, \"dc:type\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 1, \"attributes\": [{\"use\": \"required\", \"name\": \"rdf:resource\", \"ref\": \"rdf:resource\"}], \"restriction\": {\"enumeration\": [\"conference paper\", \"data paper\", \"departmental bulletin paper\", \"editorial\", \"journal article\", \"newspaper\", \"periodical\", \"review article\", \"software paper\", \"article\", \"book\", \"book part\", \"cartographic material\", \"map\", \"conference object\", \"conference proceedings\", \"conference poster\", \"dataset\", \"aggregated data\", \"clinical trial data\", \"compiled data\", \"encoded data\", \"experimental data\", \"genomic data\", \"geospatial data\", \"laboratory notebook\", \"measurement and test data\", \"observational data\", \"recorded data\", \"simulation data\", \"survey data\", \"interview\", \"image\", \"still image\", \"moving image\", \"video\", \"lecture\", \"patent\", \"internal report\", \"report\", \"research report\", \"technical report\", \"policy report\", \"report part\", \"working paper\", \"data management plan\", \"sound\", \"thesis\", \"bachelor thesis\", \"master thesis\", \"doctoral thesis\", \"interactive resource\", \"learning object\", \"manuscript\", \"musical notation\", \"research proposal\", \"software\", \"technical documentation\", \"workflow\", \"other\"]}}}, \"datacite:version\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"oaire:versiontype\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"rdf:resource\", \"ref\": \"rdf:resource\"}], \"restriction\": {\"enumeration\": [\"AO\", \"SMUR\", \"AM\", \"P\", \"VoR\", \"CVoR\", \"EVoR\", \"NA\"]}}}, \"jpcoar:identifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"identifierType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"DOI\", \"HDL\", \"URI\"]}}]}}, \"jpcoar:identifierRegistration\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"identifierType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"JaLC\", \"Crossref\", \"DataCite\", \"PMID\"]}}]}}, \"jpcoar:relation\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"relationType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"isVersionOf\", \"hasVersion\", \"isPartOf\", \"hasPart\", \"isReferencedBy\", \"references\", \"isFormatOf\", \"hasFormat\", \"isReplacedBy\", \"replaces\", \"isRequiredBy\", \"requires\", \"isSupplementTo\", \"isSupplementedBy\", \"isIdenticalTo\", \"isDerivedFrom\", \"isSourceOf\"]}}]}, \"jpcoar:relatedIdentifier\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"identifierType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"ARK\", \"arXiv\", \"DOI\", \"HDL\", \"ICHUSHI\", \"ISBN\", \"J-GLOBAL\", \"Local\", \"PISSN\", \"EISSN\", \"NAID\", \"PMID\", \"PURL\", \"SCOPUS\", \"URI\", \"WOS\"]}}]}}, \"jpcoar:relatedTitle\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}}, \"dcterms:temporal\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"datacite:geoLocation\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"datacite:geoLocationPoint\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}, \"datacite:pointLongitude\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 1, \"restriction\": {\"maxInclusive\": 180, \"minInclusive\": -180}}}, \"datacite:pointLatitude\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 1, \"restriction\": {\"maxInclusive\": 90, \"minInclusive\": -90}}}}, \"datacite:geoLocationBox\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}, \"datacite:westBoundLongitude\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 1, \"restriction\": {\"maxInclusive\": 180, \"minInclusive\": -180}}}, \"datacite:eastBoundLongitude\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 1, \"restriction\": {\"maxInclusive\": 180, \"minInclusive\": -180}}}, \"datacite:southBoundLatitude\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 1, \"restriction\": {\"maxInclusive\": 90, \"minInclusive\": -90}}}, \"datacite:northBoundLatitude\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 1, \"restriction\": {\"maxInclusive\": 90, \"minInclusive\": -90}}}}, \"datacite:geoLocationPlace\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}}}, \"jpcoar:fundingReference\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"datacite:funderIdentifier\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"funderIdentifierType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"Crossref Funder\", \"GRID\", \"ISNI\", \"Other\"]}}]}}, \"jpcoar:funderName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 1, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"datacite:awardNumber\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"awardURI\", \"ref\": null}]}}, \"jpcoar:awardTitle\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}}, \"jpcoar:sourceIdentifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"identifierType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"PISSN\", \"EISSN\", \"ISSN\", \"NCID\"]}}]}}, \"jpcoar:sourceTitle\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:volume\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"jpcoar:issue\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"jpcoar:numPages\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"jpcoar:pageStart\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"jpcoar:pageEnd\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"dcndl:dissertationNumber\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"dcndl:degreeName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"dcndl:dateGranted\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"jpcoar:degreeGrantor\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"jpcoar:nameIdentifier\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"nameIdentifierScheme\", \"ref\": null, \"restriction\": {\"enumeration\": [\"e-Rad\", \"NRID\", \"ORCID\", \"ISNI\", \"VIAF\", \"AID\", \"kakenhi\", \"Ringgold\", \"GRID\"]}}, {\"use\": \"optional\", \"name\": \"nameIdentifierURI\", \"ref\": null}]}}, \"jpcoar:degreeGrantorName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}}, \"jpcoar:conference\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"jpcoar:conferenceName\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:conferenceSequence\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"jpcoar:conferenceSponsor\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:conferenceDate\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"startMonth\", \"ref\": null, \"restriction\": {\"maxInclusive\": 12, \"minInclusive\": 1, \"totalDigits\": 2}}, {\"use\": \"optional\", \"name\": \"endYear\", \"ref\": null, \"restriction\": {\"maxInclusive\": 2200, \"minInclusive\": 1400, \"totalDigits\": 4}}, {\"use\": \"optional\", \"name\": \"startDay\", \"ref\": null, \"restriction\": {\"maxInclusive\": 31, \"minInclusive\": 1, \"totalDigits\": 2}}, {\"use\": \"optional\", \"name\": \"endDay\", \"ref\": null, \"restriction\": {\"maxInclusive\": 31, \"minInclusive\": 1, \"totalDigits\": 2}}, {\"use\": \"optional\", \"name\": \"endMonth\", \"ref\": null, \"restriction\": {\"maxInclusive\": 12, \"minInclusive\": 1, \"totalDigits\": 2}}, {\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}, {\"use\": \"optional\", \"name\": \"startYear\", \"ref\": null, \"restriction\": {\"maxInclusive\": 2200, \"minInclusive\": 1400, \"totalDigits\": 4}}]}}, \"jpcoar:conferenceVenue\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:conferencePlace\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"xml:lang\", \"ref\": \"xml:lang\"}]}}, \"jpcoar:conferenceCountry\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"restriction\": {\"patterns\": [\"^[A-Z]{3}$\"]}}}}, \"jpcoar:file\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}, \"jpcoar:URI\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0, \"attributes\": [{\"use\": \"optional\", \"name\": \"label\", \"ref\": null}, {\"use\": \"optional\", \"name\": \"objectType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"abstract\", \"dataset\", \"fulltext\", \"software\", \"summary\", \"thumbnail\", \"other\"]}}]}}, \"jpcoar:mimeType\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}, \"jpcoar:extent\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0}}, \"datacite:date\": {\"type\": {\"maxOccurs\": \"unbounded\", \"minOccurs\": 0, \"attributes\": [{\"use\": \"required\", \"name\": \"dateType\", \"ref\": null, \"restriction\": {\"enumeration\": [\"Accepted\", \"Available\", \"Collected\", \"Copyrighted\", \"Created\", \"Issued\", \"Submitted\", \"Updated\", \"Valid\"]}}]}}, \"datacite:version\": {\"type\": {\"maxOccurs\": 1, \"minOccurs\": 0}}}, \"custom:system_file\": {\"type\": {\"minOccurs\": 0, \"maxOccurs\": \"unbounded\"}, \"jpcoar:URI\": {\"type\": {\"minOccurs\": 0, \"maxOccurs\": 1, \"attributes\": [{\"name\": \"objectType\", \"ref\": null, \"use\": \"optional\", \"restriction\": {\"enumeration\": [\"abstract\", \"summary\", \"fulltext\", \"thumbnail\", \"other\"]}}, {\"name\": \"label\", \"ref\": null, \"use\": \"optional\"}]}}, \"jpcoar:mimeType\": {\"type\": {\"minOccurs\": 0, \"maxOccurs\": 1}}, \"jpcoar:extent\": {\"type\": {\"minOccurs\": 0, \"maxOccurs\": \"unbounded\"}}, \"datacite:date\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": \"unbounded\", \"attributes\": [{\"name\": \"dateType\", \"ref\": null, \"use\": \"required\", \"restriction\": {\"enumeration\": [\"Accepted\", \"Available\", \"Collected\", \"Copyrighted\", \"Created\", \"Issued\", \"Submitted\", \"Updated\", \"Valid\"]}}]}}, \"datacite:version\": {\"type\": {\"minOccurs\": 0, \"maxOccurs\": 1}}}}"
    namespaces={"": "https://github.com/JPCOAR/schema/blob/master/1.0/", "dc": "http://purl.org/dc/elements/1.1/", "xs": "http://www.w3.org/2001/XMLSchema", "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "xml": "http://www.w3.org/XML/1998/namespace", "dcndl": "http://ndl.go.jp/dcndl/terms/", "oaire": "http://namespace.openaire.eu/schema/oaire/", "jpcoar": "https://github.com/JPCOAR/schema/blob/master/1.0/", "dcterms": "http://purl.org/dc/terms/", "datacite": "https://schema.datacite.org/meta/kernel-4/", "rioxxterms": "http://www.rioxx.net/schema/v2.0/rioxxterms/"}
    schema_location='https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd'
    oaischema = OAIServerSchema(id=uuid.uuid4(),schema_name=schema_name,form_data=form_data,xsd=xsd,namespaces=namespaces,schema_location=schema_location,isvalid=True,is_mapping=False,isfixed=False,version_id=1)
    with db.session.begin_nested():
        db.session.add(oaischema)


@pytest.fixture()
def db_itemtype(app, db):
    item_type_name = ItemTypeName(name='テストアイテムタイプ',
                                  has_site_license=True,
                                  is_active=True)
    item_type_schema=dict()
    with open('tests/data/itemtype_schema.json', 'r') as f:
        item_type_schema = json.load(f)
    
    item_type_form=dict()
    with open('tests/data/itemtype_form.json', 'r') as f:
        item_type_form = json.load(f)
    
    item_type_render=dict()
    with open('tests/data/itemtype_render.json', 'r') as f:
        item_type_render = json.load(f)
    
    item_type_mapping=dict()
    with open('tests/data/itemtype_mapping.json', 'r') as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(name_id=1,harvesting_type=True,
                         schema=item_type_schema,
                         form=item_type_form,
                         render=item_type_render,
                         tag=1,version_id=1,is_deleted=False)
    
    item_type_mapping = ItemTypeMapping(item_type_id=1,mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
        
    return {'item_type_name':item_type_name,'item_type':item_type}