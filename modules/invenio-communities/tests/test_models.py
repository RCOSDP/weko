# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Model functions tests."""

from __future__ import absolute_import, print_function

import pytest

from invenio_communities.models import Community


@pytest.mark.parametrize('case_modifier', [
    (lambda x: x),
    (lambda x: x.upper()),
    (lambda x: x[0].upper() + x[1:]),
])
def test_filter_community(app, db, communities_for_filtering, user,
                          case_modifier):
    """Test the community filter task."""
    (comm0, comm1, comm2) = communities_for_filtering

    # Case insensitive
    results = Community.filter_communities(
                p=case_modifier('beautiful'),
                so='title').all()
    assert len(results) == 1
    assert {c.id for c in results} == {comm0.id}

    # Keyword search
    results = Community.filter_communities(
                p=case_modifier('errors'),
                so='title').all()
    assert len(results) == 1
    assert {c.id for c in results} == {comm2.id}

    # Partial keyword present
    results = Community.filter_communities(
                p=case_modifier('test'),
                so='title').all()
    assert len(results) == 3
    assert {c.id for c in results} == {comm0.id,
                                       comm1.id, comm2.id}

    # Order matter
    results = Community.filter_communities(
                p=case_modifier('explicit implicit'),
                so='title').all()
    assert len(results) == 1
    assert {c.id for c in results} == {comm0.id}

    results = Community.filter_communities(
                p=case_modifier('implicit explicit'),
                so='title').all()
    assert len(results) == 0
    assert {c.id for c in results} == set()
