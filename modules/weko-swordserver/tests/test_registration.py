# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from unittest.mock import MagicMock, patch

from werkzeug.datastructures import FileStorage

from weko_swordserver.registration import check_bagit_import_items

from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def check_bagit_import_items(file, packaging):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_registration.py::test_check_bagit_import_items -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_bagit_import_items(app,db,index,users,tokens,sword_mapping,sword_client,make_crate,mocker):
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


