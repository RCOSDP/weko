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

"""Module tests."""
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

from __future__ import absolute_import, print_function

from invenio_records.api import Record
import pytest

from invenio_communities.models import InclusionRequest
from invenio_communities.tasks import delete_marked_communities, delete_expired_requests
from datetime import datetime,timedelta

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_tasks.py::test_community_delete_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_community_delete_task(app, db, communities):
    """Test the community deletion task."""
    (comm1, comm2, comm3) = communities
    communities_key = app.config["COMMUNITIES_RECORD_KEY"]
    rec1 = Record.create({'title': 'Foobar'})
    InclusionRequest.create(community=comm1, record=rec1, notify=False)

    assert InclusionRequest.get(comm1.id, rec1.id)

    comm1.accept_record(rec1)
    assert 'comm1' in rec1[communities_key]

    comm1.delete()
    assert comm1.is_deleted

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_tasks.py::test_delete_marked_communities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
# def delete_marked_communities():
def test_delete_marked_communities(app, db, communities):
    (comm1, comm2, comm3) = communities
    communities_key = app.config["COMMUNITIES_RECORD_KEY"]
    rec1 = Record.create({'title': 'Foobar'})
    InclusionRequest.create(community=comm1, record=rec1, notify=False)
    with pytest.raises(NotImplementedError):
        assert delete_marked_communities()
    
    
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_tasks.py::test_delete_expired_requests -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp    
# def delete_expired_requests(): do not work
def test_delete_expired_requests(app, db, communities):
    (comm1, comm2, comm3) = communities
    communities_key = app.config["COMMUNITIES_RECORD_KEY"]
    rec1 = Record.create({'title': 'Foobar'})
    InclusionRequest.create(community=comm1, record=rec1,notify=False)
    assert delete_expired_requests()

    