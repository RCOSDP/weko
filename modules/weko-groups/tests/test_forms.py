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


"""Test groups formss."""

import pytest
from wtforms.validators import ValidationError

from weko_groups.forms import EmailsValidator, NewMemberForm


def test_emails_validator(app):
    """
    Test validation of email addresses.

    :param app: The flask application.
    """
    with app.app_context():
        validator = EmailsValidator()
        form = NewMemberForm()

        form.emails.data = '\n'.join([
            '',
            'test_example@example.com',
            'example@net.com',
            '',
            'test.user@example.net',
        ])

        validator(form, form.emails)

        form.emails.data += '\ninvalid_email'
        with pytest.raises(ValidationError):
            validator(form, form.emails)
