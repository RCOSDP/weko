# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
import bagit
from unittest.mock import MagicMock, patch

from werkzeug.datastructures import FileStorage

from zipfile import BadZipFile
from sqlalchemy.exc import SQLAlchemyError

from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.registration import check_bagit_import_items

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


    # Case # 4 XXX
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]
    workflow_ = workflow["workflow"]
    original_itemtype_id = workflow_.itemtype_id

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
                with patch("weko_swordserver.registration.ItemTypes.get_by_id", return_value=None):
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "Item type not found for registration your item."


    # Case # 5
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword__mapping = sword_mapping[0]["sword_mapping"]
    sword__client = sword_client[1]["sword_client"]
    workflow_ = workflow["workflow"]
    original_itemtype_id = workflow_.itemtype_id

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
                with patch("weko_swordserver.registration.ItemTypes.get_by_id", return_value=None):
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "Item type not found for registration your item."


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
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword__client, sword__mapping)):
                res = check_bagit_import_items(file, packaging[0])
                assert res["error"] == "Item type and workflow do not match."
    workflow_.itemtype_id = original_itemtype_id
    db.session.commit()

    # Case # 7
    client_id = tokens[2]["client"].client_id
    user_email = users[2]["email"]
    sword_mapping = sword_mapping[0]["sword_mapping"]
    sword_client = sword_client[1]["sword_client"]

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
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword_client, sword_mapping)):
                with patch("weko_swordserver.registration.WorkFlow.get_workflow_by_id", return_value=None):
                    res = check_bagit_import_items(file, packaging[0])
                    assert res["error"] == "Workflow not found for registration your item."

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
            with patch("weko_swordserver.registration.get_record_by_client_id", return_value=(sword_client, None)):
                res = check_bagit_import_items(file, packaging[0])
                assert res["error"] == "Metadata mapping not defined for registration your item."

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
        with patch("weko_swordserver.registration.unpack_zip") as unpack_zip:
            unpack_zip.return_value = data_path, []
            with patch("bagit.Bag", side_effect=bagit.BagValidationError):
                res = check_bagit_import_items(file, packaging[0])
                assert res == {
                    "data_path": data_path,
                    "error": "__init__() missing 1 required positional argument: 'message'"
                }

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
        with patch("weko_swordserver.registration.unpack_zip", side_effect=BadZipFile):
            res = check_bagit_import_items(file, packaging[0])
            assert res == {
                "error": f"The format of the specified file {file_name} dose not "
                + "support import. Please specify a zip file."
            }

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
        with patch(
            "weko_swordserver.registration.User.query", new_callable=MagicMock
        ) as mock_db:
            mock_filter_by = MagicMock()
            mock_filter_by.one_or_none.side_effect = SQLAlchemyError
            mock_db.filter_by.return_value = mock_filter_by
            with pytest.raises(WekoSwordserverException) as e:
                check_bagit_import_items(file, packaging[0])
                mock_db.filter_by.assert_called_once_with(email=user_email)
            assert e.value.errorType == ErrorType.ServerError
            assert e.value.message == (
                "An error occurred while searching user by On-Behalf-Of."
            )

    access_token = tokens[0]["token"].access_token
    headers["On-Behalf-Of"] = access_token
    with app.test_request_context(headers=headers):
        with patch(
            "weko_swordserver.registration.Token.query", new_callable=MagicMock
        ) as mock_db:
            mock_filter_by = MagicMock()
            mock_filter_by.one_or_none.side_effect = SQLAlchemyError
            mock_db.filter_by.return_value = mock_filter_by
            with pytest.raises(WekoSwordserverException) as e:
                check_bagit_import_items(file, packaging[0])
                mock_db.filter_by.assert_called_once_with(access_token=access_token)
            assert e.value.errorType == ErrorType.ServerError
            assert e.value.message == (
                "An error occurred while searching user by On-Behalf-Of."
            )

    shib_eppn = "test_shib_eppn"
    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment;filename={file_name}",
        "Packaging": packaging[0],
        "On-Behalf-Of": shib_eppn,
    }
    with app.test_request_context(headers=headers):
        with patch(
            "weko_swordserver.registration.ShibbolethUser.query",
            new_callable=MagicMock,
        ) as mock_db:
            mock_filter_by = MagicMock()
            mock_filter_by.one_or_none.side_effect = SQLAlchemyError
            mock_db.filter_by.return_value = mock_filter_by
            with pytest.raises(WekoSwordserverException) as e:
                check_bagit_import_items(file, packaging[0])
                mock_db.filter_by.assert_called_once_with(shib_eppn=shib_eppn)
            assert e.value.errorType == ErrorType.ServerError
            assert e.value.message == (
                "An error occurred while searching user by On-Behalf-Of."
            )


