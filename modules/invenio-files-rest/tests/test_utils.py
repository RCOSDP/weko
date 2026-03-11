# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Files download/upload REST API similar to S3 for Invenio."""

import botocore.client
from invenio_files_rest.utils import create_boto3_s3_client, parse_storage_host


# def create_boto3_s3_client(access_key, secret_key, region_name=None, endpoint_url=None, client_config={}):
# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_utils.py::test_create_boto3_s3_client -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_create_boto3_s3_client(app):
    # Test case (Pos): S3 credentials are not configured
    client = create_boto3_s3_client("access_key", "")
    assert client is None

    # Test case (Pos): client_config is set
    client = create_boto3_s3_client(
        "access_key", "secret_key",
        client_config={"user_agent": "UA", "region_name": "eu-west-1"})
    assert isinstance(client, botocore.client.BaseClient)
    assert client.meta.service_model.service_name == "s3"
    assert client.meta.config.user_agent == "UA"
    assert client.meta.region_name == "eu-west-1"
    assert client.meta.endpoint_url == "https://s3.eu-west-1.amazonaws.com"

    # Set app config for testing
    app.config.update({
        "FILES_REST_STORAGE_SERVICE_PATTERN": {
            "aws_s3": [
                r"^s3\.amazonaws\.com$",
                r"^s3\.(?P<region>.+)\.amazonaws\.com$",
                r"^(?P<bucket>.+)\.s3\.(?P<region>.+)\.amazonaws\.com$"
            ],
        }
    })

    # Test case (Pos): region_name is set
    client = create_boto3_s3_client(
        "access_key", "secret_key",
        region_name="us-west-1",
        endpoint_url="https://s3.amazonaws.com")
    assert isinstance(client, botocore.client.BaseClient)
    assert client.meta.service_model.service_name == "s3"
    assert client.meta.region_name == "us-west-1"
    assert client.meta.endpoint_url == "https://s3.us-west-1.amazonaws.com"

    # Test case (Pos): get region from endpoint url
    client = create_boto3_s3_client(
        "access_key", "secret_key",
        endpoint_url="https://s3.us-west-2.amazonaws.com")
    assert isinstance(client, botocore.client.BaseClient)
    assert client.meta.service_model.service_name == "s3"
    assert client.meta.region_name == "us-west-2"
    assert client.meta.endpoint_url == "https://s3.us-west-2.amazonaws.com"

    # Test case (Pos): not get region from endpoint url
    client = create_boto3_s3_client(
        "access_key", "secret_key",
        endpoint_url="https://s3.amazonaws.com")
    assert isinstance(client, botocore.client.BaseClient)
    assert client.meta.region_name == "us-east-1"
    assert client.meta.service_model.service_name == "s3"
    assert client.meta.endpoint_url == "https://s3.amazonaws.com"

    # Test case (Pos): other client
    client = create_boto3_s3_client(
        "access_key", "secret_key", endpoint_url="https://example.com")
    assert isinstance(client, botocore.client.BaseClient)
    assert client.meta.service_model.service_name == "s3"
    assert client.meta.endpoint_url == "https://example.com"


# def parse_storage_host(host):
# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_utils.py::test_parse_storage_host_match_service -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_parse_storage_host_match_service(app):
    # サービスパターン設定
    patterns = {
        "aws_s3": [
            r"^s3\.amazonaws\.com$",
            r"^(?P<bucket>.+)\.s3\.amazonaws\.com$"
        ],
        "wasabi": [
            r"^s3\.wasabisys\.com$",
            r"^s3\.(?P<region>[a-z0-9-]+)\.wasabisys\.com$"
        ],
    }
    mock_config = {"FILES_REST_STORAGE_SERVICE_PATTERN": patterns}
    app.config.update(mock_config)

    # Test case (Pos): Match aws_s3 pattern
    result = parse_storage_host("s3.amazonaws.com")
    assert result["service"] == "aws_s3"
    assert result["params"] == {}
    # Test case (Pos): Match aws_s3 pattern with bucket name
    result2 = parse_storage_host("mybucket.s3.amazonaws.com")
    assert result2["service"] == "aws_s3"
    assert result2["params"]["bucket"] == "mybucket"
    # Test case (Pos): Match wasabi pattern
    result3 = parse_storage_host("s3.wasabisys.com")
    assert result3["service"] == "wasabi"
    assert result3["params"] == {}
    # Test case (Pos): Match wasabi pattern with region
    result4 = parse_storage_host("s3.us-west-1.wasabisys.com")
    assert result4["service"] == "wasabi"
    assert result4["params"]["region"] == "us-west-1"


# def parse_storage_host(host):
# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_utils.py::test_parse_storage_host_no_match -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_parse_storage_host_no_match(app):
    # Test case (Pos): No match any pattern
    patterns = {
        "aws_s3": [r"^s3\.amazonaws\.com$"],
    }
    mock_config = {"FILES_REST_STORAGE_SERVICE_PATTERN": patterns}
    app.config.update(mock_config)
    result = parse_storage_host("unknown.host.com")
    assert result["service"] is None
    assert result["params"] == {}


# def parse_storage_host(host):
# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_utils.py::test_parse_storage_host_empty_patterns -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_parse_storage_host_empty_patterns(app):
    # Test case (Pos): Empty patterns
    mock_config = {"FILES_REST_STORAGE_SERVICE_PATTERN": {}}
    app.config.update(mock_config)
    result = parse_storage_host("s3.amazonaws.com")
    assert result["service"] is None
    assert result["params"] == {}
