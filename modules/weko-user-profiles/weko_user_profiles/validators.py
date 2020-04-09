# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Validators for user profiles."""

import re

from flask_babelex import lazy_gettext as _

username_regex = re.compile('^[a-zA-Z][a-zA-Z0-9-_]{2}[a-zA-Z0-9-_]*$')
"""Username rules."""

USERNAME_RULES = _(
    'Username must start with a letter, be at least three characters long and'
    ' only contain alphanumeric characters, dashes and underscores.')
"""Description of username validation rules.

.. note:: Used for both form help text and for form validation error."""


def validate_username(username):
    """Validate the username.

    See :data:`~.username_regex` to know which rules are applied.

    :param username: A username.
    :raises ValueError: If validation fails.
    """
    if not username_regex.match(username):
        raise ValueError(USERNAME_RULES)
