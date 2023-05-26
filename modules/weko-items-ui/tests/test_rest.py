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
from flask import Flask, json, url_for
from mock import patch, MagicMock

from sqlalchemy.exc import SQLAlchemyError
from elasticsearch.exceptions import ElasticsearchException
from weko_admin.models import RankingSettings

ranking_type = [
    "new_items",
    "most_reviewed_items",
    "most_downloaded_items",
    "most_searched_keywords",
    "created_most_items_user"
]

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py::test_WekoRanking -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize('ranking_type', ranking_type)
def test_WekoRanking(app, client, db, db_ranking, ranking_type):
    """Test Ranking."""
    app.config['WEKO_ITEMS_UI_RANKING_DEFAULT_SETTINGS'] = {
    'is_show': True,
    'new_item_period': 14,
    'statistical_period': 365,
    'display_rank': 10,
    'rankings': {"new_items": True, "most_reviewed_items": True, "most_downloaded_items": True, "most_searched_keywords": True, "created_most_items_user": True}
    }
    res = client.get("/v1.0/ranking/" + ranking_type)
    assert res.status_code == 200
    try:
        json.loads(res.get_data())
        assert True
    except:
        assert False
        
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_rest.py::test_WekoRanking_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_WekoRanking_error(app, client, db, db_ranking):
    """Test Ranking."""
    url = "/v1.0/ranking/most_reviewed_items"
    
    app.config['WEKO_ITEMS_UI_RANKING_DEFAULT_SETTINGS'] = {
    'is_show': True,
    'new_item_period': 14,
    'statistical_period': 365,
    'display_rank': 10,
    'rankings': {"new_items": True, "most_reviewed_items": True, "most_downloaded_items": False, "most_searched_keywords": False, "created_most_items_user": False}
    }
    res = client.get(url)
    headers = {}
    headers['If-None-Match'] = res.headers['Etag'].strip('"')
    res = client.get(url, headers=headers)
    assert res.status_code == 304
    
    res = client.get("/ver1.0/ranking/most_reviewed_items")
    assert res.status_code == 400
    
    res = client.get("/v1.0/ranking/most_reviewed_items?display_rank=typeerror")
    assert res.status_code == 400
    
    res = client.get("/v1.0/ranking/no_ranking")
    assert res.status_code == 404

    with patch('weko_admin.models.RankingSettings.get', MagicMock(side_effect=SQLAlchemyError())):
        res = client.get(url)
        assert res.status_code == 500
        
    with patch('weko_admin.models.RankingSettings.get', MagicMock(side_effect=ElasticsearchException())):
        res = client.get(url)
        assert res.status_code == 500

    res = client.get("/v1.0/ranking/most_downloaded_items")
    assert res.status_code == 403