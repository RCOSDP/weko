

from re import L

import pytest
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import CombinedMultiDict

from weko_search_ui import default_search_factory


@pytest.fixture
def request():
    request['values'] = CombinedMultiDict([ImmutableMultiDict([('page', '1'), ('size', '20'), ('sort', 'wtl'), ('timestamp', '1636732132.1051335'), ('search_type', '0'), ('q', ''), ('title', ''), ('creator', ''), ('text1', ''), ('text2', ''), (
        'text3', ''), ('text4', ''), ('text5', ''), ('text6', ''), ('text7', ''), ('text8', ''), ('text9', ''), ('text10', ''), ('text11', ''), ('date_range1_from', '19990101'), ('date_range1_to', '19991231')]), ImmutableMultiDict([])])
    return request


def test__get_date_query(request):
    
    _get_date_query('date_range1', [('from', 'to'), 'date_range1']) == {}
