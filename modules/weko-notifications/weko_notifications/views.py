# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""


from __future__ import absolute_import, print_function

import traceback
import requests

from flask import (
    Blueprint, current_app, flash, jsonify, render_template, request
)
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_db import db

from weko_user_profiles.utils import current_userprofile

from .client import NotificationClient
from .forms import NotificationsForm, handle_notifications_form
from .models import NotificationsUserSettings
from .utils import (
    create_userprofile, inbox_url, create_subscription, get_push_template, user_uri
)

blueprint_ui = Blueprint(
    "weko_notifications_settings",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/account/settings/notifications/"
)
"""Blueprint for weko-notifications settings.

registered in .views module.

>>> from .views import blueprint_ui
>>> if app.config["WEKO_NOTIFICATIONS"]:
        app.register_blueprint(blueprint_ui)
"""

blueprint_api = Blueprint(
    "weko_notifications",
    __name__,
    template_folder="templates",
    static_folder="static"
)
"""Blueprint for weko-notifications API.
registered in .setup.py
"""


@blueprint_ui.before_app_first_request
def init_push_templates():
    """Initialize push template."""
    templates = get_push_template()
    if not templates:
        return

    for template in templates:
        try:
            requests.post(
                inbox_url(endpoint="/push-template"),
                json=template
            )
        except requests.RequestException as ex:
            traceback.print_exc()
            current_app.logger.error(
                f"Error updating push template. "
            )
            return
    current_app.logger.info("Push templates updated successfully.")


@blueprint_ui.route("/", methods=["GET", "POST"])
@login_required
@register_menu(
    blueprint_ui, "settings.notifications",
    _("%(icon)s Notifications", icon="<i class='fa fa-bell fa-fw'></i>"),
    order=3
)
@register_breadcrumb(
    blueprint_ui, "breadcrumbs.settings.notifications", _("Notifications")
)
def user_settings():
    """View for settings notifications."""
    notifications_form = notifications_form_factory()
    form_action = request.form.to_dict()

    if form_action:
        try:
            handle_notifications_form(notifications_form)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            traceback.print_exc()
            current_app.logger.error(
                f"Error updating notifications settings. user_id={current_user.id}"
            )
            flash(_("Failed to update push subscription."), category="error")

        else:
            endpoint = notifications_form.webpush_endpoint.data
            try:
                if endpoint == "":
                    current_app.logger.info(
                        "No push subscription for user %s.",
                        current_user.id
                    )
                    flash(
                        _("Failed to get subscription information. Please try again."),
                        category="error"
                    )
                elif notifications_form.subscribe_webpush.data:
                    subscripsion = create_subscription(
                        current_user.id,
                        notifications_form.webpush_endpoint.data,
                        notifications_form.webpush_expiration_time.data,
                        notifications_form.webpush_p256dh.data,
                        notifications_form.webpush_auth.data
                    )
                    userprofile = create_userprofile(current_userprofile)

                    current_app.logger.info(
                        "Updating push subscription for user %s: %s",
                        current_user.id,
                        endpoint[:24] + "..." + endpoint[-8:]
                    )
                    requests.post(inbox_url(endpoint="/subscribe"), json=subscripsion)
                    requests.post(inbox_url(endpoint="/userprofile"), json=userprofile)
                else:
                    current_app.logger.info(
                        "Unsubscribing push subscription for user %s: %s",
                        current_user.id,
                        endpoint[:24] + "..." + endpoint[-8:]
                    )
                    requests.post(
                        inbox_url(endpoint="/unsubscribe"), json={"endpoint": endpoint}
                    )
            except Exception as ex:
                traceback.print_exc()
                current_app.logger.error(
                    f"Error updating push subscription. user_id={current_user.id}"
                )
                flash(_("Failed to update push subscription."), category="error")

    return render_template(
        current_app.config["WEKO_NOTIFICATIONS_TEMPLATE"],
        notifications_form=notifications_form
    )

def notifications_form_factory():
    """Factory for notifications form.

    Returns:
        NotificationsForm: The notifications form.
    """
    user_settings = NotificationsUserSettings.get_by_user_id(current_user.id)
    if user_settings is None:
        user_settings = NotificationsUserSettings.create_or_update(
            user_id=current_user.id
        )

    form = NotificationsForm(
        subscribe_webpush=False,
        webpush_endpoint="",
        webpush_expiration_time="",
        webpush_p256dh="",
        webpush_auth="",
        subscribe_email=user_settings.subscribe_email,
        prefix="notifications"
    )
    return form



@blueprint_api.route("/notifications", methods=["GET"])
def notifications():
    """Retrieve notifications for the current user."""
    if not current_user.is_authenticated:
        return jsonify(
            code=401,
            message=_("Unauthorized access."),
        ), 401

    user_id = current_user.id
    client = NotificationClient(inbox_url())
    notifications = [
        notification.replace(inbox_url(), inbox_url(_external=True))
        for notification in
        client.notifications(target=user_uri(user_id, _external=True))
    ]

    return jsonify(
        code=200,
        message=_("Notifications retrieved successfully."),
        count=len(notifications),
        notifications=notifications
    )
