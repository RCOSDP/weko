# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from unittest.mock import patch
from marshmallow import ValidationError

from weko_notifications.notifications import ActivityType
from weko_notifications.schema import ActorResource, InboxResource, UrlObject, DocumentObject, ContextObject, NotificationSchema, validate_string_or_list, validate_activity_type

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace


# def validate_string_or_list(value):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_validate_string_or_list -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_validate_string_or_list():
    assert validate_string_or_list("string") is None
    assert validate_string_or_list(["string1", "string2"]) is None
    with pytest.raises(ValidationError):
        validate_string_or_list(123)
    with pytest.raises(ValidationError):
        validate_string_or_list([123, "string2"])

# def validate_activity_type(value):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_validate_activity_type -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_validate_activity_type():
    assert validate_activity_type(ActivityType.ANNOUNCE.value) is None
    with pytest.raises(ValidationError):
        validate_activity_type("invalid")
    with pytest.raises(ValidationError):
        validate_activity_type(["invalid", "invalid"])

# class ActorResource(Schema):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_actor_resource_validation -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_actor_resource_validation():
    valid_data = {"id": "123", "type": "Person", "name": "John Doe"}
    invalid_data = {"id": "123", "type": 123, "name": 456}

    schema = ActorResource()

    # Valid data should pass
    result = schema.load(valid_data).data
    assert result == valid_data

    # Invalid data should raise ValidationError
    with pytest.raises(ValidationError) as ex:
        schema.load(invalid_data).data
    assert "type" in ex.value.messages
    assert "name" in ex.value.messages

# class InboxResource(Schema):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_inbox_resource_validation -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_inbox_resource_validation():
    valid_data = {"id": "123", "inbox": "inbox_url", "type": "Service"}
    invalid_data = {"id": "123", "inbox": "inbox_url", "type": 123}

    schema = InboxResource()

    # Valid data should pass
    result = schema.load(valid_data).data
    assert result == valid_data

    # Invalid data should raise ValidationError
    with pytest.raises(ValidationError) as ex:
        schema.load(invalid_data).data
    assert "type" in ex.value.messages

# class UrlObject(Schema):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_url_object_validation -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_url_object_validation():
    valid_data = {"id": "123", "mediaType": "application/json", "type": "URL"}
    invalid_data = {"id": "123", "mediaType": "application/json", "type": 123}

    schema = UrlObject()

    # Valid data should pass
    result = schema.load(valid_data).data
    assert result == valid_data

    # Invalid data should raise ValidationError
    with pytest.raises(ValidationError) as ex:
        schema.load(invalid_data).data
    assert "type" in ex.value.messages

# class DocumentObject(Schema):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_document_object_validation -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_document_object_validation():
    valid_data = {"id": "123", "object": "doc", "type": "Document", "ietf:cite-as": "cite-as", "url": {"id": "456", "mediaType": "application/pdf", "type": "URL"}}
    invalid_data = {"id": "123", "object": "doc", "type": 123, "ietf:cite-as": "cite-as", "url": {"id": "456", "mediaType": "application/pdf", "type": 123}}

    schema = DocumentObject()

    # Valid data should pass
    result = schema.load(valid_data).data
    assert result == valid_data

    # Invalid data should raise ValidationError
    with pytest.raises(ValidationError) as ex:
        schema.load(invalid_data).data
    assert "type" in ex.value.messages
    assert "url" in ex.value.messages

# class ContextObject(Schema):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_context_object_validation -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_context_object_validation():
    valid_data = {"id": "123", "ietf:cite-as": "cite-as", "type": "Context"}
    invalid_data = {"id": "123", "ietf:cite-as": "cite-as", "type": 123}

    schema = ContextObject()

    # Valid data should pass
    result = schema.load(valid_data).data
    assert result == valid_data

    # Invalid data should raise ValidationError
    with pytest.raises(ValidationError) as ex:
        schema.load(invalid_data).data
    assert "type" in ex.value.messages

# class NotificationSchema(Schema):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_schema.py::test_notification_schema_validation -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
def test_notification_schema_validation(json_notifications):
    valid_data = json_notifications["after_approval"]
    valid_data2 = {
        "id": "urn:uuid:ab65a169-5b3b-474f-b0cf-db77e145e952",
        "updated": "2025-01-23T04:57:18Z",
        "@context": ["https://www.w3.org/ns/activitystreams", "https://purl.org/coar/notify"],
        "type": ["Announce", "coar-notify:EndorsementAction"],
        "origin": {"id": "123", "inbox": "inbox_url", "type": "Inbox"},
        "target": {"id": "456", "inbox": "inbox_url", "type": "Inbox"},
        "object": {"id": "789", "object": "doc", "type": "Document", "ietf:cite-as": "cite-as", "url": {"id": "101", "mediaType": "application/pdf", "type": "URL"}},
        "actor": {"id": "111", "type": "Person", "name": "John Doe"},
        "context": {"id": "112", "ietf:cite-as": "cite-as", "type": "Context"},
        "inReplyTo": "reply_to"
    }
    invalid_data = {
        "id": "123",
        "updated": "2025-01-01 00:00:00",
        "@context": ["https://www.w3.org/ns/activitystreams", "https://purl.org/coar/notify"],
        "type": 123,
        "origin": {"id": "123", "inbox": "inbox_url", "type": "Inbox"},
        "target": {"id": "456", "inbox": "inbox_url", "type": "Inbox"},
        "object": {"id": "789", "object": "doc", "type": "Document", "ietf:cite-as": "cite-as", "url": {"id": "101", "mediaType": "application/pdf", "type": "URL"}},
        "actor": {"id": "111", "type": "Person", "name": "John Doe"},
        "context": {"id": "112", "ietf:cite-as": "cite-as", "type": "Context"},
        "inReplyTo": "reply_to"
    }

    schema = NotificationSchema()
    # Valid data should pass
    result = schema.load(valid_data).data
    assert result["id"] is not None
    assert result["id"].startswith("urn:uuid:")
    assert result["updated"] is not None
    assert result["@context"] == valid_data["@context"]
    assert result["type"] == valid_data["type"]
    assert result["origin"] == valid_data["origin"]
    assert result["target"] == valid_data["target"]
    assert result["object"] == valid_data["object"]
    assert result["actor"] == valid_data["actor"]
    assert result["context"] == valid_data["context"]
    assert result["inReplyTo"] == valid_data["inReplyTo"]

    # Valid data should pass
    result = schema.load(valid_data2).data
    assert result["id"] == valid_data2["id"]
    assert result["updated"] == valid_data2["updated"]

    # Invalid data should raise ValidationError
    with pytest.raises(ValidationError) as ex:
        schema.load(invalid_data).data
    assert "id" in ex.value.messages
    assert "updated" in ex.value.messages
    assert "type" in ex.value.messages
