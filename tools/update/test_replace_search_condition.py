from flask import Flask
import tempfile
import shutil
import pytest
import os
import sys
from flask_babelex import Babel
from invenio_i18n import InvenioI18N
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_db import InvenioDB
from invenio_db import db as db_
from weko_records.config import WEKO_ITEMTYPE_EXCLUDED_KEYS
from weko_records_ui.config import WEKO_PERMISSION_SUPER_ROLE_USER, WEKO_PERMISSION_ROLE_COMMUNITY, EMAIL_DISPLAY_FLG
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords, Record
from invenio_search import InvenioSearch
from weko_deposit.api import WekoDeposit
from weko_search_ui import WekoSearchUI
from weko_records_ui import WekoRecordsUI
from weko_records import WekoRecords
from weko_records.api import ItemTypes, Mapping
from weko_itemtypes_ui import WekoItemtypesUI
from invenio_records.models import RecordMetadata
from sqlalchemy_utils.functions import create_database, database_exists
from mock import patch, MagicMock
from elasticsearch.exceptions import TransportError
from invenio_records_rest.errors import PIDResolveRESTError
from werkzeug.exceptions import InternalServerError
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime

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
        SEARCH_UI_SEARCH_INDEX='tenant1',
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
        WEKO_PERMISSION_ROLE_COMMUNITY=WEKO_PERMISSION_ROLE_COMMUNITY,
        EMAIL_DISPLAY_FLG=EMAIL_DISPLAY_FLG
    )

    WekoRecords(app_)
    Babel(app_)
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
    WekoItemtypesUI(app_)
    WekoSearchUI(app_)
    WekoRecordsUI(app_)

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
        yield

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

@pytest.fixture
def metadata_json1():
    metadata_json1 = {
            "_oai": {
                "id": "oai:jdcat-dev.ir.rcos.nii.ac.jp:00021042",
                "sets": [
                    "1636462638957"
                ]
            },
            "path": [
              "1636462638957"
            ],
            "recid": "21042",
            "item_type_id": "12",
            "item_1551264418667": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "subitem_1551257036415": "Distributor",
                        "subitem_1551257245638": [
                            {
                                "subitem_1551257276108": "東京大学史料編纂所",
                                "subitem_1551257279831": "ja"
                            },
                            {
                                "subitem_1551257276108": "Historiographical Institute, the University of Tokyo",
                                "subitem_1551257279831": "en"
                            }
                        ],
                        "subitem_1551257339190": [
                            {
                                "subitem_1551257342360": ""
                            }
                        ]
                    },
                    {
                        "subitem_1551257036415": "Other",
                        "subitem_1551257245638": [
                            {
                                "subitem_1551257276108": "神奈川県立金沢文庫・称名寺",
                                "subitem_1551257279831": "ja"
                            },
                            {
                                "subitem_1551257276108": "KANAGAWA PREFECTURAL KANAZAWA-BUNKO MUSEUM, Shomyoji Temple",
                                "subitem_1551257279831": "en"
                            }
                        ],
                        "subitem_1551257339190": [
                            {
                                "subitem_1551257342360": ""
                            }
                        ]
                    }
                ]
            },
            "item_1636460428217": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_1522657647525": "Abstract",
                        "subitem_1522657697257": "成立: 鎌倉時代後期\n差出: きよあり\n形状: 竪紙（上半分欠の切紙として伝存）\n遺文: 鎌22439\n和暦年月日: （年月日未詳）\n神奈川県史: 1476\n金文番号: 577\n料紙: 楮紙\n員数: 1通\n整理番号: 2847\n紙背: 題未詳聖教（折本、真言関係）\n法量: 縦16.1 x 横50.7\n紙数: 1紙",
                        "subitem_1523262169140": "ja"
                    },
                    {
                        "subitem_1522657647525": "Other",
                        "subitem_1522657697257": "史資料: テキスト",
                        "subitem_1523262169140": "ja"
                    },
                    {
                        "subitem_1522657647525": "Other",
                        "subitem_1522657697257": "materials: text",
                        "subitem_1523262169140": "en"
                    }
                ]
            }
    }
    return metadata_json1

@pytest.fixture
def metadata_json2():
    metadata_json2 = {
            "recid": "21043",
            "item_type_id": "12",
            "item_1551264418667": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                    {
                        "subitem_1551257036415": "Distributor",
                        "subitem_1551257245638": [
                            {
                                "subitem_1551257276108": "東京大学史料編纂所",
                                "subitem_1551257279831": "ja"
                            },
                            {
                                "subitem_1551257276108": "Historiographical Institute, the University of Tokyo",
                                "subitem_1551257279831": "en"
                            }
                        ],
                        "subitem_1551257339190": [
                            {
                                "subitem_1551257342360": ""
                            }
                        ]
                    },
                    {
                        "subitem_1551257036415": "Other",
                        "subitem_1551257245638": [
                            {
                                "subitem_1551257276108": "神奈川県立金沢文庫・称名寺",
                                "subitem_1551257279831": "ja"
                            },
                            {
                                "subitem_1551257276108": "KANAGAWA PREFECTURAL KANAZAWA-BUNKO MUSEUM, Shomyoji Temple",
                                "subitem_1551257279831": "en"
                            }
                        ],
                        "subitem_1551257339190": [
                            {
                                "subitem_1551257342360": ""
                            }
                        ]
                    }
                ]
            },
    }
    return metadata_json2

@pytest.fixture
def metadata_json3():
    metadata_json3 = {
            "recid": "21044",
            "item_type_id": "12",
            "item_1636460428217": {
                "attribute_name": "Description",
                "attribute_value_mlt": [
                    {
                        "subitem_1522657647525": "Abstract",
                        "subitem_1522657697257": "成立: 鎌倉時代後期\n差出: きよあり\n形状: 竪紙（上半分欠の切紙として伝存）\n遺文: 鎌22439\n和暦年月日: （年月日未詳）\n神奈川県史: 1476\n金文番号: 577\n料紙: 楮紙\n員数: 1通\n整理番号: 2847\n紙背: 題未詳聖教（折本、真言関係）\n法量: 縦16.1 x 横50.7\n紙数: 1紙",
                        "subitem_1523262169140": "ja"
                    },
                    {
                        "subitem_1522657647525": "Other",
                        "subitem_1522657697257": "史資料: テキスト",
                        "subitem_1523262169140": "ja"
                    },
                    {
                        "subitem_1522657647525": "Other",
                        "subitem_1522657697257": "materials: text",
                        "subitem_1523262169140": "en"
                    }
                ]
            }
    }
    return metadata_json3

@pytest.fixture
def metadata_json4():
    metadata_json4 = {
            "recid": "21045",
            "item_type_id": "12",
    }
    return metadata_json4

"""
def test_get_meta_records(app,db,metadata_json):
    from replace_search_condition import get_meta_records
    with patch("sqlalchemy.engine.Engine.connect",return_value=db.session):
        get_meta_records()
"""

@pytest.fixture
def metadata_records(app,metadata_json1,metadata_json2,metadata_json3,metadata_json4):
    record1 = MagicMock()
    record1.id = 'e5fa1417-7879-4388-80db-520a04d5f431'
    record1.json = metadata_json1
    record1.uuid = 'e5fa1417-7879-4388-80db-520a04d5f431'
    record2 = MagicMock()
    record2.id = 'e5fa1417-7879-4388-80db-520a04d5f432'
    record2.json = metadata_json2
    record3 = MagicMock()
    record3.id = 'e5fa1417-7879-4388-80db-520a04d5f433'
    record3.json = metadata_json3
    record4 = MagicMock()
    record4.id = 'e5fa1417-7879-4388-80db-520a04d5f434'
    record4.json = metadata_json4
    record5 = MagicMock()
    record5.id = 'e5fa1417-7879-4388-80db-520a04d5f435'
    record5.json = metadata_json1
    record6 = MagicMock()
    record6.id = 'e5fa1417-7879-4388-80db-520a04d5f436'
    record6.json = metadata_json1

    return [record1, record2, record3, record4, record5, record6]


def test_filter_records(app,db,metadata_records):
    assert len(metadata_records) == 6
    from replace_search_condition import filter_records
    result = filter_records(metadata_records)
    assert len(result) == 5


def test_update_records_metadata(app,db,metadata_records):
    assert len(metadata_records) == 6
    from replace_search_condition import update_records_metadata
    with patch("replace_search_condition.get_meta_records",return_value=metadata_records):
        with patch("replace_search_condition.update_record_metadata",side_effect = [MagicMock(), PIDResolveRESTError(), InternalServerError(), NoResultFound(), KeyError(), TransportError('', '')]):
            update_records_metadata()


def test_update_record_metadata(app,db,metadata_records):
    from replace_search_condition import update_record_metadata
    depositMock = MagicMock()
    depositMock.id = 'e5fa1417-7879-4388-80db-520a04d5f431'
    depositMock.created = datetime.utcnow()
    depositMock.jrc = {}
    
    with patch("replace_search_condition.ItemsMetadata.get_record",
               return_value=MagicMock()):
        depositMock.jrc.update(dict(_item_metadata=metadata_records[0].json))
        depositMock.jrc['path'] = metadata_records[0].json.get('path')
        update_record_metadata(depositMock, metadata_records[0])

        metadata_records[0].json['_oai'] = {"id": "oai:jdcat-dev.ir.rcos.nii.ac.jp:00021042"}
        update_record_metadata(depositMock, metadata_records[0])

        metadata_records[0].json['_oai'] = {"id": "oai:jdcat-dev.ir.rcos.nii.ac.jp:00021042"}
        depositMock.jrc['path'] = []
        update_record_metadata(depositMock, metadata_records[0])

        with patch("replace_search_condition.FeedbackMailList.get_mail_list_by_item_id",
                   return_value=MagicMock()):
            update_record_metadata(depositMock, metadata_records[0])

        with patch("replace_search_condition.serialize_relations",
                   return_value={"version": [{"ver": 1}, {"ver": 2}, {"ver": 3}]}):
            queryMock = MagicMock()
            recidResultMock = MagicMock()
            recidMock = MagicMock()
            recidMock.object_uuid = depositMock.id
            recidResultMock.one_or_none = recidMock
            queryMock.filter_by = recidResultMock
            with patch("replace_search_condition.PersistentIdentifier.query",
                       return_value=queryMock):
                update_record_metadata(depositMock, metadata_records[0])

        depositMock.jrc['_oai'] = metadata_records[1].json.get('_oai')
        depositMock.jrc.update(dict(_item_metadata=metadata_records[1].json))
        update_record_metadata(depositMock, metadata_records[1])

        with patch("replace_search_condition.set_timestamp"):
            depositMock.jrc = None
            update_record_metadata(depositMock, metadata_records[1])



def test_main(app,db):
    from replace_search_condition import main
    main()
