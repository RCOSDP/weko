from pytest_invenio.fixtures import database, app, es_clear
from mock import mock
from helpers import insert_action_to_db, login_user_via_session, insert_user_to_db, insert_flow_action, insert_flow_define, insert_flow_role
import flask
import pytest
from click.testing import CliRunner
from weko_workflow.cli import workflow

def side_effect_json1(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"3","name":"Item Registration","date":"2019-11-20","version":"1.0.1","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"8","name":"Approval by Guarantor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def side_effect_json2(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"8","name":"Approval by Guarantor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"3","name":"Item Registration","date":"2019-11-20","version":"1.0.1","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def side_effect_json3(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"3","name":"Item Registration","date":"2019-11-20","version":"1.0.1","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"8","name":"Approval by Guarantor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def side_effect_json4(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"3","name":"Item Registration","date":"2019-11-20","version":"1.0.1","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"8","name":"Approval by Guarantor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def side_effect_json5(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"3","name":"Item Registration","date":"2019-11-20","version":"1.0.1","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def side_effect_json6(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"3","name":"Item Registration","date":"2019-11-20","version":"1.0.1","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def side_effect_json7(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"3","name":"Item Registration","date":"2019-11-20","version":"1.0.1","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"DEL"}]

def side_effect_json8(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"10","name":"Approval by Administrator","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def side_effect_json9(*args, **kwargs):
    return [{"id":"1","name":"Start","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"9","name":"Approval by Advisor","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"},
            {"id":"2","name":"End","date":"2019-11-20","version":"1.0.0","user":"0","user_deny":False,"role":"0","role_deny":False,"action":"ADD"}]

def test_flow(app, database, client, es_clear):
    insert_user_to_db(database)
    insert_action_to_db(database)
    insert_flow_define()
    login_user_via_session(client, 1)
    res = client.get('/admin/')
    assert res.status_code == 200
    m = mock.MagicMock()
    m.get_json = side_effect_json1
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json2
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json3
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json4
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json5
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json6
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json7
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json8
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200

    m.get_json = side_effect_json9
    with mock.patch('weko_workflow.admin.request', m):
        res = client.post('/admin/flowsetting/action/18f974eb-bb67-446e-9ce1-db57110a74ca')
        assert res.status_code == 200
        
def test_cmd(app,database,script_info, es_clear):
    runner = CliRunner()
    command_args = 'init action_status,Action'.split()
    result = runner.invoke(workflow, command_args, obj=script_info)
    assert result.exit_code == 0
