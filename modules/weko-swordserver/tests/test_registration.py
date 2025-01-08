# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import os
import pytest
import bagit
from unittest.mock import MagicMock, patch

from werkzeug.datastructures import FileStorage

from zipfile import BadZipFile
from sqlalchemy.exc import SQLAlchemyError

from weko_search_ui.utils import handle_validate_item_import
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.registration import check_bagit_import_items, generate_metadata_from_json, handle_files_info
from weko_swordserver.utils import unpack_zip

from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def check_bagit_import_items(file, packaging):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_check_bagit_import_items -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_bagit_import_items(app,db,index,users,tokens,sword_mapping,sword_client,make_crate,mocker,workflow):
    # sucsess case for publish_status is "public". It is required to scope "deposit:actions".
    client_id = tokens[2]["client"].client_id

    # mock_request = mocker.patch("weko_swordserver.registration.request")
    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        mapped_json = json_data("data/item_type/mapped_json_2.json")
        mock_map = mocker.patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json)

        zip, _ = make_crate()
        storage = FileStorage(filename="payload.zip",stream=zip)
        packaging = "http://purl.org/net/sword/3.0/package/SimpleZip"

        with app.test_request_context():
            result = check_bagit_import_items(storage,packaging)

        mock_map.assert_called_once()

    assert result.get("data_path").startswith("/tmp/weko_import_")
    assert result.get("register_format") == "Direct"
    assert result.get("item_type_id") == 2
    assert result.get("error") is None


    # Case # 1
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

            zip, _ = make_crate()
            file = FileStorage(filename=file_name, stream=zip)

            with app.test_request_context(headers=headers):
                with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                    res = check_bagit_import_items(file, packaging[0])
                    assert not hasattr(res, "error")
                    assert res["list_record"][0]["errors"] is None


    # Case # 2
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

            zip, _ = make_crate()
            file = FileStorage(filename=file_name, stream=zip)

            with app.test_request_context(headers=headers):
                with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                    with patch("weko_swordserver.registration.handle_files_info", side_effect=Exception("Test error message.")) as mock_handle_files_info:
                        res = check_bagit_import_items(file, packaging[0])
                        assert res["error"] == "Test error message."
                        mock_handle_files_info.assert_called_once()


    # Case # 3
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

            zip, _ = make_crate()
            file = FileStorage(filename=file_name, stream=zip)

            with app.test_request_context(headers=headers):
                with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                    def mock_handle(*args, **kwargs):
                        list_record = args[0]
                        list_record[0]["id"] = "１"
                        modified_args = (list_record,) + args[1:]
                        return handle_validate_item_import(*modified_args, **kwargs)
                    with patch("weko_swordserver.registration.handle_validate_item_import", side_effect=mock_handle) as mock_handle_validate_item_import:
                        res = check_bagit_import_items(file, packaging[0])
                        errors = res["list_record"][0]["errors"]
                        assert 'Please specify item ID by half-width number.' in errors
                        assert 'Specified URI and system URI do not match.' in errors
                        mock_handle_validate_item_import.assert_called_once()


    # Case # 4
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        zip, _ = make_crate()
        file = FileStorage(filename=file_name, stream=zip)

        with app.test_request_context(headers=headers):
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                with patch("weko_swordserver.registration.json.load", side_effect=UnicodeDecodeError) as mock_json_load:
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "function takes exactly 5 arguments (0 given)"
                    mock_json_load.assert_called_once()


    # Case # 5
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        zip, _ = make_crate()
        file = FileStorage(filename=file_name, stream=zip)

        with app.test_request_context(headers=headers):
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                with patch("weko_swordserver.registration.ItemTypes.get_by_id", return_value=None) as mock_get_by_id:
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "Item type not found for registration your item."
                    mock_get_by_id.assert_called_once()


    # Case # 6
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]
    workflow_ = workflow["workflow"]
    original_itemtype_id = workflow_.itemtype_id
    workflow_.itemtype_id = 1
    db.session.commit()

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        zip, _ = make_crate()
        file = FileStorage(filename=file_name, stream=zip)

        with app.test_request_context(headers=headers):
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)) as mock_get_record_by_client_id:
                res = check_bagit_import_items(file, packaging[0])
                assert res["error"] == "Item type and workflow do not match."
                mock_get_record_by_client_id.assert_called_once()
    workflow_.itemtype_id = original_itemtype_id
    db.session.commit()


    # Case # 7
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        zip, _ = make_crate()
        file = FileStorage(filename=file_name, stream=zip)

        with app.test_request_context(headers=headers):
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                with patch("weko_swordserver.registration.WorkFlow.get_workflow_by_id", return_value=None) as mock_get_workflow_by_id:
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "Workflow not found for registration your item."
                    mock_get_workflow_by_id.assert_called_once()


    # Case # 8
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[0]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

            zip, _ = make_crate()
            file = FileStorage(filename=file_name, stream=zip)

            with app.test_request_context(headers=headers):
                res = check_bagit_import_items(file, packaging[0])
                assert not hasattr(res, "error")
                assert res["list_record"][0]["errors"] is None


    # Case # 9
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[0]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

            zip, _ = make_crate()
            file = FileStorage(filename=file_name, stream=zip)

            with app.test_request_context(headers=headers):
                with patch("weko_swordserver.registration.handle_files_info", side_effect=Exception("Test error message.")) as mock_handle_files_info:
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "Test error message."
                    mock_handle_files_info.assert_called_once()


    # Case # 10
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[0]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        mapped_json = json_data("data/item_type/mapped_json_2.json")
        with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped_json):

            zip, _ = make_crate()
            file = FileStorage(filename=file_name, stream=zip)

            with app.test_request_context(headers=headers):
                def mock_handle(*args, **kwargs):
                    list_record = args[0]
                    list_record[0]["id"] = "１"
                    modified_args = (list_record,) + args[1:]
                    return handle_validate_item_import(*modified_args, **kwargs)
                with patch("weko_swordserver.registration.handle_validate_item_import", side_effect=mock_handle) as mock_handle_validate_item_import:
                    res = check_bagit_import_items(file, packaging[0])
                    errors = res["list_record"][0]["errors"]
                    assert 'Please specify item ID by half-width number.' in errors
                    assert 'Specified URI and system URI do not match.' in errors
                    mock_handle_validate_item_import.assert_called_once()


    # Case # 11
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[0]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        zip, _ = make_crate()
        file = FileStorage(filename=file_name, stream=zip)

        with app.test_request_context(headers=headers):
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                with patch("weko_swordserver.registration.json.load", side_effect=UnicodeDecodeError) as mock_json_load:
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "function takes exactly 5 arguments (0 given)"
                    mock_json_load.assert_called_once()


    # Case # 12
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[0]["sword_client"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        zip, _ = make_crate()
        file = FileStorage(filename=file_name, stream=zip)

        with app.test_request_context(headers=headers):
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                with patch("weko_swordserver.registration.ItemTypes.get_by_id", return_value=None) as mock_get_by_id:
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "Item type not found for registration your item."
                    mock_get_by_id.assert_called_once()


    # Case # 13
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]

    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }

    with patch("weko_swordserver.registration.request") as mock_request:
        mock_oauth = MagicMock()
        mock_oauth.client.client_id = client_id
        mock_oauth.access_token.scopes = tokens[2]["scope"].split(" ")
        mock_request.oauth = mock_oauth

        zip, _ = make_crate()
        file = FileStorage(filename=file_name, stream=zip)

        with app.test_request_context(headers=headers):
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword_client, None)) as mock_get_record_by_client_id:
                res = check_bagit_import_items(file, packaging[0])
                assert res["error"] == "Metadata mapping not defined for registration your item."
                mock_get_record_by_client_id.assert_called_once()

    # Case # 14
    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    data_path = "test_data_path"
    zip, _ = make_crate()
    file = FileStorage(filename=file_name, stream=zip)
    user_email = users[0]["email"]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }
    with app.test_request_context(headers=headers):
        with patch("weko_swordserver.registration.unpack_zip") as mock_unpack_zip:
            mock_unpack_zip.return_value = data_path, []
            with patch("bagit.Bag", side_effect=bagit.BagValidationError) as mock_bag:
                res = check_bagit_import_items(file, packaging[0])
                assert res == {
                    "data_path": data_path,
                    "error": "__init__() missing 1 required positional argument: 'message'"
                }
                mock_bag.assert_called_once()


    # Case # 15
    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    zip, _ = make_crate()
    file = FileStorage(filename=file_name, stream=zip)
    user_email = users[0]["email"]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }
    with app.test_request_context(headers=headers):
        with patch("weko_swordserver.registration.unpack_zip", side_effect=BadZipFile) as mock_unpack_zip:
            res = check_bagit_import_items(file, packaging[0])
            assert res == {
                "error": f"The format of the specified file {file_name} dose not "
                + "support import. Please specify a zip file."
            }
            mock_unpack_zip.assert_called_once()


    # Case # 16
    file_name = "mockfile.zip"
    packaging = [
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
    ]
    zip, _ = make_crate()
    file = FileStorage(filename=file_name, stream=zip)
    user_email = users[0]["email"]
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": user_email,
    }
    with app.test_request_context(headers=headers):
        with patch("weko_swordserver.registration.User.query", new_callable=MagicMock) as mock_user_query:
            mock_filter_by = MagicMock()
            mock_filter_by.one_or_none.side_effect = SQLAlchemyError
            mock_user_query.filter_by.return_value = mock_filter_by
            with pytest.raises(WekoSwordserverException) as e:
                check_bagit_import_items(file, packaging[0])
                mock_user_query.filter_by.assert_called_once_with(email=user_email)
            assert e.value.errorType == ErrorType.ServerError
            assert e.value.message == "An error occurred while searching user by On-Behalf-Of."

    access_token = tokens[0]["token"].access_token
    headers["On-Behalf-Of"] = access_token
    with app.test_request_context(headers=headers):
        with patch("weko_swordserver.registration.Token.query", new_callable=MagicMock) as mock_token_query:
            mock_filter_by = MagicMock()
            mock_filter_by.one_or_none.side_effect = SQLAlchemyError
            mock_token_query.filter_by.return_value = mock_filter_by
            with pytest.raises(WekoSwordserverException) as e:
                check_bagit_import_items(file, packaging[0])
                mock_token_query.filter_by.assert_called_once_with(access_token=access_token)
            assert e.value.errorType == ErrorType.ServerError
            assert e.value.message == "An error occurred while searching user by On-Behalf-Of."

    shib_eppn = "test_shib_eppn"
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": shib_eppn,
    }
    with app.test_request_context(headers=headers):
        with patch("weko_swordserver.registration.ShibbolethUser.query", new_callable=MagicMock) as mock_shib_query:
            mock_filter_by = MagicMock()
            mock_filter_by.one_or_none.side_effect = SQLAlchemyError
            mock_shib_query.filter_by.return_value = mock_filter_by
            with pytest.raises(WekoSwordserverException) as e:
                check_bagit_import_items(file, packaging[0])
                mock_shib_query.filter_by.assert_called_once_with(shib_eppn=shib_eppn)
            assert e.value.errorType == ErrorType.ServerError
            assert e.value.message == "An error occurred while searching user by On-Behalf-Of."



# def generate_metadata_from_json(json, mapping, item_type, is_change_identifier=False):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_generate_metadata_from_json -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_generate_metadata_from_json(app,db,index,users,tokens,sword_mapping,sword_client,item_type,make_crate,mocker,workflow):
    # sucsess case for publish_status is "public". It is required to scope "deposit:actions".

    # Case # 17
    sword__mapping = sword_mapping[0]["sword_mapping"]
    item__type = item_type[0]["item_type"]
    mapped__json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped__json) as mock_map:
        with app.test_request_context():
            res = generate_metadata_from_json(mapped__json, sword__mapping, item__type)
            assert len(res) == 1
            assert res[0]["errors"] is None, "errors is not None"
        mock_map.assert_called_once()

    # Case # 18
    sword__mapping = sword_mapping[0]["sword_mapping"]
    item__type = item_type[0]["item_type"]
    mapped__json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped__json) as mock_map:
        with app.test_request_context():
            with patch.dict("flask.current_app.config", {"WEKO_HANDLE_ALLOW_REGISTER_CNRI": True}):
                res = generate_metadata_from_json(mapped__json, sword__mapping, item__type, True)
                assert len(res) == 1
                assert res[0]["is_change_identifier"] is True, "errors is not True"
        mock_map.assert_called_once()

    # Case # 19
    sword__mapping = sword_mapping[0]["sword_mapping"]
    item__type = item_type[0]["item_type"]
    mapped__json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped__json) as mock_map:
        with app.test_request_context():
            with patch.dict("flask.current_app.config", {"WEKO_HANDLE_ALLOW_REGISTER_CNRI": True}):
                res = generate_metadata_from_json(mapped__json, sword__mapping, item__type, False)
                assert len(res) == 1
                assert res[0]["is_change_identifier"] is False, "errors is not False"
        mock_map.assert_called_once()



# def handle_files_info(list_record, files_list, data_path, filename):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_handle_files_info -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_handle_files_info(app,sword_mapping,item_type,make_crate):
    # sucsess case for publish_status is "public". It is required to scope "deposit:actions".

    # Case # 20
    file__name = "payload.zip"
    zip, _ = make_crate()
    storage = FileStorage(filename=file__name,stream=zip)
    data__path, files__list = unpack_zip(storage)

    sword__mapping = sword_mapping[0]["sword_mapping"]
    item__type = item_type[0]["item_type"]
    mapped__json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped__json):
        with app.test_request_context():
            list__record = generate_metadata_from_json(mapped__json, sword__mapping, item__type)
            res = handle_files_info(list__record, files__list, data__path, file__name)
            print("res:" + str(res))
            assert len(res) == 1
            assert res[0]["errors"] is None
            assert len(res[0]["file_path"]) > 0


    # Case # 21
    file__name = "payload.zip"
    zip, _ = make_crate()
    storage = FileStorage(filename=file__name,stream=zip)
    data__path, files__list = unpack_zip(storage)

    sword__mapping = sword_mapping[0]["sword_mapping"]
    item__type = item_type[0]["item_type"]
    mapped__json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped__json):
        with app.test_request_context():
            list__record = generate_metadata_from_json(mapped__json, sword__mapping, item__type)
            res = handle_files_info(list__record, [], data__path, file__name)
            print("res:" + str(res))
            assert len(res) == 1
            assert res[0]["errors"] is None, "errors is not None"
            assert not hasattr(res[0], 'file_path')


    # Case # 22
    file__name = "payload.zip"
    zip, file__size = make_crate()
    storage = FileStorage(filename=file__name,stream=zip)
    data__path, files__list = unpack_zip(storage)

    storage.seek(0, 0)
    storage.save(os.path.join(data__path, "data", file__name))

    sword__mapping = sword_mapping[0]["sword_mapping"]
    item__type = item_type[0]["item_type"]
    mapped__json = json_data("data/item_type/mapped_json_2.json")
    with patch("weko_swordserver.mapper.WekoSwordMapper.map",return_value=mapped__json):
        with app.test_request_context():
            with patch.dict("flask.current_app.config", {"WEKO_SWORDSERVER_DEPOSIT_DATASET": True}):
                list__record = generate_metadata_from_json(mapped__json, sword__mapping, item__type)
                res = handle_files_info(list__record, files__list, data__path, file__name)
                assert len(res) == 1
                assert res[0]["errors"] is None, "errors is not None"
                assert res[0]["metadata"]["files_info"][0]["items"][1]["filesize"][0]["value"] == str(file__size)
