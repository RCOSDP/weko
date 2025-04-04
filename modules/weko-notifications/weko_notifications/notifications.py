# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

from enum import Enum

from flask import url_for

from .config import COAR_NOTIFY_CONTEXT
from .utils import inbox_url


class ActivityType(Enum):
    ACCEPT_REVIEW = ["Accept", "coar-notify:ReviewAction"]

    ACKNOWLEDGE_AND_REJECT = ["Reject"]
    ACKNOWLEDGE_AND_TENTATIVE_ACCEPT = ["TentativeAccept"]
    ACKNOWLEDGE_AND_TENTATIVE_REJECT = ["TentativeReject"]

    ANNOUNCE = ["Announce"]
    ANNOUNCE_ENDORSE = ["Announce", "coar-notify:EndorsementAction"]
    ANNOUNCE_INGEST = ["Announce", "coar-notify:IngestAction"]
    ANNOUNCE_RELATIONSHIP = ["Announce", "coar-notify:RelationshipAction"]
    ANNOUNCE_REVIEW = ["Announce", "coar-notify:ReviewAction"]

    OFFER_ENDORSE = ["Offer", "coar-notify:EndorsementAction"]
    OFFER_INGEST = ["Offer", "coar-notify:IngestAction"]
    OFFER_REVIEW = ["Offer", "coar-notify:ReviewAction"]

    UNDO = ["Undo"]


class Notification(object):
    """Notification class."""
    def __init__(self):
        """Initialize notification."""
        self.activity_type = None
        """ActivityType | str: Activity type."""

        self.origin = {}
        """dict: Origin entity."""
        self.target = {}
        """dict: Target entity."""
        self.object = {}
        """dict: Object entity."""

        self.actor = {}
        """dict: Actor entity."""
        self.context = {}
        """dict: Context entity."""

        self.in_reply_to = None
        """str: inReplyTo. alias of 'inReplyTo'."""

        self.payload = {}
        """dict: Notification payload validated by `NotificationSchema`."""

        self._is_validated = False

    def __str__(self):
        """Return notification body."""
        return str(self.current_body)

    def __eq__(self, other):
        """Return True if the value is equal to the current id."""
        return self.id == other.id

    @property
    def id(self):
        """str: Notification ID."""
        return self.payload["id"] if "id" in self.payload else None

    @property
    def updated(self):
        """str: Updated timestamp. """
        return self.payload["updated"] if "updated" in self.payload else None

    @property
    def current_body(self):
        """dict: Notification body. """
        _body = {}
        _body.update({"id": self.id}) if self.id else None
        _body.update({"updated": self.updated}) if self.updated else None
        _body.update({"@context": COAR_NOTIFY_CONTEXT})
        _body.update({
            "type": self.activity_type.value
                if isinstance(self.activity_type, ActivityType)
                else self.activity_type
        })
        _body.update({"origin": self.origin})
        _body.update({"target": self.target})
        _body.update({"object": self.object})
        _body.update({"actor": self.actor}) if self.actor else None
        _body.update({"context": self.context}) if self.context else None
        _body.update(
            {"inReplyTo": self.in_reply_to}
        ) if self.in_reply_to else None

        return _body

    def create(self):
        """Create notification.

        Create and validate notification payload.

        Returns:
            Notification: Notification instance with payload.
        """
        from .schema import NotificationSchema
        self.payload = NotificationSchema().load(self.current_body).data
        self.activity_type = self.payload.get("type")
        self.origin = self.payload.get("origin")
        self.target = self.payload.get("target")
        self.object = self.payload.get("object")
        self.actor = self.payload.get("actor", {})
        self.context = self.payload.get("context", {})
        self.in_reply_to = self.payload.get("inReplyTo")
        self._is_validated = True
        return self

    @classmethod
    def load(cls, payload):
        """Load notification.

        Load and validate notification payload.

        Args:
            payload (dict): Notification payload.
        Returns:
            Notification: Notification instance with payload.
        """
        obj = cls()
        from .schema import NotificationSchema
        obj.payload = NotificationSchema().load(payload).data
        obj._is_validated = True
        return obj

    def validate(self):
        """Validate notification payload.

        Returns:
            Notification: Notification instance with payload.
        """
        from .schema import NotificationSchema
        self.payload = NotificationSchema().load(self.current_body).data

    def set_type(self, activity_type):
        """Set activity type.

        Args:
            activity_type (ActivityType):
                One of the Activity Stream 2.0 Activity Types
        Returns:
            Notification: Notification instance
        """
        self.activity_type = activity_type
        self._is_validated = False
        return self

    def set_origin(self, id, inbox, entity_type):
        """Set origin entity.

        Args:
            id (str):
                ID of the origin entity. This should be the URI of the origin.
            inbox (str):
                Inbox URL of the origin entity.
            entity_type (list[str] | str):
                Type of the origin entity.
        Returns:
            Notification: Notification instance
        """
        self.origin = {"id": id, "inbox": inbox, "type": entity_type}
        self._is_validated = False
        return self


    def set_target(self, id, inbox, entity_type):
        """Set target entity.

        Args:
            id (str):
                ID of the target entity. This should be the URI of the target.
            inbox (str):
                Inbox URL of the target entity.
            entity_type (list[str] | str):
                Type of the target entity.
        Returns:
            Notification: Notification instance
        """
        self.target = {"id": id, "inbox": inbox, "type": entity_type}
        self._is_validated = False
        return self

    def set_object(
            self, id, object=None,
            object_type=None, ietf_cite_as=None, url=None, name=None
    ):
        """Set object entity.

        Args:
            id (str):
                ID of the object entity. This should be the URI of the object.
            object (str | None):
                Object of the object entity.
            object_type (list[str] | str):
                Type of the object entity.
            ietf_cite_as (str | None):
                IETF Cite As of the object entity.
            url (dict | None):
                URL of the object entity.
            name (str | None):
                Name of the object entity.
        Returns:
            Notification: Notification instance
        """
        self.object["id"] = id
        self.object["object"] = object if object else None
        self.object["type"] = object_type if object_type else None
        self.object["ietf:cite-as"] = ietf_cite_as if ietf_cite_as else None
        self.object["url"] = url if url else None
        self.object["name"] = name if name else None
        self._is_validated = False
        return self

    def set_actor(self, id, entity_type, name):
        """Set actor entity.

        Args:
            id (str):
                ID of the actor entity. This should be the URI of the actor.
            entity_type (list[str] | str):
                Type of the actor entity.
            name (str):
                Name of the actor entity.
        Returns:
            Notification: Notification instance
        """
        self.actor = {"id": id, "type": entity_type, "name": name}
        self._is_validated = False
        return self

    def set_context(self, id, ietf_cite_as=None, entity_type=None):
        """Set context entity.

        Args:
            id (str):
                ID of the context entity. This should be the URI of the context.
            ietf_cite_as (str | None):
                IETF Cite As of the context entity. alias of 'ietf:cite-as'.
            entity_type (list[str] | str):
                Type of the context entity.
        Returns:
            Notification: Notification instance
        """
        self.context["id"] = id
        self.context["ietf:cite-as"] = ietf_cite_as if ietf_cite_as else None
        self.context["type"] = entity_type if entity_type else None
        self._is_validated = False
        return self

    def send(self, client):
        """Send notification.

        Args:
            client (NotificationClient): Notification client.
        Returns:
            str: Notification ID sent.
        """
        return client.send(self)


    @classmethod
    def create_item_registared(
            cls, target_id, object_id, actor_id, **kwargs
        ):
        """Create item registared notification.

        Create a notification of type Announce,coar-notify::IngestAction
        for the item had registered.

        Args:
            target_id (int): ID of the target user.
            object_id (int): ID of the object item.
            actor_id (int): ID of the actor user.
            kwargs (dict):
                object_name (str): Name of the object item. <br>
                ietf_cite_as (str): IETF Cite As of the object item. <br>
                actor_name (str): Name of the actor user.

        Returns:
            Notification: Notification instance
        """
        site_index_url = url_for('weko_theme.index', _external=True)
        item_url = url_for(
            "invenio_records_ui.recid", pid_value=object_id, _external=True
        )
        obj = cls()
        obj.set_type(ActivityType.ANNOUNCE_INGEST)
        obj.set_origin(
            id=site_index_url,
            inbox=inbox_url(_external=True),
            entity_type="Service"
        )
        obj.set_target(
            id=f"{site_index_url}user/{target_id}",
            inbox=inbox_url(_external=True),
            entity_type="Person"
        )
        obj.set_object(
            id=item_url,
            ietf_cite_as=kwargs.get("ietf_cite_as"),
            object_type=["Page", "sorg:WebPage"],
            name=kwargs.get("object_name")
        )
        obj.set_actor(
            id=f"{site_index_url}user/{actor_id}",
            entity_type="Person",
            name=kwargs.get("actor_name") or "Unknown"
        )
        return obj.create()

    @classmethod
    def create_request_approval(
            cls, target_id, object_id, actor_id, context_id, **kwargs
        ):
        """Create offer notification.

        Create a notification of type Offer,coar-notify::EndorsementAction to
        request approval for the item registration.

        Args:
            target_id (int): ID of the target user.
            object_id (int): ID of the object item.
            actor_id (int): ID of the actor user.
            context_id (int): ID of the context page.
            kwargs (dict):
                object_name (str): Name of the object item. <br>
                actor_name (str): Name of the actor user.

        Returns:
            Notification: Notification instance
        """
        site_index_url = url_for('weko_theme.index', _external=True)
        item_url = url_for(
            "invenio_records_ui.recid", pid_value=object_id, _external=True
        )
        activity_url = url_for(
            "weko_workflow.display_activity", activity_id=context_id,
            _external=True
        )

        obj = cls()
        obj.set_type(ActivityType.OFFER_ENDORSE)
        obj.set_origin(
            id=site_index_url,
            inbox=inbox_url(_external=True),
            entity_type="Service"
        )
        obj.set_target(
            id=f"{site_index_url}user/{target_id}",
            inbox=inbox_url(_external=True),
            entity_type="Person"
        )
        obj.set_object(
            id=item_url,
            object_type=["Page", "sorg:WebPage"],
            name=kwargs.get("object_name")
        )
        obj.set_actor(
            id=f"{site_index_url}user/{actor_id}",
            entity_type="Person",
            name=kwargs.get("actor_name") or "Unknown"
        )
        obj.set_context(
            id=activity_url,
            entity_type=["Page", "sorg:WebPage"]
        )
        return obj.create()

    @classmethod
    def create_item_approved(
            cls, target_id, object_id, actor_id, context_id, **kwargs
        ):
        """Create item approved notification.

        Create a notification of type Announce,coar-notify:EndorsementAction
        for the item had approved.

        Args:
            target_id (int): ID of the target user.
            object_id (int): ID of the object item.
            actor_id (int): ID of the actor user.
            context_id (int): ID of the context page.
            kwargs (dict):
                object_name (str): Name of the object item. <br>
                ietf_cite_as (str): IETF Cite As of the object item. <br>
                actor_name (str): Name of the actor user.

        Returns:
            Notification: Notification instance
        """
        site_index_url = url_for('weko_theme.index', _external=True)
        item_url = url_for(
            "invenio_records_ui.recid", pid_value=object_id, _external=True
        )
        activity_url = url_for(
            "weko_workflow.display_activity", activity_id=context_id,
            _external=True
        )
        obj = cls()
        obj.set_type(ActivityType.ANNOUNCE_ENDORSE)
        obj.set_origin(
            id=site_index_url,
            inbox=inbox_url(_external=True),
            entity_type="Service"
        )
        obj.set_target(
            id=f"{site_index_url}user/{target_id}",
            inbox=inbox_url(_external=True),
            entity_type="Person"
        )
        obj.set_object(
            id=item_url,
            ietf_cite_as=kwargs.get("ietf_cite_as"),
            object_type=["Page", "sorg:WebPage"],
            name=kwargs.get("object_name")
        )
        obj.set_actor(
            id=f"{site_index_url}user/{actor_id}",
            entity_type="Person",
            name=kwargs.get("actor_name") or "Unknown"
        )
        obj.set_context(
            id=activity_url,
            entity_type=["Page", "sorg:WebPage"]
        )
        return obj.create()

    @classmethod
    def create_item_rejected(
            cls, target_id, object_id, actor_id, context_id, **kwargs
        ):
        """Create item rejected notification.

        Create a notification of type Reject for the item had rejected.

        Args:
            target_id (int): ID of the target user.
            object_id (int): ID of the object item.
            actor_id (int): ID of the actor user.
            context_id (int): ID of the context page.
            kwargs (dict):
                object_name (str): Name of the object item. <br>
                ietf_cite_as (str): IETF Cite As of the object item. <br>
                actor_name (str): Name of the actor user.

        Returns:
            Notification: Notification instance
        """
        site_index_url = url_for('weko_theme.index', _external=True)
        item_url = url_for(
            "invenio_records_ui.recid", pid_value=object_id, _external=True
        )
        activity_url = url_for(
            "weko_workflow.display_activity", activity_id=context_id,
            _external=True
        )
        obj = cls()
        obj.set_type(ActivityType.ACKNOWLEDGE_AND_REJECT)
        obj.set_origin(
            id=site_index_url,
            inbox=inbox_url(_external=True),
            entity_type="Service"
        )
        obj.set_target(
            id=f"{site_index_url}user/{target_id}",
            inbox=inbox_url(_external=True),
            entity_type="Person"
        )
        obj.set_object(
            id=item_url,
            ietf_cite_as=kwargs.get("ietf_cite_as"),
            object_type=["Page", "sorg:WebPage"],
            name=kwargs.get("object_name")
        )
        obj.set_actor(
            id=f"{site_index_url}user/{actor_id}",
            entity_type="Person",
            name=kwargs.get("actor_name") or "Unknown"
        )
        obj.set_context(
            id=activity_url,
            entity_type=["Page", "sorg:WebPage"]
        )
        return obj.create()
