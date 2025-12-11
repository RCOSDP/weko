# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Files download/upload REST API similar to S3 for Invenio."""

import botocore.client
from invenio_files_rest.utils import create_boto3_s3_client

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
