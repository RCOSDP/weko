# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""


from flask import request, flash
from flask_babelex import lazy_gettext as _
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField

from .models import NotificationsUserSettings


def handle_notifications_form(form):
    """Handle notifications form.

    Validate and Flash messages.

    Args:
        form (flask_wtf.FlaskForm): The notifications form.
    """
    if not isinstance(form, NotificationsForm):
        raise TypeError(
            "form must be an instance of NotificationsForm, "
            "not {}".format(type(form))
        )
    form.process(formdata=request.form)

    if form.validate_on_submit():
        if form.subscribe_email.data and current_user.confirmed_at is None:
            form.subscribe_email.errors.append(
                _("Email notifications require a confirmed email address.")
            )
            form.subscribe_email.data = False
            return
        if form.subscribe_webpush.data and not form.webpush_endpoint.data:
            form.subscribe_webpush.errors.append(
                _("Failed to get subscription information. Please try again.")
            )
            form.subscribe_webpush.data = False
            return
        NotificationsUserSettings.create_or_update(
            user_id=current_user.id,
            subscribe_email=form.subscribe_email.data
        )
        flash(_("Notifications settings updated."), category="success")
    else:
        flash(
            _("Failed to update your notifications settings."),
            category="error"
        )


class NotificationsForm(FlaskForm):
    """Form for notifications settings."""

    subscribe_webpush = BooleanField(
        # NOTE: Form field label
        _("Web push"),
        # NOTE: Form field help text
        description=_("Receive notifications via web push.")
    )
    """Web push notification subscription status."""
    webpush_endpoint = HiddenField(
        _("Web push endpoint"),
    )
    webpush_expiration_time = HiddenField(
        _("Web push expiration time"),
    )
    webpush_p256dh = HiddenField(
        _("Web push p256dh"),
    )
    webpush_auth = HiddenField(
        _("Web push auth"),
    )
    subscribe_email = BooleanField(
        _("Email"),
        description=_("Receive notifications via email.")
    )
