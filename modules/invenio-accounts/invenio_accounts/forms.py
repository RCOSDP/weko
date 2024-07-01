# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Additional non-userprofile fields used during registration.

Currently supported: recaptcha
"""
from flask import request
from flask_security.forms import NextFormMixin
from flask_wtf import FlaskForm, Recaptcha, RecaptchaField
from invenio_db import db
from invenio_i18n import gettext as _
from wtforms import FormField, HiddenField

from .proxies import current_datastore
from .utils import validate_domain


class RegistrationFormRecaptcha(FlaskForm):
    """Form for editing user profile."""

    recaptcha = RecaptchaField(
        validators=[Recaptcha(message=_("Please complete the reCAPTCHA."))]
    )


class RevokeForm(FlaskForm):
    """Form for revoking a session."""

    sid_s = HiddenField()


def confirm_register_form_factory(Form, app):
    """Return confirmation for extended registration form."""

    class ConfirmRegisterForm(Form, NextFormMixin):
        def __init__(self, *args, **kwargs):
            """Adds next parameter from URL."""
            super(ConfirmRegisterForm, self).__init__(*args, **kwargs)
            if not self.next.data:
                self.next.data = request.args.get("next", "")

        def validate(self, extra_validators=None):
            """Validate domain on email list."""
            if not super().validate(extra_validators=extra_validators):
                return False

            if not validate_domain(self.email.data):
                self.email.errors.append(_("The email domain is blocked."))
                return False
            return True

    if app.config.get("RECAPTCHA_PUBLIC_KEY") and app.config.get(
        "RECAPTCHA_PRIVATE_KEY"
    ):

        class ConfirmRegisterWithCaptchaForm(ConfirmRegisterForm):
            recaptcha = FormField(RegistrationFormRecaptcha, separator=".")

        return ConfirmRegisterWithCaptchaForm

    return ConfirmRegisterForm


def register_form_factory(Form, app):
    """Return extended registration form."""
    if app.config.get("RECAPTCHA_PUBLIC_KEY") and app.config.get(
        "RECAPTCHA_PRIVATE_KEY"
    ):

        class RegisterForm(Form):
            recaptcha = FormField(RegistrationFormRecaptcha, separator=".")

        return RegisterForm

    return Form


def login_form_factory(Form, app):
    """Return extended login form."""

    class LoginForm(Form):
        pass

    return LoginForm


def send_confirmation_form_factory(Form, app):
    """Return extended login form."""

    class SendConfirmationEmailView(Form):
        """Form which sends confirmation instructions.

        If user not in the system, do not raise but ignore.
        The overriden behaviour exists because the endpoint is public and users can
        take an insight on which emails exist in the system otherwise.
        """

        def validate(self, extra_validators=None):
            with db.session.no_autoflush:
                self.user = current_datastore.get_user(self.data["email"])
            # Form is valid if user exists and they are not yet confirmed
            if self.user is not None and self.user.confirmed_at is None:
                return True
            return False

    return SendConfirmationEmailView
