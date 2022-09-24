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

"""Module tests."""

import pytest
from elasticsearch.exceptions import NotFoundError
from mock import patch, MagicMock

from weko_deposit.tasks import update_items_by_authorInfo


class MockRecordsSearch:
    class MockQuery:
        class MockExecute:
            def __init__(self):
                pass
            def to_dict(self):
                raise NotFoundError
        def __init__(self):
            pass
        def execute(self):
            return self.MockExecute()
    def __init__(self, index=None):
        pass
    
    def update_from_dict(self,query=None):
        return self.MockQuery()


def test_update_authorInfo(app, db):
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    with patch('weko_deposit.tasks.RecordsSearch', mock_recordssearch):
        with pytest.raises(NotFoundError):
            update_items_by_authorInfo([], {})
