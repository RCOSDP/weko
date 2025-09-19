# conftest.py
from __future__ import absolute_import, print_function

import pytest
import shutil
import json
import tempfile
import uuid
from flask import Flask

from invenio_db import InvenioDB
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from weko_records import WekoRecords
from weko_workflow import WekoWorkflow
from weko_deposit import WekoDeposit

from invenio_db import db as db_
from sqlalchemy_utils.functions import create_database, database_exists
from weko_records.models import ItemMetadata
from invenio_records.models import RecordMetadata
from weko_workflow.models import (
    Activity,
    ActionStatus,
    Action,
    ActivityAction,
    WorkFlow,
    FlowDefine,
    FlowAction,
    ActionFeedbackMail,
    ActionIdentifier,
    FlowActionRole,
    ActivityHistory,
    GuestActivity, 
    WorkflowRole
)

@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""

    app_ = Flask("testapp", instance_path=instance_path)

    app_.config.update(
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        SEARCH_UI_SEARCH_INDEX="test-search-weko"
    #     CELERY_ALWAYS_EAGER=True,
    #     CELERY_CACHE_BACKEND="memory",
    #     CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    #     CELERY_RESULT_BACKEND="cache",
    #     CACHE_REDIS_URL=os.environ.get(
    #         "CACHE_REDIS_URL", "redis://redis:6379/0"
    #     ),
    #     CACHE_REDIS_DB=0,
    #     CACHE_REDIS_HOST="redis",
    #     REDIS_PORT="6379",
    #     JSONSCHEMAS_URL_SCHEME="http",
    #     SECRET_KEY="CHANGE_ME",
    #     SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
    #     SQLALCHEMY_DATABASE_URI=os.environ.get(
    #         'SQLALCHEMY_DATABASE_URI',
    #         'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
    #     # SQLALCHEMY_DATABASE_URI=os.environ.get(
    #     #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
    #     # ),
    #     SQLALCHEMY_TRACK_MODIFICATIONS=True,
    #     SQLALCHEMY_ECHO=False,
    #     TESTING=True,
    #     WTF_CSRF_ENABLED=False,
    #     DEPOSIT_SEARCH_API="/api/search",
    #     SECURITY_PASSWORD_HASH="plaintext",
    #     SECURITY_PASSWORD_SCHEMES=["plaintext"],
    #     SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
    #     OAUTHLIB_INSECURE_TRANSPORT=True,
    #     OAUTH2_CACHE_TYPE="simple",
    #     ACCOUNTS_JWT_ENABLE=False,
    #     INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
    #     SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
    #     
    #     INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
    #     
    #     WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
    #     WEKO_MAX_FILE_SIZE=WEKO_BUCKET_QUOTA_SIZE,
    #     INDEX_IMG="indextree/36466818-image.jpg",
    #     WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
    #     DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
    #     WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
    #     WEKO_INDEX_TREE_STYLE_OPTIONS={
    #         "id": "weko",
    #         "widths": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
    #     },
    #     WEKO_INDEX_TREE_UPATED=True,
    #     WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
    #     I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English"),("da", "Danish")],
    #     SERVER_NAME="TEST_SERVER",
    #     SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
    #     SEARCH_INDEX_PREFIX="test-",
    #     WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME=WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
    #     WEKO_SCHEMA_DDI_SCHEMA_NAME=WEKO_SCHEMA_DDI_SCHEMA_NAME,
    #     WEKO_PERMISSION_SUPER_ROLE_USER=[
    #         "System Administrator",
    #         "Repository Administrator",
    #     ],
    #     WEKO_PERMISSION_ROLE_COMMUNITY=["Community Administrator"],
    )

    InvenioDB(app_)
    InvenioRecords(app_)
    InvenioSearch(app_)
    WekoRecords(app_)
    WekoDeposit(app_)
    WekoWorkflow(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def db(app):
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def item_data(db):
    obj_uuid1 = uuid.uuid4()
    obj_uuid2 = uuid.uuid4()
    item_meta1 = ItemMetadata(id=obj_uuid1, item_type_id=1, json={"item_0001": {"resourcetype": "periodical"}})
    item_meta2 = ItemMetadata(id=obj_uuid2, item_type_id=1, json={"item_0001": {"resourcetype": "periodical", "resourceuri": ""}})
    rec_meta1 = RecordMetadata(id=obj_uuid1, json={"item_0001": {"attribute_name": "item_resource_type", "attribute_value_mlt": [{"resourcetype": "periodical"}]}})
    rec_meta2 = RecordMetadata(id=obj_uuid2, json={"item_0001": {"attribute_name": "item_resource_type", "attribute_value_mlt": [{"resourcetype": "periodical", "resourceuri": ""}]}})
    db.session.add_all([item_meta1, item_meta2, rec_meta1, rec_meta2])
    db.session.commit()

    return [obj_uuid1, obj_uuid2]

@pytest.fixture()
def action_data(db):
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

