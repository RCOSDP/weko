
from zipfile import BadZipFile
import pytest
import datetime
from time import sleep
from unittest.mock import MagicMock, patch

from flask import url_for,json,abort
from sword3common.lib.seamless import SeamlessException
from werkzeug.datastructures import FileStorage

from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier
from invenio_files_rest.models import Location
from invenio_records.models import RecordMetadata

from weko_search_ui.utils import check_import_items, handle_check_date, handle_check_exist_record, import_items_to_system
from weko_swordserver.errors import *
from weko_swordserver.registration import check_bagit_import_items, generate_metadata_from_json
from weko_swordserver.views import blueprint, _get_status_document,_create_error_document,post_service_document
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


# def post_service_document():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_views.py::test_post_service_document -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_post_service_document(app,client,db,users,esindex,location,index,make_zip,tokens,item_type,doi_identifier,mocker,sword_mapping,sword_client):
    login_user_via_session(client=client,email=users[0]["email"])
    token_direct = tokens[0]["token"].access_token
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
    zip = make_zip()
    storage = FileStorage(filename="payload.zip",stream=zip)
    res = client.post(url, data=dict(file=storage),content_type="multipart/form-data",headers=headers)
    assert res.status_code == 200

    recid = PersistentIdentifier.get("recid","1").object_uuid
    record = RecordMetadata.query.filter_by(id=recid).one_or_none()
    assert record is not None
    record = record.json
    file_metadata = record["item_1617605131499"]["attribute_value_mlt"][0]
    assert file_metadata.get("url") is not None
    assert file_metadata.get("url").get("url") == "https://localhost/record/1/files/sample.html"
    assert res.json == {"recid":"1"}

    zip = make_zip()
    storage=FileStorage(filename="payload.zip",stream=zip)
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        # exist "error" in check_result
        checked = {"error":"test_check_error","item":"test_item"}
        with patch("weko_search_ui.utils.check_import_items",return_value=checked):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
                assert e.errorType == ErrorType.ServerError
                assert e.message == "Error in check_import_items: test_check_error"

        # exist "error" in item
        checked = {"error":"","item":{"errors":["this is test item error1","this is test item error2"]}}
        with patch("weko_search_ui.utils.check_import_items",return_value=checked):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
                assert e.errorType == ErrorType.ContentMalformed
                assert e.message == "Error in check_import_items: this is test item error1, this is test item error2"

        # else
        checked = {"error":"","item":{}}
        with patch("weko_search_ui.utils.check_import_items",return_value=checked):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
                assert e.errorType == ErrorType.ContentMalformed
                assert e.message == "Error in check_import_items: item_missing"

        # item.status is not new
        checked = {"error":"","item":{"status":"update","item_title":"not_new_item"}}
        with patch("weko_search_ui.utils.check_import_items",return_value=checked):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
                assert e.errorType == ErrorType.BadRequest
                assert e.message == "This item is already registered: not_new_item"

        # import failed
        checked = {"error":"","item":{"status":"new","item_title":"new_item"}}
        with patch("weko_search_ui.utils.check_import_items",return_value=checked):
            with patch("weko_swordserver.views.import_items_to_system",return_value={"error_id":"test error in import"}):
                with pytest.raises(WekoSwordserverException) as e:
                    post_service_document()
                    assert e.errorType == ErrorType.ServerError
                    assert e.message == "Error in import_items_to_system: test error in import"


    # case # 9
    zip = make_zip()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            def mock_import_items_to_system(*args, **kwargs):
                res = import_items_to_system(*args, **kwargs)
                res["success"] = True
                return res
            with patch("weko_swordserver.views.import_items_to_system",side_effect=mock_import_items_to_system):
                res = post_service_document()
                assert res.status_code == 200


    # case # 10
    zip = make_zip()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            def mock_import_items_to_system(*args, **kwargs):
                res = import_items_to_system(*args, **kwargs)
                res["success"] = False
                return res
            with patch("weko_swordserver.views.import_items_to_system",side_effect=mock_import_items_to_system):
                with pytest.raises(WekoSwordserverException) as e:
                    post_service_document()
                assert e.value.errorType == ErrorType.ServerError
                assert e.value.message.startswith("Error in import_items_to_system: ")


    # case # 11-13 TODO


    # case # 14
    zip = make_zip()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with patch("weko_swordserver.views.check_import_file_format",return_value="OTHERS"):
                def mock_check_import_items(*args, **kwargs):
                    res = check_import_items(*args, **kwargs)
                    res["list_record"][0]["status"] = "update"
                    return res
                with patch("weko_search_ui.utils.check_import_items",side_effect=mock_check_import_items):
                    with pytest.raises(WekoSwordserverException) as e:
                        post_service_document()
                    assert e.value.errorType == ErrorType.BadRequest
                    assert e.value.message.startswith("This item is already registered: ")


    # case # 15
    # ErrorType.ServerError
    zip = make_zip()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with patch("weko_swordserver.views.check_import_file_format",return_value="OTHERS"):
                with patch("weko_search_ui.utils.unpackage_import_file",side_effect=FileNotFoundError):
                    with pytest.raises(WekoSwordserverException) as e:
                        post_service_document()
                    assert e.value.errorType == ErrorType.ServerError
                    assert e.value.message == f"Error in check_import_items: The csv/tsv file was not found in the specified file {file_name}. Check if the directory structure is correct."

    # ErrorType.ContentMalformed
    zip = make_zip()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with patch("weko_swordserver.views.check_import_file_format",return_value="OTHERS"):
                def mock_handle_check_date(*args, **kwargs):
                    list_record = args[0]
                    list_record[0]["metadata"]["pubdate"] = "20221111"
                    modified_args = (list_record,) + args[1:]
                    return handle_check_date(*modified_args, **kwargs)
                with patch("weko_search_ui.utils.handle_check_date", side_effect=mock_handle_check_date):
                    with pytest.raises(WekoSwordserverException) as e:
                        post_service_document()
                    assert e.value.errorType == ErrorType.ContentMalformed
                    assert e.value.message == "Error in check_import_items: Please specify PubDate with YYYY-MM-DD."

    # not item
    zip = make_zip()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with patch("weko_swordserver.views.check_import_file_format",return_value="OTHERS"):
                def mock_check_import_items(*args, **kwargs):
                    res = check_import_items(*args, **kwargs)
                    del res["list_record"]
                    return res
                with patch("weko_search_ui.utils.check_import_items", side_effect=mock_check_import_items):
                    with pytest.raises(WekoSwordserverException) as e:
                        post_service_document()
                    assert e.value.errorType == ErrorType.ContentMalformed
                    assert e.value.message == "Error in check_import_items: item_missing"


    # case # 16
    zip = make_zip()
    file_name = "payload.zip"
    file_name2 = "payload2.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name2}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
            assert e.value.errorType == ErrorType.BadRequest
            assert e.value.message == f"Not found {file_name2} in request body."


    # case # 17
    zip = make_zip()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":"",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
            assert e.value.errorType == ErrorType.BadRequest
            assert e.value.message == "Cannot get filename by Content-Disposition."



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

    token_direct = tokens[0]["token"].access_token
    token_workflow = tokens[1]["token"].access_token
    token_none = tokens[3]["token"].access_token
    # Digest VERIFICATION ON
    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True

    # Direct registration
    url = url_for("weko_swordserver.post_service_document")
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
    mapped_json = json_data("data/item_type/mapped_json_2.json")
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


    # invalid Content-Length
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = False

    # invalid Content-Length and be rejected
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True

    # print("Workflow registration")
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = False
    # mocker.patch("weko_swordserver.views._get_status_workflow_document",side_effect=lambda a,x:{"activity":a.id,"recid":x})

    # Workflow registration
    zip, _ = make_crate()
    storage = FileStorage(filename="payload.zip",stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_workflow),
        "Content-Disposition":"attachment; filename=payload.zip",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    mapped_json = json_data("data/item_type/mapped_json_2.json")
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
        # assert file_metadata.get("url").get("url") == f"https://localhost/record/{recid.id}/files/sample.rst"

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


    app.config["WEKO_SWORDSERVER_DIGEST_VERIFICATION"] = True

    # case # 1
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            def mock_import_items_to_system(*args, **kwargs):
                res = import_items_to_system(*args, **kwargs)
                res["success"] = True
                return res
            with patch("weko_swordserver.views.import_items_to_system",side_effect=mock_import_items_to_system):
                res = post_service_document()
                assert res.status_code == 200


    # case # 2
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            def mock_import_items_to_system(*args, **kwargs):
                res = import_items_to_system(*args, **kwargs)
                res["success"] = False
                return res
            with patch("weko_swordserver.views.import_items_to_system",side_effect=mock_import_items_to_system):
                with pytest.raises(WekoSwordserverException) as e:
                    post_service_document()
                assert e.value.errorType == ErrorType.ServerError
                assert e.value.message.startswith("Error in import_items_to_system: ")


    # case # 3-5 TODO


    # case # 6
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            def mock_handle_check_exist_record(*args, **kwargs):
                res = handle_check_exist_record(*args, **kwargs)
                res[0]["status"] = None
                return res
            with patch("weko_swordserver.registration.handle_check_exist_record",side_effect=mock_handle_check_exist_record):
                with pytest.raises(WekoSwordserverException) as e:
                    post_service_document()
                assert e.value.errorType == ErrorType.BadRequest
                assert e.value.message.startswith("This item is already registered: ")


    # case # 7
    # ErrorType.ServerError
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with patch("weko_swordserver.registration.unpack_zip", side_effect=BadZipFile):
                with pytest.raises(WekoSwordserverException) as e:
                    post_service_document()
                assert e.value.errorType == ErrorType.ServerError
                assert e.value.message == f"Error in check_import_items: The format of the specified file {file_name} dose not support import. Please specify a zip file."

    # ErrorType.ContentMalformed
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            def mock_handle_check_date(*args, **kwargs):
                list_record = args[0]
                list_record[0]["metadata"]["pubdate"] = "20241115"
                modified_args = (list_record,) + args[1:]
                return handle_check_date(*modified_args, **kwargs)
            with patch("weko_swordserver.registration.handle_check_date", side_effect=mock_handle_check_date):
                with pytest.raises(WekoSwordserverException) as e:
                    post_service_document()
                assert e.value.errorType == ErrorType.ContentMalformed
                assert e.value.message == "Error in check_import_items: Please specify PubDate with YYYY-MM-DD."

    # not item
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            def mock_check_bagit_import_items(*args, **kwargs):
                res = check_bagit_import_items(*args, **kwargs)
                del res["list_record"]
                return res
            with patch("weko_swordserver.views.check_bagit_import_items", side_effect=mock_check_bagit_import_items):
                with pytest.raises(WekoSwordserverException) as e:
                    post_service_document()
                assert e.value.errorType == ErrorType.ContentMalformed
                assert e.value.message == "Error in check_import_items: item_missing"


    # case # 8
    # no digest
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
            assert e.value.errorType == ErrorType.DigestMismatch
            assert e.value.message == "Request body and digest verification failed."

    # not SHA-256
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-1={}".format(calculate_hash(storage))
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
            assert e.value.errorType == ErrorType.DigestMismatch
            assert e.value.message == "Request body and digest verification failed."

    # digest check failed
    zip, _  = make_crate()
    file_name = "payload.zip"
    storage = FileStorage(filename=file_name,stream=zip)
    headers = {
        "Authorization":"Bearer {}".format(token_direct),
        "Content-Disposition":f"attachment; filename={file_name}",
        "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip",
        "Digest":"SHA-256={}".format("dummydigest")
    }
    with app.test_request_context(url,method="POST",headers=headers,data=dict(file=storage)):
        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):
            with pytest.raises(WekoSwordserverException) as e:
                post_service_document()
            assert e.value.errorType == ErrorType.DigestMismatch
            assert e.value.message == "Request body and digest verification failed."



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
