# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test invenio-accounts schemas."""

import pytest
from marshmallow import ValidationError

from invenio_accounts.profiles.schemas import (
    validate_locale,
    validate_timezone,
    validate_visibility,
)


def test_validate_visibility():
    """Test validate_visibility."""
    validate_visibility("public")
    validate_visibility("restricted")
    with pytest.raises(ValidationError):
        validate_visibility("invalid")


def test_validate_locale(app):
    """Test validate_locale."""
    with app.app_context():
        validate_locale("en")
        with pytest.raises(ValidationError):
            validate_locale("invalid")


def test_validate_timezone(app):
    """Test validate_timezone."""
    with app.app_context():
        validate_timezone("Europe/Zurich")
        validate_timezone("Europe/Vienna")
        validate_timezone("Europe/London")
        with pytest.raises(ValidationError):
            validate_timezone("invalid")
