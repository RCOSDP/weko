# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
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

"""Tests for user profile validators."""

import pytest

from weko_user_profiles.validators import validate_username

test_usernames = {
    'valid': 'Good-Name_9',
    'invalid_begins_with_number': '9CantStartWithNumber',
    'invalid_characters': '_Containsi!!ega!Char acters*',
    'invalid_short': 'ab',
}


def test_validate_username(app):
    """Test username validator."""
    # Goodname can contain letters, numbers and starts with a letter
    validate_username(test_usernames['valid'])

    # Can't start with a number
    with pytest.raises(ValueError):
        validate_username(test_usernames['invalid_begins_with_number'])

    # Can only contain latin letters and numbers
    with pytest.raises(ValueError):
        validate_username(test_usernames['invalid_characters'])

    with pytest.raises(ValueError):
        validate_username(test_usernames['invalid_short'])
