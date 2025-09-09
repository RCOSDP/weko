import os
import pytest
import datetime
from unittest.mock import MagicMock, patch

from flask import url_for, request, abort
from flask_limiter.errors import RateLimitExceeded
from sword3common.lib.seamless import SeamlessException
from werkzeug.datastructures import FileStorage

from invenio_accounts.testutils import login_user_via_session
from invenio_files_rest.models import Location
from weko_workflow.errors import WekoWorkflowException

from weko_swordserver.errors import *
from weko_swordserver.views import _get_status_workflow_document, blueprint, _get_status_document, _create_error_document

from .helpers import calculate_hash

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
def test_post_service_document(app,client,db,users,make_crate,esindex,location,index,make_zip,tokens,item_type,doi_identifier,mocker,sword_mapping,sword_client):
    def update_location_size():
        loc = db.session.query(Location).filter(
                    Location.id == 1).one()
        loc.size = 1547
    mocker.patch("weko_swordserver.views._get_status_document", side_effect=lambda id:{"recid": id})
    mocker.patch("weko_swordserver.views._get_status_workflow_document", side_effect=lambda aid, id:{"activity": aid,"recid": id})
    mocker.patch("weko_search_ui.utils.find_and_update_location_size", side_effect=update_location_size)
    mocker.patch("weko_swordserver.views.dbsession_clean")

    token_direct = tokens[0]["token"].access_token
    token_workflow = tokens[1]["token"].access_token
    url = url_for("weko_swordserver.post_service_document")

    # Direct registration
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = False
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "On-Behalf-Of": "test_on_behalf_of",
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "new"}]
    }
    mocker.patch("weko_swordserver.views.import_items_to_system", return_value={"success": True, "recid": 2000001})
    mocker.patch("weko_items_ui.utils.send_mail_direct_registered")
    os.makedirs("/var/tmp/test", exist_ok=True)

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 201
    assert result.json.get("recid") == "2000001"
    assert not os.path.exists("/var/tmp/test"), os.rmdir("/var/tmp/test")

    # Workflow registration, duplicate check
    login_user_via_session(client=client, email=users[1]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    headers = {
        "Authorization": "Bearer {}".format(token_workflow),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "On-Behalf-Of": "test_on_behalf_of",
        "Digest": "SHA-256={}".format(calculate_hash(storage)),
    }
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Workflow",
        "workflow_id": 1001,
        "list_record": [{"status": "new", "metadata": {}}],
        "duplicate_check": True
    }
    mocker.patch("weko_items_ui.utils.check_duplicate", return_value=(False, [], []))
    mocker.patch("weko_swordserver.views.import_items_to_activity", return_value=(url_for("weko_workflow.display_activity", activity_id="A-TEST-00001"), "2000001", "end_action", None))

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 201
    assert result.json.get("recid") == "2000001"


    # invalid Content-Disposition's filename
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=invalid_payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Not found invalid_payload.zip in request body."

    # invalid Content-Disposition
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "invalid",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Cannot get filename by Content-Disposition."

    # Workflow registration, not have activity sqope
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = False
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Workflow",
        "list_record": [{"status": "new", "metadata": {}}],
        "duplicate_check": True
    }

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 403
    assert result.json.get("error") == "Not allowed operation in your token scope."

    # error in result
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "error": "Unexpected error.",
    }

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Item check error: Unexpected error."

    # error in item
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "new", "errors": ["Item check error."]}],
    }

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Item check error: Item check error."

    # not new item
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "item_title": "test_title"}],
    }

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "This item is already registered: test_title."

    # item duplicated
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "new", "metadata": {},}],
        "duplicate_check": True
    }
    mocker.patch("weko_items_ui.utils.check_duplicate", return_value=(True, ["2000001"], ["/records/2000001"]))

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Some similar items are already registered: ['/records/2000001']."

    # failed to import to system
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "new", "metadata": {},}]
    }
    with patch("weko_swordserver.views.import_items_to_system", return_value={"success": False, "error_id": "Failed to import to system."}):
        result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
        assert result.status_code == 400
        assert result.json.get("error") == "Failed to import item; Failed to import to system."

    # unexpected error in import to system
    login_user_via_session(client=client, email=users[1]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_workflow),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="JSON")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Workflow",
        "list_record": [{"status": "new", "metadata": {},}]
    }
    with patch("weko_swordserver.views.update_item_ids", side_effect=Exception("test error")):
        result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
        assert result.status_code == 400
        assert result.json.get("error") == (
            "Failed to import item; Unexpected error " \
            "Please open the following URL to continue with the remaining operations: " \
            "http://test_server.localdomain/workflow/activity/detail/A-TEST-00001."
        )

    # jsonid format
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip", stream=zip)
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest": "SHA-256={}".format(calculate_hash(storage)),
    }
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="JSON")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker.patch("weko_swordserver.views.is_valid_file_hash", return_value=True)
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "new", "metadata": {}}],
    }

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 201
    assert result.json.get("recid") == "2000001"

    # digest mismatch
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip", stream=zip)
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest": "SHA-256={}".format(calculate_hash(storage)),
    }
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="JSON")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker.patch("weko_swordserver.views.is_valid_file_hash", return_value=False)

    result = client.post(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 412
    assert result.json.get("error") == "Failed to verify request body and digest."


# def put_object(recid):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_put_object -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_put_object(
    app, client, db, users, make_crate, esindex, location, index, make_zip,
    tokens, item_type, doi_identifier, mocker, sword_mapping, sword_client, es_records
):
    def update_location_size():
        loc = db.session.query(Location).filter(
                    Location.id == 1).one()
        loc.size = 1547
    mocker.patch("weko_swordserver.views._get_status_document", side_effect=lambda id:{"recid": id})
    mocker.patch("weko_swordserver.views._get_status_workflow_document", side_effect=lambda aid, id:{"activity": aid,"recid": id})
    mocker.patch("weko_search_ui.utils.find_and_update_location_size", side_effect=update_location_size)
    mocker.patch("weko_swordserver.views.dbsession_clean")

    token_direct = tokens[0]["token"].access_token
    token_workflow = tokens[1]["token"].access_token

    tokens[0]["token"]._scopes = "deposit:write deposit:actions item:update"
    tokens[1]["token"]._scopes = "deposit:write deposit:actions item:update user:activity"
    db.session.commit()

    url = url_for("weko_swordserver.put_object", recid=1)

    # Direct registration
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = False
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "On-Behalf-Of": "test_on_behalf_of",
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "id": "1"}]
    }
    mocker.patch("weko_swordserver.views.import_items_to_system", return_value={"success": True, "recid": 1})
    mocker.patch("weko_items_ui.utils.send_mail_direct_registered")
    mocker.patch("weko_swordserver.views.lock_item_will_be_edit", return_value=True)
    os.makedirs("/var/tmp/test", exist_ok=True)

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 200
    assert result.json.get("recid") == "1"
    assert not os.path.exists("/var/tmp/test"), os.rmdir("/var/tmp/test")

    # workflow registration,
    login_user_via_session(client=client, email=users[1]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    headers = {
        "Authorization": "Bearer {}".format(token_workflow),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "On-Behalf-Of": "test_on_behalf_of",
        "Digest": "SHA-256={}".format(calculate_hash(storage)),
    }
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Workflow",
        "workflow_id": 1001,
        "list_record": [{"status": "keep", "id": "1", "metadata": {}}],
        "duplicate_check": True
    }
    mocker.patch("weko_items_ui.utils.check_duplicate", return_value=(False, [], []))
    mocker.patch("weko_swordserver.views.import_items_to_activity", return_value=(url_for("weko_workflow.display_activity", activity_id="A-TEST-00001"), "1", "end_action", None))

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 200
    assert result.json.get("recid") == "1"

    # invalid Content-Disposition's filename
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=invalid_payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Not found invalid_payload.zip in request body."

    # invalid Content-Disposition
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "invalid",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Cannot get filename by Content-Disposition."

    # Workflow registration, not have activity scope
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = False
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Workflow",
        "list_record": [{"status": "keep", "metadata": {}}],
        "duplicate_check": True
    }

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 403
    assert result.json.get("error") == "Not allowed operation in your token scope."

    # error in result
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "error": "Unexpected error.",
    }

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Item check error: Unexpected error."

    # error in item
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "errors": ["Item check error."]}],
    }

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Item check error: Item check error."

    # new item
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "new", "item_title": "test_title"}],
    }

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "This item is not registered yet: test_title"

    # item_id mismatch
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "id": "invalid", "item_title": "test_title"}],
    }

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Item id does not match. item: invalid, request: 1"

    # item duplicated
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "id": "1", "metadata": {},}],
        "duplicate_check": True
    }
    mocker.patch("weko_items_ui.utils.check_duplicate", return_value=(True, ["2000001"], ["/records/2000001"]))

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Some similar items are already registered: ['/records/2000001']."

    # being edited
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "id": "1", "metadata": {},}],
    }
    mocker.patch("weko_items_ui.utils.check_duplicate", return_value=(False, [], []))
    with patch("weko_swordserver.views.lock_item_will_be_edit", return_value=False):
        result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
        assert result.status_code == 400
        assert result.json.get("error") == "Item 1 will be edited by another process."

    # failed to import to system
    login_user_via_session(client=client, email=users[0]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "id": "1", "metadata": {},}]
    }
    with patch("weko_swordserver.views.import_items_to_system", return_value={"success": False, "error_id": "Failed to import to system"}):
        result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
        assert result.status_code == 400
        assert result.json.get("error") == "Failed to update item 1: Failed to import to system."

    # failed to import to activity
    login_user_via_session(client=client, email=users[1]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = False
    headers = {
        "Authorization": "Bearer {}".format(token_workflow),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Workflow",
        "list_record": [{"status": "keep", "id": "1", "metadata": {}}],
    }
    mocker.patch("weko_swordserver.views.import_items_to_activity",
                 return_value=("sample_url", "1", "end_action", "Failed to import to activity"))

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 400
    assert result.json.get("error") == "Failed to update item 1: Failed to import to activity. " \
                                       "Please open the following URL to continue with the remaining operations: sample_url."

    # failed to import to activity without url
    login_user_via_session(client=client, email=users[1]["email"])
    headers = {
        "Authorization": "Bearer {}".format(token_workflow),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    zip = make_zip()
    storage = FileStorage(filename="payload.zip", stream=zip)
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="TSV/CSV")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Workflow",
        "list_record": [{"status": "keep", "id": "1", "metadata": {}}],
    }
    mocker.patch("weko_swordserver.views.import_items_to_activity",
                 return_value=("", "1", "end_action", "Failed to import to activity"))

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 500
    assert result.json.get("error") == "Unexpected error: Failed to import to activity."

    # jsonid format
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip", stream=zip)
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest": "SHA-256={}".format(calculate_hash(storage)),
    }
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="JSON")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker.patch("weko_swordserver.views.is_valid_file_hash", return_value=True)
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "Direct",
        "list_record": [{"status": "keep", "id": "1", "metadata": {}}],
    }

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 200
    assert result.json.get("recid") == "1"

    # digest mismatch
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip", stream=zip)
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest": "SHA-256={}".format(calculate_hash(storage)),
    }
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="JSON")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker.patch("weko_swordserver.views.is_valid_file_hash", return_value=False)

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 412
    assert result.json.get("error") == "Failed to verify request body and digest."

    # invalid registration type
    login_user_via_session(client=client, email=users[0]["email"])
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = False
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip", stream=zip)
    headers = {
        "Authorization": "Bearer {}".format(token_direct),
        "Content-Disposition": "attachment; filename=payload.zip",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    mocker.patch("weko_swordserver.views.check_import_file_format", return_value="JSON")
    mocker.patch("weko_swordserver.views.get_shared_ids_from_on_behalf_of", return_value=[])
    mocker_check_item = mocker.patch("weko_swordserver.views.check_import_items")
    mocker_check_item.return_value = {
        "data_path": "/var/tmp/test",
        "register_type": "invalid_type",
        "list_record": [{"status": "keep", "id": "1", "metadata": {}}],
    }

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 500
    assert result.json.get("error") == "Invalid register format has been set for admin setting"

    # invalid registration type with data_path exists
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip", stream=zip)
    os.makedirs("/var/tmp/test", exist_ok=True)

    result = client.put(url, data={"file": storage}, content_type="multipart/form-data", headers=headers)
    assert result.status_code == 500
    assert result.json.get("error") == "Invalid register format has been set for admin setting"
    assert not os.path.exists("/var/tmp/test"), os.rmdir("/var/tmp/test")


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
def test_delete_item(app, client, db, tokens, sword_client, users,es_records, mocker):
    mocker.patch("weko_swordserver.views._get_status_document", side_effect=lambda id:{"recid": id})
    mocker.patch("weko_swordserver.views.dbsession_clean")
    mocker.patch("weko_items_ui.utils.send_mail_item_deleted")

    token_direct = tokens[0]["token"].access_token
    token_workflow = tokens[1]["token"].access_token

    tokens[0]["token"]._scopes = "deposit:write deposit:actions item:delete"
    tokens[1]["token"]._scopes = "deposit:write deposit:actions item:delete user:activity"
    db.session.commit()

    # direct deletion
    login_user_via_session(client=client,email=users[0]["email"])
    mock_record = MagicMock()
    mock_record.pid_doi = None
    mocker.patch("weko_swordserver.views.WekoRecord.get_record_by_pid", return_value=mock_record)
    mocker.patch("weko_swordserver.views.check_deletion_type", return_value={"deletion_type": "Direct"})
    mock_delete_item_directly = mocker.patch("weko_swordserver.views.delete_item_directly")
    mocker.patch("weko_swordserver.views.lock_item_will_be_edit", return_value=True)
    mocker.patch("weko_swordserver.views.UserActivityLogger")

    url = url_for("weko_swordserver.delete_object", recid=2000001)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
    }

    res = client.delete(url, headers=headers)
    assert res.status_code == 204
    expected = {
        "remote_addr": request.remote_addr,
        "referrer": request.referrer,
        "hostname": request.host,
        "user_id": users[0]["id"],
        "shared_ids": [],
        "action": "DELETE"
    }
    mock_delete_item_directly.assert_called_once_with("2000001", request_info=expected)

    # direct deletion, being edited
    mocker.patch("weko_swordserver.views.lock_item_will_be_edit", return_value=False)
    res = client.delete(url, headers=headers)
    assert res.status_code == 400
    assert res.json.get("error") == "Item 2000001 will be edited by another process."

    # workflow deletion, not have activity scope
    login_user_via_session(client=client,email=users[1]["email"])
    mocker.patch("weko_swordserver.views.check_deletion_type", return_value={"deletion_type": "Workflow"})

    url = url_for("weko_swordserver.delete_object", recid=2000001)
    headers = {
        "Authorization": "Bearer {}".format(token_direct)
    }
    res = client.delete(url, headers=headers)
    assert res.status_code == 403
    assert res.json.get("error") == "Not allowed operation in your token scope."

    # workflow deletion, have activity scope, approval
    login_user_via_session(client=client,email=users[1]["email"])
    mock_delete_with_activity = mocker.patch("weko_swordserver.views.delete_items_with_activity")
    mock_delete_with_activity.return_value = ("url", "approval")
    headers = {
        "Authorization": "Bearer {}".format(token_workflow)
    }

    res = client.delete(url, headers=headers)
    assert res.status_code == 202
    mock_delete_with_activity.assert_called_once()

    # workflow deletion, have activity scope, end_action
    mock_delete_with_activity = mocker.patch("weko_swordserver.views.delete_items_with_activity")
    mock_delete_with_activity.return_value = ("url", "end_action")

    res = client.delete(url, headers=headers)
    assert res.status_code == 204
    mock_delete_with_activity.assert_called_once()

    # raise WekoWorkflowException
    with patch("weko_swordserver.views.delete_items_with_activity") as mock_delete_with_activity:
        mock_delete_with_activity.side_effect = WekoWorkflowException("test error")

        res = client.delete(url, headers=headers)
        assert res.status_code == 400
        assert res.json.get("error") == "Failed to delete item: test error"

    # raise unexpected Exception
    with patch("weko_swordserver.views.delete_items_with_activity") as mock_delete_with_activity:
        mock_delete_with_activity.side_effect = Exception("test error")

        res = client.delete(url, headers=headers)
        assert res.status_code == 400
        assert res.json.get("error") == "Unexpected error occurred during deletion: test error"

    # item with doi
    mock_record.pid_doi = "10.1234/test.00001"
    with patch("weko_swordserver.views.WekoRecord.get_record_by_pid", return_value=mock_record):
        res = client.delete(url, headers=headers)
        assert res.status_code == 400
        assert res.json.get("error") == "Cannot delete item with DOI."


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
