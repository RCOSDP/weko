# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utilities for validation of user profiles and preferences."""

from .dicts import UserPreferenceDict, UserProfileDict, ValidatedDict
from .schemas import UserPreferencesSchema, UserProfileSchema

__all__ = (
    "UserPreferenceDict",
    "UserPreferencesSchema",
    "UserProfileDict",
    "UserProfileSchema",
    "ValidatedDict",
)
