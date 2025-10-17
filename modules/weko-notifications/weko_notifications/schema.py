# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

import uuid
from datetime import datetime
from marshmallow import Schema, fields, ValidationError

from .utils import rfc3339


def validate_string_or_list(value):
    """
    Validate that the value is a string or a list of strings.

    Args:
        value: Value to validate.
    Raises:
        ValidationError:
            If the value is not a string or a list of strings.
    """
    if isinstance(value, str):
        return
    elif isinstance(value, list):
        if not all(isinstance(x, str) for x in value):
            raise ValidationError("List elements must be strings.")
        return
    raise ValidationError("Must be a string or list of strings.")


def validate_activity_type(value):
    """
    Validate that the value is a valid activity type.

    Args:
        value: Value to validate.
    Raises:
        ValidationError:
            If the value is not a valid activity type.
    """
    from .notifications import ActivityType
    if (
        value not in (activity.value for activity in ActivityType)
        and value not in (activity.deletion_value for activity in ActivityType)
    ):
        raise ValidationError("Invalid activity type.")
    return


def validate_urn_uuid(value):
    """
    Validate that the value is a URN UUID.

    Args:
        value: Value to validate.
    Raises:
        ValidationError:
            If the value is not a URN UUID.
    """
    if not value.startswith("urn:uuid:"):
        raise ValidationError("Must be a URN UUID.")
    try :
        uuid.UUID(value)
    except ValueError as ex:
        raise ValidationError("Invalid URN UUID format.") from ex


def validate_rfc3339(value):
    """
    Validate that the value is a RFC3339 format.

    Args:
        value: Value to validate.
    Raises:
        ValidationError:
            If the value is not a RFC3339 format.
    """
    try:
        value = value.replace("Z", "+00:00")
        if len(value) > 6 and value[-3] == ':':
            value = value[:-3] + value[-2:]
        datetime.strptime(value, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError:
        raise ValidationError("Invalid RFC3339 format")


class ActorResource(Schema):
    id = fields.String(required=True)
    type = fields.Field(required=True, validate=validate_string_or_list)
    name = fields.Field(required=True, validate=validate_string_or_list)


    class Meta:
        strict = True


class InboxResource(Schema):
    id = fields.String(required=True)
    inbox = fields.String(required=True)
    type = fields.Field(required=True, validate=validate_string_or_list)

    class Meta:
        strict = True


class UrlObject(Schema):
    id = fields.String(required=True)
    media_type = fields.String(
        all_none=True, attribute="mediaType", load_from="mediaType"
    )
    type = fields.Field(allow_none=True, validate=validate_string_or_list)

    class Meta:
        strict = True


class DocumentObject(Schema):
    id = fields.String(required=True)
    object = fields.String(allow_none=True)
    type = fields.Field(allow_none=True, validate=validate_string_or_list)
    ietf_cite_as = fields.String(
        allow_none=True, attribute="ietf:cite-as", load_from="ietf:cite-as"
    )
    url = fields.Nested(UrlObject, allow_none=True)
    name = fields.String(allow_none=True)

    class Meta:
        strict = True


class ContextObject(Schema):
    id = fields.String(required=True)
    ietf_cite_as = fields.String(
        allow_none=True, attribute="ietf:cite-as", load_from="ietf:cite-as"
    )
    type = fields.Field(allow_none=True, validate=validate_string_or_list)

    class Meta:
        strict = True


class NotificationSchema(Schema):
    """Notification schema."""
    id = fields.String(
        required=True, validate=validate_urn_uuid,
        missing=lambda: f"urn:uuid:{uuid.uuid4()}")
    """URN:UUID of the notification."""
    updated = fields.String(
        required=True, validate=validate_rfc3339 , missing=rfc3339
    )
    """Timestamp of the notification(RFC3339)."""
    at_context = fields.List(
        fields.String(),
        required=True, attribute="@context", load_from="@context"
    )
    """Context of the notification. alias of '@context'."""

    activity_type = fields.Field(
        required=True, validate=validate_activity_type,
        attribute="type", load_from="type"
    )
    """Type of the notification."""
    origin = fields.Nested(InboxResource, required=True)
    """Origin entity of the notification."""
    target = fields.Nested(InboxResource, required=True)
    """Target entity of the notification."""
    object = fields.Nested(DocumentObject, required=True)
    """Object entity of the notification."""
    actor = fields.Nested(ActorResource, allow_none=True)
    """Actor entity of the notification."""
    context = fields.Nested(ContextObject, allow_none=True)
    """Context entity of the notification."""

    in_reply_to = fields.String(
        allow_none=True, attribute="inReplyTo", load_from="inReplyTo"
    )
    """In reply to the notification. alias of 'inReplyTo'."""

    class Meta:
        strict = True
