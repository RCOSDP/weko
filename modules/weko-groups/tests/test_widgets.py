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
# WEKO3 is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.


"""Test groups data models."""

import pytest
from mock import patch, MagicMock

from weko_groups.widgets import RadioGroupWidget


# class RadioGroupWidget(object):
# def __call__(self, field, **kwargs):
def test___call__(app):
    # The widget reads field.default and iterates the field to get its
    # subfields, so it needs the field itself - not a bare list of subfields.
    test = RadioGroupWidget(descriptions={"data": "description"})
    subfield = MagicMock()
    subfield.label = MagicMock()
    subfield.label.text = "text"
    subfield.data = "data"
    subfield.return_value = "<input>"

    field = MagicMock()
    field.default = "data"
    field.__iter__.return_value = iter([subfield])

    html = test.__call__(field=field)

    assert subfield.checked is True
    assert "text" in html
    assert "description" in html
