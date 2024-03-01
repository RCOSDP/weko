import io
import uuid
from datetime import datetime
from unittest import mock  # python3
#from unittest.mock import MagicMock

import mock  # python2, after pip install mock
import pytest
from flask import Flask, json, jsonify, session, url_for
from flask_babelex import get_locale, to_user_timezone, to_utc
from flask_login import current_user
from flask_security import login_user
from flask_security.utils import login_user
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from mock import patch

from weko_items_ui.models import CRISLinkageResult
from weko_deposit.pidstore import weko_deposit_minter
from weko_records.models import ItemMetadata

record_uuid = uuid.uuid4()
record_uuid_2 = uuid.uuid4()
record_uuid_3 = uuid.uuid4()
record_uuid_4 = uuid.uuid4()
record_uuid_5 = uuid.uuid4()
data = {"recid":1}
data_2 = {"recid":2}
data_4 = {"recid":4}

cris_linkage_result = CRISLinkageResult(
    recid = 1,
    cris_institution = "researchmap",
    last_linked_date = datetime.now(),
    last_linked_item = record_uuid,
    succeed = False,
    failed_log = "failed_log"
)

cris_linkage_result_2 = CRISLinkageResult(
    recid = 2,
    cris_institution = "researchmap",
    last_linked_date = datetime.now(),
    last_linked_item = record_uuid_2,
    succeed = False,
    failed_log = "failed_log"
)

cris_linkage_result_4 = CRISLinkageResult(
    recid = 4,
    cris_institution = "researchmap",
    last_linked_date = datetime.now(),
    last_linked_item = record_uuid_4,
    succeed = False,
    failed_log = "failed_log"
)

item_metadata = ItemMetadata(
    id = record_uuid,
    item_type_id = 1,
    json = {}
)

item_metadata_2 = ItemMetadata(
    id = record_uuid_2,
    item_type_id = 1,
    json = {}
)

item_metadata_3 = ItemMetadata(
    id = record_uuid_3,
    item_type_id = 1,
    json = {}
)

item_metadata_4 = ItemMetadata(
    id = record_uuid_4,
    item_type_id = 1,
    json = {}
)

item_metadata_5 = ItemMetadata(
    id = record_uuid_5,
    item_type_id = 1,
    json = {}
)

#class CRISLinkageResult(db.Model, Timestamp):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp

class TestCRISLinkageResult:

    # def get_last(self ,recid ,cris_institution):
    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult::test_get_last -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_get_last(self, app, db):
        weko_deposit_minter(record_uuid, data, 1)
        db.session.add(item_metadata)
        db.session.commit()
        with db.session.begin_nested():
            db.session.add(cris_linkage_result)
        db.session.commit()

        result = CRISLinkageResult().get_last(recid=100, cris_institution="researchmap")
        assert result == None

    # def register_linkage_result(self ,recid ,cris_institution ,result ,item_uuid ,failed_log):
    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult::test_register_linkage_result -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_register_linkage_result(self,app, db):
        weko_deposit_minter(record_uuid_2, data_2, 2)
        weko_deposit_minter(record_uuid_3, data, 100)
        db.session.add(item_metadata_2)
        db.session.add(item_metadata_3)
        db.session.commit()
        with db.session.begin_nested():
            db.session.add(cris_linkage_result_2)
        db.session.commit()

        result = CRISLinkageResult().register_linkage_result(recid=2, cris_institution="researchmap", result=True, item_uuid=record_uuid_2, failed_log="")
        assert result == True

        result = CRISLinkageResult().register_linkage_result(recid=100, cris_institution="researchmap", result=False, item_uuid=record_uuid_3, failed_log="")
        assert result == True


    # def set_running(self, item_uuid ,cris_institution):
    # .tox/c1/bin/pytest --cov=weko_items_ui tests/test_models.py::TestCRISLinkageResult::test_set_running -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
    def test_set_running(self,app,db):
        weko_deposit_minter(record_uuid_4, data_4, 4)
        weko_deposit_minter(record_uuid_5, data, 100)
        db.session.add(item_metadata_4)
        db.session.add(item_metadata_5)
        db.session.commit()
        with db.session.begin_nested():
            db.session.add(cris_linkage_result_4)
        db.session.commit()

        CRISLinkageResult().set_running(record_uuid_4, "researchmap")
        result = CRISLinkageResult().get_last(4, "researchmap")
        assert result.last_linked_item == record_uuid_4

        CRISLinkageResult().set_running(record_uuid_5, "researchmap")
        result = CRISLinkageResult().get_last(100, "researchmap")
        assert result.last_linked_item == record_uuid_5
