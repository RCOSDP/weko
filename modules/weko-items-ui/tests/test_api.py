# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp

import pytest
from mock import patch
from unittest.mock import MagicMock
import json
from weko_items_ui.api import item_login
from flask import session

# def item_login(item_type_id: int = 0):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_api.py::test_item_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_item_login(app,client,db_itemtype,users,request):
    with open('tests/data/temp_data.json', 'r') as f:
        temp_data = json.dumps(json.load(f))
    
    with open('tests/data/temp_data2.json', 'r') as f:
        temp_data2 = json.dumps(json.load(f))
    
    with open('tests/data/temp_data3.json', 'r') as f:
        temp_data3 = json.dumps(json.load(f))

    with app.test_request_context():
        with patch('weko_workflow.api.WorkActivity.get_activity_metadata',return_value=temp_data):
            with patch('flask.templating._render', return_value=''):
                with client.session_transaction() as session:
                    session['activity_info'] = {'activity_id': 'A-20220818-00001', 'action_id': 3, 'action_version': '1.0.1', 'action_status': 'M', 'commond': ''}
                    assert item_login(1)==('weko_items_ui/iframe/item_edit.html', True, False, {}, '/items/jsonschema/1', '/items/schemaform/1', '/items/iframe/model/save', [], {}, True, [], False)
                    assert item_login(0)==('weko_items_ui/iframe/error.html', False, False, {}, '/items/jsonschema/0', '/items/schemaform/0', '/items/iframe/model/save', [], {}, False, [], False)
                    assert item_login(99)==('weko_items_ui/iframe/error.html', False, False, {}, '/items/jsonschema/99', '/items/schemaform/99', '/items/iframe/model/save', [], {}, False, [], False)

    with app.test_request_context('weko_items_ui/iframe/'):
        with patch('weko_workflow.api.WorkActivity.get_activity_metadata',return_value=temp_data2):
            with patch('flask.templating._render', return_value=''):
                with client.session_transaction() as session:
                    session['activity_info'] = {'activity_id': 'A-20220818-00001', 'action_id': 3, 'action_version': '1.0.1', 'action_status': 'M', 'commond': ''}
                    assert item_login(1)==('weko_items_ui/iframe/item_edit.html', True, False, {}, '/items/jsonschema/1', '/items/schemaform/1', '/items/iframe/model/save', [], {}, True, [], False)
                    assert item_login(0)==('weko_items_ui/iframe/error.html', False, False, {}, '/items/jsonschema/0', '/items/schemaform/0', '/items/iframe/model/save', [], {}, False, [], False)
                    assert item_login(99)==('weko_items_ui/iframe/error.html', False, False, {}, '/items/jsonschema/99', '/items/schemaform/99', '/items/iframe/model/save', [], {}, False, [], False)

    with app.test_request_context():
        with patch('weko_workflow.api.WorkActivity.get_activity_metadata',return_value=temp_data3):
            with patch('flask.templating._render', return_value=''):
                with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                    with app.test_client() as client:
                        with client.session_transaction() as session:
                            session['activity_info'] = {'activity_id': 'A-20220818-00001', 'action_id': 3, 'action_version': '1.0.1', 'action_status': 'M', 'commond': ''}
                        assert item_login(1)==('weko_items_ui/iframe/item_edit.html', True, False, {}, '/items/jsonschema/1', '/items/schemaform/1', '/items/iframe/model/save', [], {}, True, [], False)
                        assert item_login(0)==('weko_items_ui/iframe/error.html', False, False, {}, '/items/jsonschema/0', '/items/schemaform/0', '/items/iframe/model/save', [], {}, False, [], False)
                        assert item_login(99)==('weko_items_ui/iframe/error.html', False, False, {}, '/items/jsonschema/99', '/items/schemaform/99', '/items/iframe/model/save', [], {}, False, [], False)





