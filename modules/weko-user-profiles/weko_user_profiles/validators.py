# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

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
