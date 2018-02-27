# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Storage module tests."""

from __future__ import absolute_import, print_function

import pytest

from invenio_files_rest.helpers import make_path


def test_make_path():
    """Test path for files."""
    myid = 'deadbeef-dead-dead-dead-deaddeafbeef'
    base = '/base'
    f = 'data'

    assert make_path(base, myid, f, 1, 1) == \
        '/base/d/eadbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 3, 1) == \
        '/base/d/e/a/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 1, 3) == \
        '/base/dea/dbeef-dead-dead-dead-deaddeafbeef/data'
    assert make_path(base, myid, f, 2, 2) == \
        '/base/de/ad/beef-dead-dead-dead-deaddeafbeef/data'

    pytest.raises(AssertionError, make_path, base, myid, f, 1, 50)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 1)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 50)
