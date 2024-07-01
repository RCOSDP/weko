# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Schemas for user profiles and preferences."""

import pytz
from flask import current_app
from invenio_i18n import lazy_gettext as _
from marshmallow import Schema, ValidationError, fields


def validate_visibility(value):
    """Check if the value is a valid visibility setting."""
    if value not in ["public", "restricted"]:
        raise ValidationError(
            message=str(_("Value must be either 'public' or 'restricted'."))
        )


def validate_locale(value):
    """Check if the value is a valid locale."""
    locales = current_app.extensions["invenio-i18n"].get_locales()
    locales = [locale.language for locale in locales]

    if value not in locales:
        raise ValidationError(message=str(_("Value must be a valid locale.")))
    current_app.config["BABEL_DEFAULT_LOCALE"] = value


def validate_timezone(value):
    """Check if the value is a valid timezone."""
    if value not in pytz.all_timezones:
        raise ValidationError(message=str(_("Value must be a valid timezone.")))
    current_app.config["BABEL_DEFAULT_TIMEZONE"] = value


class UserProfileSchema(Schema):
    """The default user profile schema."""

    full_name = fields.String()
    affiliations = fields.String()


class UserPreferencesSchema(Schema):
    """The default schema for user preferences."""

    visibility = fields.String(validate=validate_visibility)
    email_visibility = fields.String(validate=validate_visibility)
    locale = fields.String(validate=validate_locale)
    timezone = fields.String(validate=validate_timezone)
