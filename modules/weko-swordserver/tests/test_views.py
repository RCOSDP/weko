import os
from unittest.mock import MagicMock, PropertyMock
from flask import url_for,json,request,abort
from flask_login.utils import login_user
from zipfile import BadZipFile
import pytest
import datetime
from time import sleep
from unittest.mock import MagicMock, patch

from flask import url_for,json,abort
from flask_limiter.errors import RateLimitExceeded
from sword3common.lib.seamless import SeamlessException
from werkzeug.datastructures import FileStorage

from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier
from invenio_files_rest.models import Location
from invenio_records.models import RecordMetadata

from weko_search_ui.utils import handle_check_date, handle_check_exist_record, import_items_to_system
from weko_workflow.models import Activity

from weko_swordserver.errors import *
from weko_swordserver.views import _get_status_workflow_document, blueprint, _get_status_document,_create_error_document,post_service_document

from .helpers import json_data, calculate_hash

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp

# def get_service_document():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_get_service_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_get_service_document(client,users,tokens):
    login_user_via_session(client=client,email=users[0]["email"])
    token = tokens[0]["token"].access_token
    url = url_for("weko_swordserver.get_service_document")
    headers = {
        "Authorization":"Bearer {}".format(token),
    }
    res = client.get(url,headers=headers)
    assert res.status_code == 200

    mock_identify = MagicMock()
    mock_identify.repositoryName = "testRepositoryName1"
    with patch("invenio_oaiserver.api.OaiIdentify.get_all",return_value=mock_identify):
        res = client.get(url,headers=headers)
        assert res.status_code == 200
        assert res.json["dc:title"] == "testRepositoryName1"
    with patch("weko_swordserver.views.get_site_info_name", return_value=("testRepositoryName2","")):
        res = client.get(url,headers=headers)
        assert res.status_code == 200
        assert res.json["dc:title"] == "testRepositoryName2"


# def post_service_document():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_post_service_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_post_service_document(app,client,db,users,esindex,location,index,make_zip,tokens,item_type,doi_identifier,mocker,sword_mapping,sword_client,admin_settings):
    token_direct = tokens[0]["token"].access_token
    token_workflow = tokens[1]["token"].access_token
    admin_settings[9].settings = {"data_format": {"TSV": {"item_type": "1", "register_format": "Direct"}, "XML": {"workflow": "1", "item_type": "1", "register_format": "Workflow"}}, "default_format": "TSV"}
    db.session.commit()

    url = url_for("weko_swordserver.post_service_document")
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    def update_location_size():
        loc = db.session.query(Location).filter(
                    Location.id == 1).one()
        loc.size = 1547
    mocker.patch("weko_swordserver.views._get_status_document",side_effect=lambda x:{"recid":x})
    mocker.patch("weko_search_ui.utils.find_and_update_location_size",side_effect=update_location_size)
    mocker.patch("weko_search_ui.utils.send_item_created_event_to_es")
    mocker.patch("weko_swordserver.views.dbsession_clean")
    # register TSV/CSV file
    zip = make_zip()
    # with patch("weko_swordserver.views.import_items_to_system", return_value={"success": True, "recid": 1}):
    login_user_via_session(client=client,email=users[0]["email"])
    storage = FileStorage(filename="payload.zip",stream=zip)
    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
    assert res.status_code == 200

    recid = json.loads(res.data)["recid"]
    recid = PersistentIdentifier.get("recid",recid).object_uuid
    record = RecordMetadata.query.filter_by(id=recid).one_or_none()
    assert record is not None
    record = record.json
    file_metadata = record["item_1617605131499"]["attribute_value_mlt"][0]
    assert file_metadata.get("url") is not None
    assert file_metadata.get("url").get("url") == "https://localhost/record/1/files/sample.html"

    # register XML file
    login_user_via_session(client=client,email=users[1]["email"])
    expected_activity_id = "A-20240301-00001"
    activity = MagicMock(spec=Activity)
    prop_mock = PropertyMock(return_value=expected_activity_id)
    type(activity).activity_id = prop_mock
    detail = "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002"
    current_action = "item_login"
    recid = 200001
    with patch("weko_swordserver.views.import_items_to_activity", return_value=(detail, recid, current_action)):
        file_data2 = FileStorage(
            stream=open("tests/data/workflow_data/sample_file_jpcoar_xml.zip", "rb"),
            filename="sample_file_jpcoar_xml.zip",
            content_type="application/zip",
        )
        headers2 = {
            "Authorization":"Bearer {}".format(token_workflow),
            "Content-Disposition":"attachment; filename=sample_file_jpcoar_xml.zip",
            "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
        }
        res = client.post(url, data=dict(file=file_data2),content_type="multipart/form-data",headers=headers2)
        assert res.status_code == 200

    # exist "error" in check_result
    login_user_via_session(client=client,email=users[0]["email"])
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    checked = {"error":"test_check_error","list_record":["test_item"]}
    with patch("weko_swordserver.registration.check_tsv_import_items",return_value=checked) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        assert res.status_code == 500
        assert json.loads(res.data).get("@type") == "ServerError"
        assert json.loads(res.data).get("error") == "Error in check_import_items: test_check_error"


    # exist "error" in item
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    checked = {"error":"","list_record":[{"errors":["this is test item error1","this is test item error2"]}]}
    with patch("weko_swordserver.views.check_import_items",return_value=(checked, None)) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        assert res.status_code == 400
        assert json.loads(res.data).get("@type") == "ContentMalformed"
        assert json.loads(res.data).get("error") == "Error in check_import_items: this is test item error1, this is test item error2"


    # else
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    checked = {"error":"","list_record":[{}]}
    with patch("weko_swordserver.views.check_import_items",return_value=(checked, None)) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        assert res.status_code == 400
        assert json.loads(res.data).get("@type") == "ContentMalformed"
        assert json.loads(res.data).get("error") == "Error in check_import_items: item_missing"


    # item.status is not new
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    checked = {"error":"","list_record":[{"status":"update","item_title":"not_new_item"}]}
    with patch("weko_swordserver.views.check_import_items",return_value=(checked, None)) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        assert res.status_code == 400
        assert json.loads(res.data).get("@type") == "BadRequest"
        assert json.loads(res.data).get("error") == "This item is already registered: not_new_item"


    # import failed (Direct)
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    checked = {"error":"","list_record":[{"status":"new","item_title":"new_item"}]}
    with patch("weko_swordserver.views.check_import_items", return_value=(checked, "TSV/CSV")) as check_import_items:
        with patch("weko_swordserver.views.import_items_to_system", return_value={"error_id":"test error in import"}) as import_items_to_system:
            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        import_items_to_system.assert_called_once()
        assert res.status_code == 500
        assert json.loads(res.data).get("@type") == "ServerError"
        assert json.loads(res.data).get("error") == "Error in import_items_to_system: test error in import"


    # import failed (Workflow)
    login_user_via_session(client=client,email=users[1]["email"])
    zip = make_zip()
    storage = FileStorage(filename="sample_file_jpcoar_xml.zip",stream=zip)
    checked = {"error":"","list_record":[{"status":"new","item_title":"new_item"}]}
    with patch("weko_swordserver.views.check_import_items", return_value=(checked, "XML")) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers2)
        check_import_items.assert_called_once()
        assert res.status_code == 500
        assert json.loads(res.data).get("@type") == "ServerError"
        assert json.loads(res.data).get("error") == "An error occurred while import to activity"

    # import failed (not has scope user:activity)
    login_user_via_session(client=client,email=users[0]["email"])
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    checked = {"error":"","list_record":[{"status":"new","item_title":"new_item"}]}
    with patch("weko_swordserver.views.check_import_items", return_value=(checked, "XML")) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        assert res.status_code == 403
        assert json.loads(res.data).get("@type") == "Forbidden"
        assert json.loads(res.data).get("error") == "Not allowed operation in your token scope."


    # invalid register format
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    checked = {"error":"","list_record":[{"status":"new","item_title":"new_item"}]}
    with patch("weko_swordserver.views.check_import_items", return_value=(checked, "invalid")) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        assert res.status_code == 500
        assert json.loads(res.data).get("@type") == "ServerError"
        assert json.loads(res.data).get("error") == "Invalid register format has been set for admin setting"


    # check if delete temporary directory
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    data_path = "test"
    os.mkdir(data_path)
    checked = {"error":"","list_record":[{"status":"new","item_title":"new_item"}], "data_path": data_path}
    with patch("weko_swordserver.views.check_import_items", return_value=(checked, "invalid")) as check_import_items:
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        check_import_items.assert_called_once()
        assert res.status_code == 500
        assert json.loads(res.data).get("@type") == "ServerError"
        assert json.loads(res.data).get("error") == "Invalid register format has been set for admin setting"
        assert not os.path.exists(data_path)

    # invalid Content-Disposition
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"inline",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
    assert res.status_code == 400
    assert json.loads(res.data).get("@type") == "BadRequest"
    assert json.loads(res.data).get("error") == "Cannot get filename by Content-Disposition."

    # invalid file name in Content-Disposition
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=invalid.txt",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
    assert res.status_code == 400
    assert json.loads(res.data).get("@type") == "BadRequest"
    assert json.loads(res.data).get("error") == "Not found invalid.txt in request body."


# def post_service_document():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_post_service_document_json_ld -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_post_service_document_json_ld(app,client,db,users,esindex,location,index,make_crate,tokens,item_type,doi_identifier,sword_mapping,sword_client,mocker):
    def update_location_size():
        loc = db.session.query(Location).filter(
                    Location.id == 1).one()
        loc.size = 1547
    mocker.patch("weko_swordserver.views._get_status_document",side_effect=lambda x:{"recid":x})
    mocker.patch("weko_search_ui.utils.find_and_update_location_size",side_effect=update_location_size)
    mocker.patch("weko_search_ui.utils.send_item_created_event_to_es")
    mocker.patch("weko_swordserver.views.dbsession_clean")

    token_direct = tokens[0]["token"].access_token
    token_workflow = tokens[1]["token"].access_token
    token_none = tokens[3]["token"].access_token
    url = url_for("weko_swordserver.post_service_document")

    # Digest VERIFICATION ON
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True

    login_user_via_session(client=client,email=users[0]["email"])
    # Direct registration
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip",stream=zip)
    mapped_json = json_data("data/item_type/mapped_json_2.json")
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
        with patch("weko_swordserver.registration.bagit.Bag.validate"):
            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        assert res.status_code == 200
        recid = res.json["recid"]
        recid = PersistentIdentifier.get("recid",recid)
        record = RecordMetadata.query.filter_by(id=recid.object_uuid).one_or_none()
        assert record is not None
        record = record.json
        file_metadata = record["item_1617604990215"]["attribute_value_mlt"][0]
        assert file_metadata.get("url") is not None
        assert file_metadata.get("url").get("url") == f"https://localhost/record/{recid.id}/files/sample.rst"


    # invalid hash and be rejected
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip",stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256=1NVAL1DHASHTEST"
    }
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
        with patch("weko_swordserver.registration.bagit.Bag.validate"):
            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        assert res.status_code == 412
        assert res.json.get("@type") == "DigestMismatch"
        assert res.json.get("error") == "Request body and digest verification failed."


    # invalid hash but setting is off
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = False

    # Workflow registration
    login_user_via_session(client=client,email=users[0]["email"])
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip",stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_workflow),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    detail = "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002"
    current_action = "item_login"
    recid = 200001
    mapped_json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.views.import_items_to_activity", return_value=(detail, recid, current_action)):
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with patch("weko_swordserver.registration.bagit.Bag.validate"):
                res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        assert res.status_code == 200

    # no scopes
    zip, _  = make_crate()
    storage = FileStorage(filename="payload.zip",stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_none),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    mapped_json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
        with patch("weko_swordserver.registration.bagit.Bag.validate"):
            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        assert res.status_code == 403


# def get_status_document(recid):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test__get_status_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_get_status_document(client, users, tokens):
    login_user_via_session(client=client,email=users[0]["email"])
    token = tokens[0]["token"].access_token
    url = url_for("weko_swordserver.get_status_document",recid="test_recid")
    headers = {
        "Authorization":"Bearer {}".format(token),
    }
    with patch("weko_swordserver.views._get_status_document",side_effect=lambda x:{"recid":x}):
        res = client.get(url, headers=headers)
        assert res.status_code == 200
        assert res.json == {"recid":"test_recid"}


# def _get_status_document(recid):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test__get_status_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test__get_status_document(app,records):
    recid_doi = records[0][0].pid_value
    recid_not_doi = records[2][0].pid_value
    recid_sysdoi = records[3][0].pid_value

    test_doi = {
        "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
        "@type": "Status",
        "@id" : url_for('weko_swordserver.get_status_document', recid=recid_doi, _external=True),
        "actions" : {"getMetadata" : False,"getFiles" : False,"appendMetadata" : False,"appendFiles" : False,"replaceMetadata" : False,"replaceFiles" : False,"deleteMetadata" : False,"deleteFiles" : False,"deleteObject" : True,},
        "eTag" : str(1),
        "fileSet" : {},
        "metadata" : {},
        "service" : url_for('weko_swordserver.get_service_document',_external=False),
        "state" : [
            {
                "@id" : "http://purl.org/net/sword/3.0/state/ingested",
                "description" : ""
            }
        ],
        "links" : [
            {
                "@id" : "http://TEST_SERVER.localdomain/records/{}".format(recid_doi),
                "rel" : ["alternate"],
                "contentType" : "text/html"
            },
            {
                "@id":"https://doi.org/test/0000000001",
                "rel":["alternate"],
                "contentType":"text/html"
            }
        ]
    }
    test_not_doi = {
        "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
        "@type": "Status",
        "@id" : url_for('weko_swordserver.get_status_document', recid=recid_not_doi, _external=True),
        "actions" : {"getMetadata" : False,"getFiles" : False,"appendMetadata" : False,"appendFiles" : False,"replaceMetadata" : False,"replaceFiles" : False,"deleteMetadata" : False,"deleteFiles" : False,"deleteObject" : True,},
        "eTag" : str(1),
        "fileSet" : {},
        "metadata" : {},
        "service" : url_for('weko_swordserver.get_service_document',_external=False),
        "state" : [
            {
                "@id" : "http://purl.org/net/sword/3.0/state/ingested",
                "description" : ""
            }
        ],
        "links" : [{
                "@id" : "http://TEST_SERVER.localdomain/records/{}".format(recid_not_doi),
                "rel" : ["alternate"],
                "contentType" : "text/html"
            }]
    }
    test_sysdoi = {
        "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
        "@type": "Status",
        "@id" : url_for('weko_swordserver.get_status_document', recid=recid_sysdoi, _external=True),
        "actions" : {"getMetadata" : False,"getFiles" : False,"appendMetadata" : False,"appendFiles" : False,"replaceMetadata" : False,"replaceFiles" : False,"deleteMetadata" : False,"deleteFiles" : False,"deleteObject" : True,},
        "eTag" : str(1),
        "fileSet" : {},
        "metadata" : {},
        "service" : url_for('weko_swordserver.get_service_document',_external=False),
        "state" : [
            {
                "@id" : "http://purl.org/net/sword/3.0/state/ingested",
                "description" : ""
            }
        ],
        "links" : [
            {
                "@id" : "http://TEST_SERVER.localdomain/records/{}".format(recid_sysdoi),
                "rel" : ["alternate"],
                "contentType" : "text/html"
            },
            {
                "@id":"test_system_doi",
                "rel":["alternate"],
                "contentType":"text/html"
            }
        ]
    }
    with app.test_request_context("/test_req"):
        # exist permalink
        result = _get_status_document(recid_doi)
        assert result == test_doi

        # not exist permalink
        result = _get_status_document(recid_not_doi)
        assert result == test_not_doi

        # exist system_identifier_doi
        result = _get_status_document(recid_sysdoi)
        assert result == test_sysdoi

        # raise WekoSwordserverException
        with pytest.raises(WekoSwordserverException) as e:
            _get_status_document("not_exist_recid")
            assert e.message == "Item not found. (recid=not_exist_recid)"
            assert e.errorType == ErrorType.NotFound


# def _get_status_workflow_document(activity, recid):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test__get_status_workflow_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test__get_status_workflow_document(app, records):
    recid_doi = records[0][0].pid_value
    recid_not_doi = records[2][0].pid_value

    expected_activity_id = "A-20240301-00001"

    test_doi = {
        "@id" : url_for('weko_swordserver.get_status_document', recid=recid_doi, _external=True),
        "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
        "@type": "ServiceDocument",
        "actions" : {"getMetadata" : False,"getFiles" : False,"appendMetadata" : False,"appendFiles" : False,"replaceMetadata" : False,"replaceFiles" : False,"deleteMetadata" : False,"deleteFiles" : False,"deleteObject" : True,},
        "fileSet" : {},
        "metadata" : {},
        "service" : url_for('weko_swordserver.get_service_document',_external=False),
        "state" : [
            {
                "@id" : "http://purl.org/net/sword/3.0/state/inWorkflow",
                "description" : ""
            }
        ],
        "links": [
            {
                "@id" : url_for('weko_workflow.display_activity', activity_id=expected_activity_id, _external=True),
                "rel" : ["alternate"],
                "contentType" : "text/html"
            },
        ]
    }
    test_doi_no_recid = {
        "@id" : "",
        "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
        "@type": "ServiceDocument",
        "actions" : {"getMetadata" : False,"getFiles" : False,"appendMetadata" : False,"appendFiles" : False,"replaceMetadata" : False,"replaceFiles" : False,"deleteMetadata" : False,"deleteFiles" : False,"deleteObject" : True,},
        "fileSet" : {},
        "metadata" : {},
        "service" : url_for('weko_swordserver.get_service_document',_external=False),
        "state" : [
            {
                "@id" : "http://purl.org/net/sword/3.0/state/inWorkflow",
                "description" : ""
            }
        ],
        "links" : [
            {
                "@id" : url_for('weko_workflow.display_activity', activity_id=expected_activity_id, _external=True),
                "rel" : ["alternate"],
                "contentType" : "text/html"
            }
        ]
    }

    with app.test_request_context("/test_req"):
        # exist recid
        result = _get_status_workflow_document(expected_activity_id, recid_doi)
        assert result == test_doi

        # not exist recid
        result = _get_status_workflow_document(expected_activity_id, None)
        assert result == test_doi_no_recid

        # raise WekoSwordserverException
        with pytest.raises(WekoSwordserverException) as e:
            _get_status_workflow_document(None, None)
            assert e.message == "Activity created, but not found."
            assert e.errorType == ErrorType.NotFound


# def delete_item(recid):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_delete_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_delete_item(client, tokens, users,es_records):
    login_user_via_session(client=client,email=users[0]["email"])
    token = tokens[0]["token"].access_token
    delete_item = es_records[0][0].pid_value
    url = url_for("weko_swordserver.delete_item",recid=delete_item)
    headers = {
        "Authorization":"Bearer {}".format(token),
    }

    res = client.delete(url, headers=headers)
    assert res.status_code == 204
    target = PersistentIdentifier.query.filter_by(pid_type="recid",pid_value=delete_item).first()
    assert target.status == "D"

    # coverage - Exception
    with patch("weko_swordserver.views.soft_delete", side_effect=Exception):
        res = client.delete(url, headers=headers)
        assert res.status_code == 204

# def _create_error_document(type, error):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test__create_error_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test__create_error_document(mocker):
    mock_datetime = mocker.patch("weko_swordserver.views.datetime")
    mock_datetime.now.return_value=datetime.datetime(2022,10,1,2,3,4)
    test = {
        "@context":"https://swordapp.github.io/swordv3/swordv3.jsonld",
        "@type":"BadRequest",
        "timestamp":"2022-10-01T02:03:04Z",
        "error":"this is test bad_request_error."
    }
    result = _create_error_document("BadRequest","this is test bad_request_error.")
    assert result == test


@blueprint.route("/test_error/<error_type>",methods=["GET"])
def error_handle_test_view(error_type):
    """View for testing the errorhandler
    """
    if error_type == "401":
        abort(401)
    elif error_type == "403":
        abort(403)
    elif error_type == "RateLimitExceeded":
        failed_limit = MagicMock()
        failed_limit.error_message = "this is test RateLimitExceeded"
        raise RateLimitExceeded(failed_limit)
    elif error_type == "SeamlessException":
        raise SeamlessException("this is test SeamlessException")
    elif error_type == "Exception":
        raise Exception("test_exception")
    elif error_type == "WekoSwordserverException":
        raise WekoSwordserverException("this is test BadRequest exception", ErrorType.BadRequest)


# def handle_unauthorized(ex):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_handle_unauthorized -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_handle_unauthorized(client,sessionlifetime):
    url = url_for("weko_swordserver.error_handle_test_view",error_type="401")
    with patch("weko_swordserver.views._create_error_document",side_effect=lambda x,y:{"type":x,"msg":y}):
        res = client.get(url)
        assert res.status_code == 401
        assert res.json == {"type":"AuthenticationRequired","msg":"Authentication is required."}


# def handle_forbidden(ex):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_handle_forbidden -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_handle_forbidden(client,sessionlifetime):
    url = url_for("weko_swordserver.error_handle_test_view",error_type="403")
    with patch("weko_swordserver.views._create_error_document",side_effect=lambda x,y:{"type":x,"msg":y}):
        res = client.get(url)
        assert res.status_code == 403
        assert res.json == {"type":"Forbidden","msg":"Not allowed operation in your token scope."}

# def handle_ratelimit(ex):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_handle_ratelimit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_handle_ratelimit(client,sessionlifetime):
    url = url_for("weko_swordserver.error_handle_test_view",error_type="RateLimitExceeded")
    with patch("weko_swordserver.views._create_error_document",side_effect=lambda x,y:{"type":x,"msg":y}):
        res = client.get(url)
        assert res.status_code == 429
        assert res.json == {"type":"TooManyRequests","msg":"Too many requests."}

# def handle_seamless_exception(ex):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_handle_seamless_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_handle_seamless_exception(client,sessionlifetime):
    url = url_for("weko_swordserver.error_handle_test_view",error_type="SeamlessException")
    with patch("weko_swordserver.views._create_error_document",side_effect=lambda x,y:{"type":x,"msg":y}):
        res = client.get(url)
        assert res.status_code == 500
        assert res.json == {"type":"ServerError","msg":"this is test SeamlessException"}


# def handle_exception(ex):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_handle_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_handle_exception(client,sessionlifetime):
    url = url_for("weko_swordserver.error_handle_test_view",error_type="Exception")
    with patch("weko_swordserver.views._create_error_document",side_effect=lambda x,y:{"type":x,"msg":y}):
        res = client.get(url)
        assert res.status_code == 500
        assert res.json == {"type":"ServerError","msg":"Internal Server Error"}


# def handle_weko_swordserver_exception(ex):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_handle_weko_swordserver_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_handle_weko_swordserver_exception(client,sessionlifetime):
    url = url_for("weko_swordserver.error_handle_test_view",error_type="WekoSwordserverException")
    with patch("weko_swordserver.views._create_error_document",side_effect=lambda x,y:{"type":x,"msg":y}):
        res = client.get(url)
        assert res.status_code == 400
        assert res.json == {"type":"BadRequest","msg":"this is test BadRequest exception"}
