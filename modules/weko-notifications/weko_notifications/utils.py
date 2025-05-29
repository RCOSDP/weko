# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

import os
import re
import json
import traceback
from marshmallow import ValidationError
import pytz
from datetime import datetime

from flask import current_app, request
from requests import HTTPError

from weko_user_profiles.config import USERPROFILES_TIMEZONE_LIST
from weko_user_profiles.models import UserProfile

from .client import NotificationClient

def inbox_url(endpoint=None, _external=False):
    """Return the inbox URL.

    Args:
        endpoint (str | None): The endpoint to append to the URL.
        _external (bool): Whether to return the URL with the full domain.

    Returns:
        str: The inbox URL.
    """
    url = (
        current_app.config["THEME_SITEURL"]
        if _external
        else current_app.config["WEKO_NOTIFICATIONS_INBOX_ADDRESS"]
    )
    if endpoint is not None:
        url += endpoint
    else:
        url += current_app.config["WEKO_NOTIFICATIONS_INBOX_ENDPOINT"]

    return str(url)


def rfc3339(timezone=None):
    """Return the current time in RFC3339 format.

    Args:
        timezone (str | None):
            The timezone to use. Defaults to "Asia/Tokyo".

    Returns:
        str: The current time in RFC3339 format.
    """
    tz = pytz.timezone(timezone or "Asia/Tokyo")
    return datetime.now(tz).isoformat(timespec="seconds").replace("+00:00", "Z")


def create_subscription(user_id, endpoint, expiration_time, p256dh, auth):
    """Create a subscription.

    Args:
        user_id (int): The user ID.
        endpoint (str): The subscription endpoint.
        expiration_time (str): The expiration
        p256dh (str): The P-256 Diffie-Hellman public key.
        auth (str): The authentication secret.

    Returns:
        dict: The subscription.
    """
    root_url = request.host_url

    subscription = {
        "target": f"{root_url}user/{user_id}",
        "endpoint": endpoint,
        "expirationTime": expiration_time,
        "keys": {
            "p256dh": p256dh,
            "auth": auth
        }
    }

    return subscription


def create_userprofile(userprofile):
    """Create a user profile.

    Args:
        userprofile (UserProfile): The user profile.

    Returns:
        dict: The user profile.
    """
    root_url = request.host_url

    posix_tz = userprofile.timezone
    iana_tz = "GMT+9:00"
    for posix, iana in USERPROFILES_TIMEZONE_LIST:
        if posix == posix_tz:
            pattern = r"\((GMT.*?)\)"
            iana_tz = re.search(pattern, str(iana)).group(1)

    userprofile = {
        "uri": f"{root_url}user/{userprofile.user_id}",
        "displayname": userprofile._displayname,
        "language": userprofile.language,
        "timezone": iana_tz,
    }

    return userprofile


def get_push_template():
    """Get the push template.

    Returns:
        dict: The push template.
    """
    template_path = current_app.config["WEKO_NOTIFICATIONS_PUSH_TEMPLATE_PATH"]
    if (
        not template_path
        or not os.path.isfile(template_path)
    ):
        current_app.logger.error(
            "Push template path is not set or file does not exist: {}"
            .format(template_path)
        )
        return None

    with open(template_path, "r", encoding="utf-8") as template_file:
        template = json.load(template_file)

    if not isinstance(template, dict):
        current_app.logger.error(
            "Push template is not a valid JSON object: {}".format(template_path)
        )
        return None

    templates = [
        {
            "name": value.get("name"),
            "description": value.get("description"),
            "type": value.get("type"),
            "language": lang,
            "title": tpl.get("title"),
            "body": tpl.get("body"),
        }
        for _, value in template.items()
        for lang, tpl in value.get("templates", {}).items()
    ]
    return templates


def _get_params_for_registrant(target_id, actor_id, shared_id):
    """Get parameters for registrant.

    Args:
        target_id (int): The target ID.
        actor_id (int): The actor ID.
        shared_id (int): The shared ID.

    Returns:
        tuple(set, str):
            - str: Set of target IDs.
            - str: The actor's name.
    """
    set_target_id = {target_id}
    is_shared = shared_id != -1
    if is_shared:
        set_target_id.add(shared_id)
    set_target_id.discard(actor_id)

    actor_profile = UserProfile.get_by_userid(actor_id)
    actor_name = actor_profile.username if actor_profile else None

    return set_target_id, actor_name

def notify_item_imported(
    target_id, recid, actor_id, object_name=None, shared_id=-1
):
    """Notify item imported.

    Args:
        target_id (int): The target ID.
        recid (str): The record ID.
        actor_id (int): The actor ID.
        shared_id (str): The shared ID.

    Returns:
        dict: The notification.
    """
    set_target_id, actor_name = _get_params_for_registrant(
        target_id, actor_id, shared_id
    )

    from .notifications import Notification
    for target_id in set_target_id:
        try:
            Notification.create_item_registered(
                target_id, recid, actor_id,
                actor_name=actor_name, object_name=object_name,
            ).send(NotificationClient(inbox_url()))
        except (ValidationError, HTTPError) as ex:
            current_app.logger.error(
                "Failed to send notification for item import."
            )
            traceback.print_exc()
            return
        except Exception as ex:
            current_app.logger.error(
                "Unexpected error occurred while sending notification for item import."
            )
            traceback.print_exc()
            return
    current_app.logger.info(
        "{num} notification(s) sent for item import."
        .format(num=len(set_target_id))
    )


def notify_item_deleted(
    target_id, recid, actor_id, object_name=None, shared_id=-1
):
    """Notify item deleted.

    Args:
        target_id (int): The target ID.
        recid (str): The record ID.
        actor_id (int): The actor ID.
        shared_id (str): The shared ID.

    Returns:
        dict: The notification.
    """
    set_target_id, actor_name = _get_params_for_registrant(
        target_id, actor_id, shared_id
    )

    from .notifications import Notification
    for target_id in set_target_id:
        try:
            Notification.create_item_deleted(
                target_id, recid, actor_id,
                actor_name=actor_name, object_name=object_name
            ).send(NotificationClient(inbox_url()))
        except (ValidationError, HTTPError) as ex:
            current_app.logger.error(
                "Failed to send notification for item delete."
            )
            traceback.print_exc()
            return
        except Exception as ex:
            current_app.logger.error(
                "Unexpected error occurred while sending notification for item delete."
            )
            traceback.print_exc()
            return
    current_app.logger.info(
        "{num} notification(s) sent for item delete."
        .format(num=len(set_target_id))
    )
