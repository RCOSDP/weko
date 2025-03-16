# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""


from __future__ import absolute_import, print_function
import traceback

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_db import db

from .forms import NotificationsForm, handle_notifications_form
from .models import NotificationsUserSettings


blueprint = Blueprint(
    "weko_notifications",
    __name__,
    template_folder="templates",
    static_folder="static"
)

blueprint_ui = Blueprint(
    "weko_notifications_settings",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/account/settings/notifications/"
)

@blueprint_ui.route("/", methods=["GET", "POST"])
@login_required
@register_menu(
    blueprint_ui, "settings.notifications",
    _("%(icon)s Notifications", icon="<i class='fa fa-bell fa-fw'></i>"),
    order=1
)
@register_breadcrumb(
    blueprint_ui, "breadcrumbs.settings.notifications", _("Notifications")
)
def notifications():
    """View for settings notifications."""
    notifications_form = notifications_form_factory()
    form = request.form.get("submit", None)

    current_app.logger.info(
        f"user_id={current_user.id} form={form}"
    )

    try:
        if form == "notifications":
            handle_notifications_form(notifications_form)
            db.session.commit()
    except Exception as ex:
        db.session.rollback()
        traceback.print_exc()
        current_app.logger.error(
            f"Error updating notifications settings. user_id={current_user.id}"
        )

    return render_template(
        current_app.config["WEKO_NOTIFICATIONS_TEMPLATE"],
        notifications_form=notifications_form
    )

def notifications_form_factory():
    """Factory for notifications form."""
    user_settings = NotificationsUserSettings.get_by_user_id(current_user.id)
    if user_settings is None:
        user_settings = NotificationsUserSettings.create_or_update(
            user_id=current_user.id
        )
    form = None
    if user_settings:
        form = NotificationsForm(
            subscribe_webpush=user_settings.subscribe_webpush,
            subscribe_email=user_settings.subscribe_email,
            prefix="notifications"
        )
    else:
        form = NotificationsForm(
            prefix="notifications"
        )
    return form
