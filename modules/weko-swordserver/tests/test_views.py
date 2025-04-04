import os
from unittest.mock import MagicMock, PropertyMock,Mock
from flask import url_for,json,request,abort
from flask_login.utils import login_user
from zipfile import BadZipFile
import pytest
import datetime
from time import sleep
from unittest.mock import MagicMock, patch
import shutil
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
from weko_swordserver.utils import check_import_file_format,update_item_ids
from weko_search_ui.utils import import_items_to_system,import_items_to_activity
from weko_swordserver.utils import check_import_items,get_shared_id_from_on_behalf_of
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


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_post_service_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_post_service_document(app,client,db,users,make_crate,esindex,location,index,make_zip,tokens,item_type,doi_identifier,mocker,sword_mapping,sword_client,admin_settings):
    token_direct = tokens[0]["token"].access_token
    token_workflow = tokens[1]["token"].access_token
    token_none = tokens[3]["token"].access_token
    admin_settings[9].settings = {"data_format": {"TSV": {"item_type": "1", "register_format": "Direct"}, "XML": {"workflow": "1", "item_type": "1", "register_format": "Workflow"}}, "default_format": "TSV"}
    db.session.commit()
    url = url_for("weko_swordserver.post_service_document")

    # ケース1: Content-Dispositionが不正
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

    # ケース2: filenameがNone
    url = url_for("weko_swordserver.post_service_document")
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
    assert res.status_code == 400
    assert json.loads(res.data).get("@type") == "BadRequest"
    assert json.loads(res.data).get("error") == "Cannot get filename by Content-Disposition."

    # ケース3: ファイルが見つからない
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

    # ケース4: Digestなし (JSON)
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    login_user_via_session(client=client,email=users[0]["email"])
    with patch("weko_swordserver.views.check_import_file_format", return_value="JSON"):
        zip, _ = make_crate()
        storage = FileStorage(filename="payload.zip", stream=zip)
        headers = {
            "Authorization":"Bearer {}".format(token_direct),
            "Content-Disposition":"attachment; filename=payload.zip",
            "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
        }

        # POSTリクエストを送信
        res = client.post(
            url,
            data=dict(file=storage),
            content_type="multipart/form-data",
            headers=headers,
        )

        assert res.status_code == 412
        assert json.loads(res.data).get("@type") == "DigestMismatch"
        assert json.loads(res.data).get("error") == "Request body and digest verification failed."

    # ケース5: DigestがSHA-256でない
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    with patch("weko_swordserver.views.check_import_file_format", return_value="JSON"):
        zip, _ = make_crate()
        storage = FileStorage(filename="payload.zip", stream=zip)
        headers = {
            "Authorization":"Bearer {}".format(token_direct),
            "Content-Disposition":"attachment; filename=payload.zip",
            "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
            "Digest":"Md5=1234567890"
        }

        # POSTリクエストを送信
        res = client.post(
            url,
            data=dict(file=storage),
            content_type="multipart/form-data",
            headers=headers,
        )

        assert res.status_code == 412
        assert json.loads(res.data).get("@type") == "DigestMismatch"
        assert json.loads(res.data).get("error") == "Request body and digest verification failed."

    # ケース6: Digest不一致
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    with patch("weko_swordserver.views.check_import_file_format", return_value="JSON"):
        zip, _ = make_crate()
        storage = FileStorage(filename="payload.zip", stream=zip)
        headers = {
            "Authorization":"Bearer {}".format(token_direct),
            "Content-Disposition":"attachment; filename=payload.zip",
            "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
            "Digest":"SHA-256=1234567890"
        }

        # POSTリクエストを送信
        res = client.post(
            url,
            data=dict(file=storage),
            content_type="multipart/form-data",
            headers=headers,
        )

        assert res.status_code == 412
        assert json.loads(res.data).get("@type") == "DigestMismatch"
        assert json.loads(res.data).get("error") == "Request body and digest verification failed."

    # ケース6: Digest一致
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    login_user_via_session(client=client,email=users[0]["email"])
    with patch("weko_swordserver.views.check_import_file_format", return_value="JSON"):
        zip, _ = make_crate()
        storage = FileStorage(filename="payload.zip", stream=zip)
        headers = {
            "Authorization":"Bearer {}".format(token_direct),
            "Content-Disposition":"attachment; filename=payload.zip",
            "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
            "Digest":"SHA-256={}".format(calculate_hash(storage))
        }
        with patch("weko_swordserver.views.check_import_items", return_value={
            "data_path": "/tmp/test",
            "list_record": [{"status": "new"}],
            "register_type": "Direct"
        }):
            with patch("weko_swordserver.views.get_shared_id_from_on_behalf_of", return_value="share_id"):
                with patch("weko_swordserver.views.import_items_to_system", return_value={"success": True,  "recid": "recid_test"}):
                    with patch("weko_swordserver.views._get_status_document", return_value={"status": "created"}):
                        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
                        assert json.loads(res.data)=={"status": "created"}

    # ケース6: registration typeでエラー　かつ　data_pathが存在している場合
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True
    login_user_via_session(client=client,email=users[0]["email"])
    with patch('shutil.rmtree') as mock_rmtree:
        with patch("weko_swordserver.views.check_import_file_format", return_value="JSON"):
            zip, _ = make_crate()
            storage = FileStorage(filename="payload.zip", stream=zip)
            headers = {
                "Authorization":"Bearer {}".format(token_direct),
                "Content-Disposition":"attachment; filename=payload.zip",
                "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
                "Digest":"SHA-256={}".format(calculate_hash(storage))
            }
            with patch("weko_swordserver.views.check_import_items", return_value={
                "data_path": "/tmp/test",
                "list_record": [{"status": "new"}]
            }):
                with patch("os.path.exists", return_value=True):
                    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
                    assert res.status_code == 500
                    assert json.loads(res.data).get("@type") == "ServerError"
                    assert json.loads(res.data).get("error") == "Invalid register type in admin settings"
                    mock_rmtree.assert_called_with("/tmp/test")

    # ケース7: registration typeでエラー　かつ　data_pathが存在していない場合
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test_data_path",
        "list_record": [{"status": "new", "item_title": "Test Item"}]
    }):
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        assert res.status_code == 500
        assert json.loads(res.data).get("@type") == "ServerError"
        assert json.loads(res.data).get("error") == "Invalid register type in admin settings"


    # ケース8: check_import_itemsでエラー
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test_data_path",
        "register_type": "Direct",
        "list_record": [{"errors": "error example", "item_title": "Test Item"}]
    }):
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        assert res.status_code == 400
        assert json.loads(res.data).get("@type") == "ContentMalformed"
        assert "Error in check_import_items:" in json.loads(res.data).get("error")

    # ケース9: 既存アイテム
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test_data_path",
        "register_type": "Direct",
        "list_record":[{"status": "existing", "item_title": "Test Item"}],
    }):
        res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
        assert res.status_code == 400
        assert json.loads(res.data).get("@type") == "BadRequest"
        assert json.loads(res.data).get("error") == "This item is already registered: Test Item"

    # ケース10: Direct - import失敗
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test",
        "list_record": [{"status": "new"}],
        "register_type": "Direct"
    }):
        with patch("weko_swordserver.views.import_items_to_system", return_value={"success": False, "error_id": "err1"}):
            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
            assert res.status_code == 500
            assert json.loads(res.data).get("@type") == "ServerError"
            assert json.loads(res.data).get("error") == "An error occurred by importing Item!"

    # ケース11: Direct - 成功
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test",
        "list_record": [{"status": "new"}],
        "register_type": "Direct"
    }):
        with patch("weko_swordserver.views.import_items_to_system", return_value={"success": True,  "recid": "recid_test"}):
            with patch("weko_swordserver.views._get_status_document", return_value={"status": "created"}):
                res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
                assert json.loads(res.data)=={"status": "created"}

    # # ケース12: Workflow - activity スコープ不足
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test",
        "list_record": [{"status": "new"}],
        "register_type": "Workflow"
    }):
        # POSTリクエストを送信
        res = client.post(
            url_for("weko_swordserver.post_service_document"),
            data=dict(file=storage),
            content_type="multipart/form-data",
            headers=headers,
        )
        # レスポンスの検証
        print("res.data:",res.data)
        assert res.status_code == 403
        assert res.json.get("@type") == "Forbidden"
        assert res.json.get("error") == "Not allowed operation in your token scope."

    # ケース13: Workflow - importエラー
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_workflow),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test",
        "list_record": [{"status": "new"}],
        "register_type": "Workflow"
    }):
        with patch("weko_swordserver.views.import_items_to_activity", return_value=(
            "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002",
            "test_recid",
            "item_login",
            True
            )):

            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
            assert "An error occurred. Please open the following URL to " \
                "continue with the remaining operations." \
                "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002: " \
                "Item id: test_recid." in json.loads(res.data).get("error")

    # ケース14: Workflow - 成功
    login_user_via_session(client=client,email=users[0]["email"])
    with patch('shutil.rmtree') as mock_rmtree:
        mock_rmtree.reset_mock()
        with patch("weko_swordserver.views.check_import_file_format", return_value="JSON"):
            zip = make_zip()
            storage=FileStorage(filename="payload.zip",stream=zip)
            headers = {
                "Authorization":"Bearer {}".format(token_workflow),
                "Content-Disposition":"attachment; filename=payload.zip",
                "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
                "Digest":"SHA-256={}".format(calculate_hash(storage))
            }
            test_dir = "/tmp/test"
            os.makedirs(test_dir, exist_ok=True)
            with patch("weko_swordserver.views.check_import_items", return_value={
                "data_path": test_dir,
                "list_record": [{"status": "new"}],
                "register_type": "Workflow"
            }):

                with patch("weko_swordserver.views.import_items_to_activity", return_value=(
                    "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002",
                    "test_recid",
                    "item_login",
                    False
                    )):
                    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
                    mock_rmtree.assert_called_with("/tmp/test")
                    assert "An error occurred. " not in json.loads(res.data)
                    shutil.rmtree(test_dir)

    # ケース15: 複数なWorkflow - 一番目失敗、二番目成功
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_workflow),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test",
        "list_record": [{"status": "new"},{"status": "new"}],
        "register_type": "Workflow"
    }):
        with patch("weko_swordserver.views.import_items_to_activity", side_effect=[(
            "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002",
            "test_recid",
            "item_login",
            False),
            ("http://test_server.localdomain/workflow/activity/detail/A-TEST-00001",
            "test_recid",
            "item_login",
            True)
            ]):

            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
            assert "An error occurred. " not in json.loads(res.data)

    # ケース18: process_item - 予期しない例外
    login_user_via_session(client=client,email=users[0]["email"])
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with patch("weko_swordserver.views.check_import_items", return_value={
        "data_path": "/tmp/test",
        "list_record": [{"status": "new"}],
        "register_type": "Direct"
    }):
        with patch("weko_swordserver.views.import_items_to_system", side_effect=Exception("Exception")):
            res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
            assert json.loads(res.data).get("@type") == "NotFound"
            assert json.loads(res.data).get("error") =="Item not found. (recid=None)"
