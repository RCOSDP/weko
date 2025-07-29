import json
import uuid
from datetime import datetime
from unittest.mock import Mock, MagicMock, call, patch

import pytest
import math
from flask import current_app, session
from flask_login.utils import login_user, logout_user
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
from marshmallow import ValidationError
from requests import HTTPError
from sqlalchemy import and_, or_, not_
from sqlalchemy.exc import SQLAlchemyError

from weko_notifications.notifications import Notification
from weko_records.api import ItemsMetadata
from weko_workflow.api import Flow, GetCommunity, WorkActivity, WorkFlow, UpdateItem
from weko_workflow.models import Activity, ActivityHistory, ActivityAction, FlowAction, FlowActionRole
from weko_schema_ui.models import PublishStatus

from invenio_accounts.models import Role, User
from invenio_pidstore.errors import PIDAlreadyExists
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from weko_workflow.models import Action as _Action
from weko_workflow.models import Activity as _Activity
from weko_workflow.models import ActivityAction
from weko_workflow.models import FlowAction as _FlowAction
from weko_workflow.models import FlowActionRole as _FlowActionRole
from weko_workflow.models import FlowDefine as _Flow
from weko_workflow.models import WorkFlow as _WorkFlow
from weko_workflow.models import ActionStatusPolicy, Activity, ActivityAction, FlowActionRole, ActivityRequestMail, ActivityItemApplication
from weko_records.models import RequestMailList as _RequestMailList
from weko_records.models import ItemApplication as _ItemApplication


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_create_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_create_flow(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()

        flow = _flow.create_flow({'flow_name': 'create_flow_test_root', 'repository_id': 'Root Index'})
        assert flow.flow_name == 'create_flow_test_root'
        assert flow.repository_id == 'Root Index'

        flow = _flow.create_flow({'flow_name': 'create_flow_test_1', 'repository_id': 'comm01'})
        assert flow.flow_name == 'create_flow_test_1'
        assert flow.repository_id == 'comm01'

        with pytest.raises(ValueError, match='Flow name cannot be empty.'):
            _flow.create_flow({'flow_name': '', 'repository_id': 'com1'})

        with pytest.raises(ValueError, match='Repository cannot be empty.'):
            _flow.create_flow({'flow_name': 'test_flow'})

        with pytest.raises(ValueError, match='Flow name is already in use.'):
            _flow.create_flow({'flow_name': 'create_flow_test_root', 'repository_id': 'Root Index'})

        with pytest.raises(ValueError, match='Repository is not found.'):
            _flow.create_flow({'flow_name': 'test_flow', 'repository_id': '999'})

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_upt_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_upt_flow(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'upt_flow_test', 'repository_id': 'Root Index'})

        flow = _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': 'Root Index'})
        assert flow.flow_name == 'upt_flow_test_1'
        assert flow.repository_id == 'Root Index'

        flow = _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': 'comm01'})
        assert flow.flow_name == 'upt_flow_test_1'
        assert flow.repository_id == 'comm01'

        with pytest.raises(ValueError, match='Flow name cannot be empty.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': '', 'repository_id': 'Root Index'})

        with pytest.raises(ValueError, match='Repository cannot be empty.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': ''})

        flow1 = _flow.create_flow({'flow_name': 'upt_flow_test', 'repository_id': 'comm01'})
        db.session.add(flow)
        db.session.add(flow1)
        db.session.commit()
        with pytest.raises(ValueError, match='Flow name is already in use.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test', 'repository_id': 'Root Index'})

        with pytest.raises(ValueError, match='Repository is not found.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'test_flow', 'repository_id': '999'})

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_get_flow_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_get_flow_list(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'get_flow_list_test', 'repository_id': 'Root Index'})
        db.session.add(flow)
        db.session.commit()

        login_user(users[2]["obj"])
        res = _flow.get_flow_list()
        assert len(res) == 1
        assert res[0] == flow

        login_user(users[3]["obj"])
        res = _flow.get_flow_list()
        assert len(res) == 0

        flow_com = _flow.create_flow({'flow_name': 'flow_comm01', 'repository_id': 'comm01'})
        db.session.add(flow_com)
        db.session.commit()

        res = _flow.get_flow_list()
        assert len(res) == 1
        assert res[0] == flow_com


class TestFlow:
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_action(self,app, client, users, db, action_data):
        with app.test_request_context():
            login_user(users[2]["obj"])
            _flow = Flow()
            flow = _flow.create_flow({'flow_name': 'create_flow_test', 'repository_id': 'Root Index'})
            assert flow.flow_name == 'create_flow_test'

            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":7,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":-1,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                "action":"ADD"
                }
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)

            flow_id = flow.flow_id
            flow = _flow.get_flow_detail(flow_id)
            assert flow.flow_name == 'create_flow_test'

            res = _flow.del_flow(flow_id)
            assert res['code'] == 500

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_upt_flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_item_registrant', [
        (-2, True, None, True, True),
        (-2, False, None, False, True),
        (2, True, 2, True, False),
        (2, False, 2, False, False),
    ])
    def test_upt_flow_action(self, app, client, users, db, action_data, user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_item_registrant):
        with app.test_request_context():
            login_user(users[2]["obj"])
            _flow = Flow()
            flow = _flow.create_flow({'flow_name': 'create_flow_test'})

            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":7,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":-1,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                }
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)

            actual =  db.session.query(FlowActionRole).get(3)
            if expected_action_user is None:
                assert actual.action_user is None
            else:
                assert actual.action_user == expected_action_user
            assert actual.specify_property is None
            assert actual.action_user_exclude == expected_action_user_exclude
            assert actual.action_item_registrant == expected_action_item_registrant
            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"parentkey.subitem_restricted_access_guarantor_mail_address",
                    "user_deny": True,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":db.session.query(FlowActionRole).get(2).flow_action_id,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"UPDATE"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":actual.flow_action_id,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"DEL"
                }
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)
            actual =  db.session.query(FlowActionRole).get(3)
            update_actual = db.session.query(FlowActionRole).get(5)
            assert actual == None
            assert update_actual.action_user_exclude == True
            assert update_actual.specify_property == "parentkey.subitem_restricted_access_guarantor_mail_address"



    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_upt_flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_request_mail', [
        (-3, True, None, True, True),
        (-3, False, None, False, True),
    ])
    def test_upt_flow_action_for_request_mail(self, app, client, users, db, action_data, user_id, user_deny, expected_action_user, expected_action_user_exclude, expected_action_request_mail):
        with app.test_request_context():
            login_user(users[2]["obj"])
            _flow = Flow()
            flow = _flow.create_flow({'flow_name': 'create_flow_test'})

            _flow_data = [
                {
                    "id":"2",
                    "name":"End",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":8,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False},
                    "action":"ADD"
                },
                {
                    "id":"1",
                    "name":"Start",
                    "date":"2022-12-09",
                    "version":"1.0.0",
                    "user":"2",
                    "user_deny": False,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":7,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"3",
                    "name":"Item Registration",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":-1,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
                {
                    "id":"4",
                    "name":"Request Mail",
                    "date":"2022-12-9",
                    "version":"1.0.1",
                    "user":str(user_id),
                    "user_deny": user_deny,
                    "role":"0",
                    "role_deny": False,
                    "workflow_flow_action_id":4,
                    "send_mail_setting": {
                        "request_approval": False,
                        "inform_approval": False,
                        "inform_reject": False
                    },
                    "action":"ADD"
                },
            ]
            _flow.upt_flow_action(flow.flow_id, _flow_data)

            actual =  db.session.query(FlowActionRole).get(4)
            if expected_action_user is None:
                assert actual.action_user is None
            else:
                assert actual.action_user == expected_action_user
            assert actual.specify_property is None
            assert actual.action_user_exclude == expected_action_user_exclude
            assert actual.action_request_mail == expected_action_request_mail

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_get_flow_action_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_flow_action_list(self, db,workflow):
        res = Flow().get_flow_action_list(workflow["flow"].id)
        assert len(res) == 7
        assert res[0].action_order == 1
        assert res[1].action_order == 2
        assert res[2].action_order == 3
        assert res[3].action_order == 4
        assert res[4].action_order == 5
        assert res[5].action_order == 6
        assert res[6].action_order == 7


class TestWorkActivity:
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_filter_by_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_filter_by_date(self,app, db):
        query = db.session.query()
        activity = WorkActivity()
        assert activity.filter_by_date('2022-01-01', '2022-01-02', query)


    conditions = [
        {
            'tab': ['todo'],
            'pagestodo': ['1'],
            'sizetodo': ['10']
        },
        {
            'tab': ['wait'],
            'pageswait': ['1'],
            'sizewait': ['10']
        },
        {
            'tab': ['all'],
            'pagesall': ['1'],
            'sizeall': ['10']
        },
        {
            'tab': ['todo']
        },
        {
            'tab': ['wait']
        },
        {
            'tab': ['all']
        }
    ]

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_WorkActivity_get_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('conditions', conditions)
    def test_WorkActivity_get_activity_list(self, app, users, db_register_activity, conditions):
        # test preparation
        activity = WorkActivity()

        # contributor
        with app.test_request_context():
            login_user(users[0]['obj'])
            activities, max_page, size, page, name_param, count = \
                activity.get_activity_list(conditions, False)
            
            if conditions.get('tab')[0] == 'todo':
                assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
                assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
                assert max_page == 1
                assert count == 1
                assert name_param == ''
                assert activities[0].activity_id == db_register_activity.get('activity')[0].activity_id
                assert activities[0].title == db_register_activity.get('activity')[0].title
            elif conditions.get('tab')[0] == 'wait':
                assert size == conditions.get('sizewait')[0] if conditions.get('sizewait') else '20'
                assert page == conditions.get('pageswait')[0] if conditions.get('pageswait') else '1'
                assert max_page == 1
                assert count == 1
                assert name_param == ''
                assert activities[0].activity_id == db_register_activity.get('activity')[2].activity_id
                assert activities[0].title == db_register_activity.get('activity')[2].title
            elif conditions.get('tab')[0] == 'all':
                assert size == conditions.get('sizeall')[0] if conditions.get('sizeall') else '20'
                assert page == conditions.get('pagesall')[0] if conditions.get('pagesall') else '1'
                assert max_page == 1
                assert count == 1
                assert name_param == ''
                assert activities[0].activity_id == db_register_activity.get('activity')[0].activity_id
                assert activities[0].title == db_register_activity.get('activity')[0].title
            else:
                assert False

        # sysadmin
        with app.test_request_context():
            login_user(users[2]['obj'])
            activities, max_page, size, page, name_param, count = \
                activity.get_activity_list(conditions, False)

            if conditions.get('tab')[0] == 'todo':
                assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
                assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
                assert max_page == 1
                assert count == 3
                assert name_param == ''
                for i in range(0, 3):
                    assert activities[i].activity_id == db_register_activity.get('activity')[2-i].activity_id
                for i in range(0, 3):
                    assert activities[i].title == db_register_activity.get('activity')[2-i].title
            elif conditions.get('tab')[0] == 'wait':
                assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
                assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
                assert max_page == 1
                assert count == 1
                assert activities[0].activity_id == db_register_activity.get('activity')[2].activity_id
                assert activities[0].title == db_register_activity.get('activity')[2].title
            elif conditions.get('tab')[0] == 'all':
                assert size == conditions.get('sizeall')[0] if conditions.get('sizeall') else '20'
                assert page == conditions.get('pagesall')[0] if conditions.get('pagesall') else '1'
                assert max_page == 1
                assert count == 3
                assert name_param == ''
                for i in range(0, 3):
                    assert activities[i].activity_id == db_register_activity.get('activity')[2-i].activity_id
                for i in range(0, 3):
                    assert activities[i].title == db_register_activity.get('activity')[2-i].title
            else:
                assert False


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_all_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_all_activity_list(self,app, client, users, db_register):
        with app.test_request_context():
            login_user(users[2]["obj"])
            activity = WorkActivity()
            activities = activity.get_all_activity_list()
            assert len(activities) == 13


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_activity_index_search(self,app, db_register):
        activity = WorkActivity()
        with app.test_request_context():
            activity_detail, item, steps, action_id, cur_step, \
                temporary_comment, approval_record, step_item_login_url,\
                histories, res_check, pid, community_id, ctx = activity.get_activity_index_search("1")
            assert activity_detail.id == 1
            assert activity_detail.action_id == 1
            assert activity_detail.title == 'test'
            assert activity_detail.activity_id == '1'
            assert activity_detail.flow_id == 1
            assert activity_detail.workflow_id == 1
            assert activity_detail.action_order == 1


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_upt_activity_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_upt_activity_detail(self,app, db_register, db_records):
        activity = WorkActivity()
        db_activity = activity.upt_activity_detail(db_records[2][2].id)
        assert db_activity == None


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_corresponding_usage_activities(self,app, db_register):
        activity = WorkActivity()
        usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
        assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
        assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_check_community_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_check_community_permission(self,app,db_register):
        activity = WorkActivity()
        activities = db_register["activities"]
        not_itemid_act = activities[0]
        # not exist activity.item_id
        result = WorkActivity._check_community_permission(not_itemid_act, ["1"])

        assert result == True

        assert 1==2
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_query_check_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_query_check_path(self, db):
        index_list = ["1","2","3"]
        metadatas = [
            {"title":"not_exist_path"},
            {"title":"deny_path","path":["4","5","6"]},
            {"title":"allow_path","path":["3","4","5"]}]
        record_metadatas = []
        for metadata in metadatas:
            record_metadatas.append(
                RecordMetadata(json=metadata)
            )
        db.session.add_all(record_metadatas)
        db.session.commit()

        # Get metadata path that contain elements of index_list
        exist_query = WorkActivity._WorkActivity__query_check_path(index_list,is_within=True)
        result = db.session.query(RecordMetadata).filter(exist_query).all()
        assert len(result)==1
        assert result[0].json==metadatas[2]

        # Get metadata path that does not contain any index_list elements
        exist_query = WorkActivity._WorkActivity__query_check_path(index_list,is_within=False)
        result = db.session.query(RecordMetadata).filter(exist_query).all()
        assert len(result)==2
        assert result[0].json==metadatas[0]
        assert result[1].json==metadatas[1]

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_community_user_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_community_user_ids(self,client, activity_acl_users):
        users = activity_acl_users["users"]
        # not login
        result = WorkActivity._WorkActivity__get_community_user_ids()
        assert result == []

        # no role
        login_user(users[6])
        result = WorkActivity._WorkActivity__get_community_user_ids()
        assert result == []

        # no communities
        login_user(users[4])
        result = WorkActivity._WorkActivity__get_community_user_ids()
        assert result == []

        # exist communities
        login_user(users[3])
        result = WorkActivity._WorkActivity__get_community_user_ids()
        assert result == [3,4]

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_activity_list(client, activity_acl, activity_acl_users, db):
        # {user_id:{tab:[activity_id,...],...}}
        result = {
            1:{# sysadmin
                "todo":[43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 28, 27, 26, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 7, 6, 5, 2, 1],
                "wait":[],
                "all":[43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
            },
            3:{# test_role01_user
                "todo":[42, 38, 37, 34, 33, 32, 31, 27, 22, 21, 19, 18, 16, 14, 5],
                "wait":[17], 
                "all":[42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 19, 18, 16, 14, 5]
            },
            4:{# test_role01_comadmin
                "todo":[42, 41, 40, 38, 34, 32, 26, 23, 22, 18, 16, 14, 12, 11, 10, 7, 6, 5],
                "wait":[39], 
                "all":[42, 41, 40, 38, 34, 32, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5]
            },
            5:{# test_role02_user
                "todo":[40,35,19,15,10],
                "wait":[],
                "all":[40,35,19,15,10]
            },
        }

        size_list = [20, 50, 75]
        activity = WorkActivity()
        for user_id, tag_act in result.items():
            user = User.query.filter_by(id=user_id).one()
            login_user(user)
            for tab, acts in tag_act.items():
                for res_size in size_list:
                    num_page = math.ceil(len(acts)/res_size)
                    for res_page in range(num_page):
                        res_page = res_page + 1
                        conditions={"tab":[tab]}
                        if res_size != 20:
                            conditions["size{}".format(tab)]=[str(res_size)]
                        if res_page != 1:
                            conditions["pages{}".format(tab)]=[str(res_page)]
                        activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions)
                        assert [ac.id for ac in activities] == acts[res_size*(res_page-1):res_size*res_page]
                        assert max_page == num_page
                        assert size == str(res_size)
                        assert page == str(res_page)
                        assert count == len(acts)

                num_page = math.ceil(len(acts)/20)
                conditions = {"tab":[tab]}
                # is_get_all = True
                activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions,is_get_all=True)
                assert [ac.id for ac in activities] == acts
                assert max_page == num_page
                assert size == '20'
                assert page == '1'
                assert count == len(acts)

                # activitylog = True
                activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions,activitylog=True)
                assert [ac.id for ac in activities] == acts
                assert max_page == math.ceil(len(acts)/100000)
                assert size == 100000
                assert page == 1
                assert count == len(acts)

        # count = 0
        user = User.query.filter_by(id=7).one()
        login_user(user)
        conditions={"tab":["todo"]}
        activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions)
        assert activities == []
        assert max_page == 0
        assert size == '20'
        assert page == '1'

        current_app.config['WEKO_ITEMS_UI_MULTIPLE_APPROVALS'] = False
        user = User.query.filter_by(id=7).one()
        login_user(user)
        conditions={"tab":["todo"]}
        activities, max_page, size, page, name_param, count = activity.get_activity_list(conditions=conditions)
        assert activities == []
        assert max_page == 0
        assert size == '20'
        assert page == '1'
    
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_usage_report_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_usage_report_activities(app, activity_usage_report):
        activity = WorkActivity()
        result = activity.get_usage_report_activities([])
        assert result == activity_usage_report

        result = activity.get_usage_report_activities([str(activity.activity_id) for activity in activity_usage_report])
        assert result == activity_usage_report

        result = activity.get_usage_report_activities([], size=5, page=1)
        assert len(result) == 5
        assert result == activity_usage_report[:5]

        result = activity.get_usage_report_activities([str(activity.activity_id) for activity in activity_usage_report], size=5, page=2)
        assert len(result) == 5
        assert result == activity_usage_report[5:10]
    
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_count_all_usage_report_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_count_all_usage_report_activities(app, activity_usage_report):
        activity = WorkActivity()
        result = activity.count_all_usage_report_activities([])
        assert result == 10

        result = activity.count_all_usage_report_activities([str(activity.activity_id) for activity in activity_usage_report[:5]])
        assert result == 5


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_count_waiting_approval_by_workflow_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_count_waiting_approval_by_workflow_id(app, db, db_register):
    activity = WorkActivity()
    assert activity.count_waiting_approval_by_workflow_id(1) == 0


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkFlow_upt_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkFlow_upt_workflow(app, db, workflow, logging_client):
    w = workflow["workflow"]
    _workflow = WorkFlow()
    data = dict(flows_id=w.flows_id,
                flows_name='test workflow01',
                itemtype_id=1,
                flow_id=1,
                index_tree_id=None,
                open_restricted=False,
                location_id=None,
                is_gakuninrdm=False,
                repository_id='Root Index')

    res = _workflow.upt_workflow(data)
    for key in data:
        assert getattr(res, key) == data[key]

    res = _workflow.upt_workflow({'flows_id': uuid.uuid4()})
    assert res is None

    with pytest.raises(AssertionError):
        _workflow.upt_workflow(None)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkFlow_get_workflow_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkFlow_get_workflow_list(app, db, workflow, users):
    w = workflow["workflow"]
    _workflow = WorkFlow()
    res = _workflow.get_workflow_list()
    assert len(res) == 1

    user = users[2]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 1

    user = users[3]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 0

    w.repository_id = "comm01"
    db.session.commit()
    user = users[3]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 1
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_filter_by_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_filter_by_action(app, db):
    query = db.session.query(Activity)
    activity = WorkActivity()


    # case: empty action
    list_action = []
    assert activity._WorkActivity__filter_by_action(query, list_action) == query


    # case: single action, correct
    list_action = ['start']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([1])))

    list_action = ['end']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([2])))

    list_action = ['itemregistration']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([3])))

    list_action = ['approval']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([4])))

    list_action = ['itemlink']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([5])))

    list_action = ['oapolicyconfirmation']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([6])))

    list_action = ['identifiergrant']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([7])))


    # case: single action, incorrect
    list_action = ['invalid_action']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([])))


    # case: multiple actions, correct
    list_action = ['start', 'itemregistration', 'approval', 'identifiergrant']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([1, 3, 4, 7])))


    # case: multiple actions, incorrect
    list_action = ['invalid1', 'invalid2', 'invalid3']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(Activity.action_id.in_([])))


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_activity_index_search(app, db_register):
    activity = WorkActivity()
    with app.test_request_context():
        activity_detail, item, steps, action_id, cur_step, \
            temporary_comment, approval_record, step_item_login_url,\
            histories, res_check, pid, community_id, ctx = activity.get_activity_index_search('1')
        assert activity_detail.id == 1
        assert activity_detail.action_id == 1
        assert activity_detail.title == 'test'
        assert activity_detail.activity_id == '1'
        assert activity_detail.flow_id == 1
        assert activity_detail.workflow_id == 1
        assert activity_detail.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_upt_activity_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_upt_activity_detail(app, db_register, db_records):
    activity = WorkActivity()
    db_activity = activity.upt_activity_detail(db_records[2][2].id)
    assert db_activity.id == 4
    assert db_activity.action_id == 2
    assert db_activity.title == 'test item1'
    assert db_activity.activity_id == '2'
    assert db_activity.flow_id == 1
    assert db_activity.workflow_id == 1
    assert db_activity.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_corresponding_usage_activities(app, db_register):
    activity = WorkActivity()
    usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
    assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
    assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_init_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_init_activity(app, users, item_type, workflow):
    """
    Test init_activity

    Args:
        app (fixture):
        users (fixture): user info
        item_type (fixture): item_type data
        workflow (fixture): data of FlowDefine, FlowAction, WorkFlow
    """
    workflow_id = workflow['workflow'].id
    flow_def_id = workflow['flow'].id
    with app.test_request_context():
        login_user(users[2]["obj"])
        # send param
        input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}

        # 51992 case.01(init_activity)
        q = Activity.query.all()
        assert len(q) == 0
        q = ActivityHistory.query.all()
        assert len(q) == 0
        q = ActivityAction.query.all()
        assert len(q) == 0

        activity = WorkActivity()
        input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
        activity_detail = activity.init_activity(input)
        assert isinstance(activity_detail, Activity)
        q = Activity.query.all()
        assert len(q) == 1
        q = ActivityHistory.query.all()
        assert len(q) == 1
        q = ActivityAction.query.all()
        assert len(q) == 7


        with patch("weko_workflow.api.current_app") as mock_current_app:
            mock_current_app.config = {
                'WEKO_WORKFLOW_ENABLE_SHOWING_TERM_OF_USE': True,
                'WEKO_ITEMS_UI_SHOW_TERM_AND_CONDITION': ['itemtype_with_terms'],
                'WEKO_WORKFLOW_MAX_ACTIVITY_ID': 1000000,
                'WEKO_WORKFLOW_ACTIVITY_ID_FORMAT': 'A-{}-{}'
            }

            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'activity_confirm_term_of_use': False}
            # 51992 case.02(init_activity)
            with patch('weko_workflow.api.get_item_type_name', return_value='itemtype_with_terms'):
                activity_detail = activity.init_activity(input)
                assert activity_detail.activity_confirm_term_of_use == False

            # 51992 case.03(init_activity)
            with patch('weko_workflow.api.get_item_type_name', return_value='itemtype_with_terms2'):
                activity_detail = activity.init_activity(input)
                assert activity_detail.activity_confirm_term_of_use == True

            # 51992 case.04(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
            activity_detail = activity.init_activity(input)
            assert activity_detail.activity_login_user == str(users[2]["obj"].id)

            # 51992 case.05(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'activity_login_user': 1}
            activity_detail = activity.init_activity(input)
            assert activity_detail.activity_login_user == 1

            # 51992 case.08(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'related_title': 'Test%20Title'}
            activity_detail = activity.init_activity(input)
            assert activity_detail.extra_info["related_title"] == 'Test Title'

            # 51992 case.09(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
            with patch("weko_workflow.api.PersistentIdentifier.create", side_effect=Exception("Test Error")):
                with pytest.raises(Exception):
                    activity.init_activity(input)

            # 51992 case.10(init_activity)
            with patch("weko_workflow.api.db.session.add", side_effect=Exception("Test Error")):
                input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
                with pytest.raises(Exception):
                    activity.init_activity(input)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_init_activity_with_single_flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_with_single_flow_action(app, users, item_type, workflow_one, mocker):
    """
    Test init_activity when FlowAction return a data

    Args:
        app (fixture):
        users (fixture): user info
        item_type (fixture): item_type data
        workflow_one (fixture): one FlowAction workflow
        mocker (fixture): mocker
    """
    workflow_id = workflow_one["workflow"].flows_id
    flow_id = int(workflow_one["flow"].id)
    work_activity = WorkActivity()
    # send param
    input = {'workflow_id': workflow_id, 'flow_id': flow_id}

    # mock
    mocker.patch("weko_workflow.api.PersistentIdentifier.create")
    mocker.patch("weko_workflow.api.db.session.add")

    # 51992 case.06(init_activity)
    with app.test_request_context():
        result = work_activity.init_activity(input)

        assert result.action_id == 0
        assert result.action_order == 0


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_init_activity_with_no_begin_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_with_no_begin_action(app, users, item_type, workflow, no_begin_action, mocker):
    """
    Test init_activity when workflow_action has not begin_action

    Args:
        app (fixture):
        users (fixture): user info
        item_type (fixture): item_type data
        workflow (fixture): data of FlowDefine, FlowAction, WorkFlow
        no_begin_action(fixture): update begin_action to other_action
        mocker (fixture): mocker
    """
    workflow_id = workflow['workflow'].id
    flow_def_id = workflow['flow'].id
    work_activity = WorkActivity()
    # send param
    input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}

    # mock
    mocker.patch("weko_workflow.api.PersistentIdentifier.create")
    mocker.patch("weko_workflow.api.db.session.add")

    # 51992 case.07(init_activity)
    with app.test_request_context():
        with pytest.raises(AttributeError):
            result = work_activity.init_activity(input)

            assert result.action_id == 0  # action_id should be the initial value

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_GetCommunity_get_community_by_root_node_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_GetCommunity_get_community_by_root_node_id(db):
    communities = GetCommunity.get_community_by_root_node_id(1738541618993)
    assert communities is not None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_deleted_workflow_list -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_deleted_workflow_list(app,db,workflow):
    res = WorkFlow().get_deleted_workflow_list()
    assert res[0].flows_name == "test workflow02"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_activity_request_mail_list_create_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_activity_request_mail_list_create_and_update(app, workflow, db, mocker):
    activity = WorkActivity()
    _request_maillist1 = []
    _request_maillist2 = [{"email": "test@example.com", "author_id": ""}]
    activity.create_or_update_activity_request_mail("1", _request_maillist1, True)
    assert activity.get_activity_request_mail("1").request_maillist == []
    activity.create_or_update_activity_request_mail("1", _request_maillist2, True)
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2
    activity.create_or_update_activity_request_mail("1111111", _request_maillist1, "aaa")
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize("case, param_method, notification_method, mail_method", [
    ("registered", "_get_params_for_registrant", "create_item_registered", "send_mail_item_registered"),
    ("request_approval", "_get_params_for_approver", "create_request_approval", "send_mail_request_approval"),
    ("approved", "_get_params_for_registrant", "create_item_approved", "send_mail_item_approved"),
    ("rejected", "_get_params_for_registrant", "create_item_rejected", "send_mail_item_rejected"),
    ("deleted", "_get_params_for_registrant", "create_item_deleted", "send_mail_item_deleted"),
    ("deletion_request", "_get_params_for_approver", "create_request_delete_approval", "send_mail_request_delete_approval"),
    ("deletion_approved", "_get_params_for_registrant", "create_item_delete_approved", "send_mail_item_delete_approved"),
    ("deletion_rejected", "_get_params_for_registrant", "create_item_delete_rejected", "send_mail_item_delete_rejected"),
])
def test_workactivity_notify_about_activity(app, db_register, mocker, case, param_method, notification_method, mail_method):
    app.config["WEKO_NOTIFICATIONS"] = True
    activity1 = db_register["activities"][0]
    activity = WorkActivity()

    mock_notify = mocker.patch.object(activity, "_notify_about_activity_wiht_case")
    mock_mail = mocker.patch.object(activity, mail_method)

    activity.notify_about_activity(activity1.activity_id, case)

    expected_params = getattr(activity, param_method)
    expected_notification = getattr(Notification, notification_method)

    mock_notify.assert_called_once_with(activity1, case, expected_params, expected_notification)
    mock_mail.assert_called_once_with(activity1)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_early_return -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_early_return(app, db, db_register, mocker):
    activity = WorkActivity()

    # with WEKO_NOTIFICATIONS is False
    app.config["WEKO_NOTIFICATIONS"] = False
    activity1 = db_register["activities"][0]
    mock_get_activity_by_id = mocker.patch.object(activity, "get_activity_by_id")
    assert activity.notify_about_activity(activity1.activity_id, 'registered') == None
    mock_get_activity_by_id.assert_not_called()

    # with restricted workflow
    app.config["WEKO_NOTIFICATIONS"] = True
    activity1.workflow.open_restricted = True
    mock_notify = mocker.patch.object(activity, "_notify_about_activity_wiht_case")
    mock_mail = mocker.patch.object(activity, "send_mail_item_registered")
    assert activity.notify_about_activity(activity1.activity_id, 'registered') == None
    mock_notify.assert_not_called()
    mock_mail.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_invalid_case -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_invalid_case(app, db, db_register, mocker):
    activity = WorkActivity()
    app.config["WEKO_NOTIFICATIONS"] = True
    activity1 = db_register["activities"][0]
    mock_notify = mocker.patch.object(activity, "_notify_about_activity_wiht_case")
    assert activity.notify_about_activity(activity1.activity_id, 'invalid_case') == None
    mock_notify.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_get_params_for_registrant -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_get_params_for_registrant(app, users, db_register, db_records, db_user_profile):
    mock_activity = MagicMock(
        activity_login_user=users[0]["id"],
        activity_update_user=users[1]["id"],
        shared_user_id=-1,
        item_id=db_records[2][2].id,
    )
    activity_obj = WorkActivity()
    set_target_id, recid, actor_id, actor_name = activity_obj._get_params_for_registrant(mock_activity)
    assert set_target_id == {users[0]["id"]}
    assert recid == db_records[2][0]
    assert actor_id == users[1]["id"]
    assert actor_name == None

    mock_activity.shared_user_id = users[2]["id"]
    mock_activity.activity_update_user = users[2]["id"]
    set_target_id, recid, actor_id, actor_name = activity_obj._get_params_for_registrant(mock_activity)
    assert set_target_id == {users[0]["id"]}
    assert recid == db_records[2][0]
    assert actor_id == users[2]["id"]
    assert actor_name == db_user_profile.username


@pytest.fixture
def mock_create_item_registered(mocker):
    return mocker.patch.object(
        Notification, "create_item_registered",
        return_value=Notification()
    )


@pytest.fixture
def mock_send(mocker):
    return mocker.patch.object(Notification, "send")


@pytest.fixture
def mock_inbox_url(mocker):
    return mocker.patch(
        "weko_workflow.api.inbox_url",
        return_value="http://example.com/inbox"
    )


@pytest.fixture
def mock_logger(mocker):
    return mocker.patch("weko_workflow.api.current_app.logger")


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_success -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_success(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    expected_calls = [
        call(1, "123", 1, context_id=1, actor_name="actor_name", object_name="test"),
        call(2, "123", 1, context_id=1, actor_name="actor_name", object_name="test"),
    ]
    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    assert mock_create_item_registered.call_args_list == expected_calls
    assert mock_send.call_count == 2
    mock_logger.info.assert_called_once_with(
        "2 notification(s) sent for test_case: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_sql_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_sql_error(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    getter = MagicMock(side_effect=SQLAlchemyError)

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_logger.error.assert_called_once_with(
        "Failed to get notification parameters for activity: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_valid_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_valid_error(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    mock_create_item_registered.side_effect = ValidationError("Invalid data")

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )
    mock_logger.error.assert_called_once_with(
        "Failed to send notification for test_case: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_http_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_http_error(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    mock_send.side_effect = HTTPError("HTTP error occurred")

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_logger.error.assert_called_once_with(
        "Failed to send notification for test_case: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_exception(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = Activity(activity_id=1, title="test")
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))
    mock_create_item_registered.side_effect = Exception("Unexpected error")

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_logger.error.assert_called_once_with(
        "Unexpected error had occurred during sending notification for activity: 1"
    )


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity_wiht_case_invalid_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity_wiht_case_invalid_activity(
    app, mock_create_item_registered, mock_send, mock_inbox_url, mock_logger
):
    activity = MagicMock()
    recid = MagicMock(pid_value="123.4")
    getter = MagicMock(return_value=({1, 2}, recid, 1, "actor_name"))

    instance = WorkActivity()
    instance._notify_about_activity_wiht_case(
        activity, "test_case", getter, Notification.create_item_registered
    )

    mock_create_item_registered.assert_not_called()
    mock_send.assert_not_called()
    mock_logger.info.assert_not_called()
    mock_logger.error.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_get_params_for_approver -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_get_params_for_approver(app, users, db, db_register, mocker, db_records, db_user_profile):
    from invenio_communities.models import Community
    from weko_index_tree.models import Index

    index = Index(position=1, id=111)
    db.session.add(index)
    db.session.commit()
    comm = Community(id="test_com11", id_role=users[3]["id"],
                        id_user=users[3]["id"], title="test community",
                        description="this is test community",
                        root_node_id=index.id)
    db.session.add(comm)
    db.session.commit()
    flow_define = db_register["flow_define"]

    mock_activity1 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=users[1]["id"],
        item_id=db_records[2][2].id,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=flow_define,
        activity_community_id=None
    )
    mock_activity2 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=-1,
        item_id=db_records[2][2].id,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=flow_define,
        activity_community_id=None,
        action_order=3
    )
    mock_activity3 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=-1,
        item_id=db_records[2][2].id,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=flow_define,
        activity_community_id="test_com11"
    )
    activity = WorkActivity()
    set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity1)

    # self request
    set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity2)
    assert set_target_id == {users[1]["id"], users[6]["id"]}
    assert recid == db_records[2][0]
    assert actor_id == users[0]["id"]
    assert actor_name == None

    # with community admin
    with patch("weko_workflow.api.GetCommunity.get_community_by_id", return_value=MagicMock(id_role=4)):
        set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity3)
        assert set_target_id == {users[1]["id"], users[6]["id"], users[3]["id"]}

    # with action_user
    flow_action = FlowAction(status='N',
                    flow_id=flow_define.flow_id,
                    action_id=4,
                    action_version='1.0.0',
                    action_order=4,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={}
                    )
    db.session.add(flow_action)
    db.session.commit()
    flow_action_role = FlowActionRole(
        action_user = users[7]["id"],
        flow_action_id = flow_action.id,
        action_user_exclude = False)
    db.session.add(flow_action_role)
    db.session.commit()
    set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity2)
    assert set_target_id == {users[1]["id"], users[6]["id"], users[7]["id"]}

    # with action_user_exclude
    flow_action_role.action_role_exclude = True
    flow_action_role.action_role = 1
    flow_action_role.action_user_exclude = True
    flow_action_role.action_user = users[6]["id"]
    db.session.commit()
    set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity2)
    assert set_target_id == {users[1]["id"]}

    # invalid action_user type
    flow_action_role.action_user = 1.0
    for action in flow_define.flow_actions:
        action.action_role = flow_action_role
    mocker.patch("weko_workflow.api.Flow.get_flow_detail", return_value=flow_define)
    set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity2)
    assert set_target_id == {users[1]["id"], users[6]["id"]}

    # exception
    with mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", side_effect=SQLAlchemyError):
        with pytest.raises(SQLAlchemyError):
            set_target_id, recid, actor_id, actor_name = activity._get_params_for_approver(mock_activity1)



# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_registered -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_registered(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_item_registered_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_registrant',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_registered(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file)
    data_callback = kwargs.get('data_callback')
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_registered(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_request_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_request_approval(app, users, db, db_register, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_request_approval_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_approver',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_request_approval(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file)
    data_callback = kwargs.get('data_callback')
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_request_approval(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_approved(app, users, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_item_approved_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_registrant',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_approved(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_approved(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_rejected -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_rejected(app, users, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_rejected_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_rejected(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_rejected(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_deleted -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_deleted(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_deleted_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_deleted(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_deleted(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_request_delete_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_request_delete_approval(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_delete_request_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_approver",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_request_delete_approval(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_request_delete_approval(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_delete_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_delete_approved(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_delete_approved_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_delete_approved(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_delete_approved(activity)
    assert res is None


def test_workactivity_send_mail_item_delete_rejected(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_delete_rejected_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_delete_rejected(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_delete_rejected(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_send_notification_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_notification_email(app, mocker):
    mock_activity = MagicMock(activity_id="123")
    mock_target = MagicMock(id=1, email="test@example.com", confirmed_at=True)
    mock_settings = {1: MagicMock(subscribe_email=True)}
    mock_profiles = {1: MagicMock(language="en")}
    mock_template = "email_template_{language}.tpl"
    mock_data_callback = MagicMock(return_value={"subject": "Test Subject", "body": "Test Body"})

    mock_load_template = mocker.patch("weko_workflow.utils.load_template", return_value="template_content")
    mock_fill_template = mocker.patch("weko_workflow.utils.fill_template", return_value={"subject": "Test Subject", "body": "Test Body"})
    mock_send_mail = mocker.patch("weko_workflow.utils.send_mail")

    activity = WorkActivity()
    activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)

    mock_load_template.assert_called_once_with(mock_template, "en")
    mock_fill_template.assert_called_once_with("template_content", mock_data_callback.return_value)
    mock_send_mail.assert_called_once_with("Test Subject", "test@example.com", "Test Body")

    mock_settings_false = {1: MagicMock(subscribe_email=False)}
    mock_send_mail.reset_mock()
    activity.send_notification_email(mock_activity, [mock_target], mock_settings_false, mock_profiles, mock_template, mock_data_callback)
    mock_send_mail.assert_not_called()

    mock_target_false = MagicMock(id=1, email="test@example.com", confirmed_at=False)
    mock_send_mail.reset_mock()
    activity.send_notification_email(mock_activity, [mock_target_false], mock_settings, mock_profiles, mock_template, mock_data_callback)
    mock_send_mail.assert_not_called()

    mock_send_mail.reset_mock()
    mock_send_mail.return_value = False
    res = activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)
    assert res == 0

    mock_logger = mocker.patch("weko_workflow.api.current_app.logger.error")
    mock_fill_template = mocker.patch("weko_workflow.utils.fill_template", side_effect=Exception("Template error"))
    activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)
    mock_logger.assert_called_once()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_create_notification_context_with_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_notification_context_with_recid(app, mocker):
    activity = MagicMock(
        updated=datetime.strptime("2025/03/28 12:00:00","%Y/%m/%d %H:%M:%S"),
        title="Test Activity", activity_id="123"
    )
    target = MagicMock(email="test@example.com")
    profile = MagicMock(timezone="Asia/Tokyo", username="test_user")
    actor_name = "actor_name"
    recid = MagicMock(pid_value="1234567890")

    activity_obj = WorkActivity()
    with app.test_request_context(base_url='http://example.org/'):
        context = activity_obj._create_notification_context(activity, target, profile, actor_name, recid)
        assert context.get("recipient_name") == profile.username
        assert context.get("actor_name") == actor_name
        assert context.get("target_title") == activity.title
        assert context.get("target_url") == "http://example.org/records/1234567890"
        assert context.get("event_date") == "2025-03-28 21:00:00"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_create_notification_context_without_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test__create_notification_context_without_recid(app, mocker):
    activity = MagicMock(
        updated=datetime.strptime("2025/03/28 12:00:00","%Y/%m/%d %H:%M:%S"),
        title="Test Activity", activity_id="123"
    )
    target = MagicMock(email="test@example.com")
    profile = MagicMock(timezone="Asia/Tokyo", username="test_user")
    actor_name = "actor_name"

    activity_obj = WorkActivity()
    with app.test_request_context(base_url='http://example.org/'):
        context = activity_obj._create_notification_context(activity, target, profile, actor_name)
        assert context.get("recipient_name") == profile.username
        assert context.get("actor_name") == actor_name
        assert context.get("target_title") == activity.title
        assert context.get("target_url") == "http://example.org/workflow/activity/detail/123"
        assert context.get("event_date") == "2025-03-28 21:00:00"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test__get_settings_for_targets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test__get_settings_for_targets(app, users, db_user_profile, db_notification_user_settings):
    set_target_id = {users[2]["id"]}
    activity_obj = WorkActivity()
    targets, settings, profiles, actor = activity_obj._get_settings_for_targets(set_target_id)
    assert targets == [users[2]["obj"]]
    assert settings.get(users[2]["id"]) == db_notification_user_settings
    assert profiles.get(users[2]["id"]) == db_user_profile
    assert actor == None

    actor_id = users[2]["id"]
    targets, settings, profiles, actor = activity_obj._get_settings_for_targets(set_target_id, actor_id)
    assert targets == [users[2]["obj"]]
    assert settings.get(users[2]["id"]) == db_notification_user_settings
    assert profiles.get(users[2]["id"]) == db_user_profile
    assert actor == users[2]["obj"]


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_non_extract_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_non_extract_files(app, mocker):
    activity = WorkActivity()

    # Mock the `get_activity_metadata` method
    mocker.patch.object(activity, 'get_activity_metadata', return_value=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": True},
            {"filename": "file2.txt", "non_extract": False},
            {"filename": "file3.txt", "non_extract": True}
        ]
    }))

    # metadata is available
    result = activity.get_non_extract_files(activity_id=1)
    assert result == ["file1.txt", "file3.txt"]

    # metadata is None
    mocker.patch.object(activity, 'get_activity_metadata', return_value=None)
    result = activity.get_non_extract_files(activity_id=1)
    assert result is None

    # no files have "non_extract" set to True
    mocker.patch.object(activity, 'get_activity_metadata', return_value=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": False},
            {"filename": "file2.txt", "non_extract": False}
        ]
    }))
    result = activity.get_non_extract_files(activity_id=1)
    assert result == []

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_UpdateItem_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_UpdateItem_publish(app, db_records):
    updated_item = UpdateItem()
    dep = db_records[0][6]
    updated_item.publish(dep, PublishStatus.PRIVATE.value)
    assert dep.get('publish_status') == PublishStatus.PRIVATE.value
    updated_item.publish(dep, PublishStatus.PUBLIC.value)
    assert dep.get('publish_status') == PublishStatus.PUBLIC.value

# def query_activities_by_tab_is_wait(query)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_wait -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_wait(users, db):
    current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = False
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email,
                _WorkFlow.flows_name,
                _Action.action_name,
                Role.name
            ).outerjoin(_Flow).outerjoin(
                _WorkFlow,
                and_(_Activity.workflow_id == _WorkFlow.id,)
            ).outerjoin(_Action).outerjoin(_FlowAction).outerjoin(_FlowActionRole).outerjoin(
                ActivityAction,
                and_(
                    ActivityAction.activity_id == _Activity.activity_id,
                    ActivityAction.action_id == _Activity.action_id,
                )
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                    _Activity.shared_user_ids == [],
                )
                )
        expected = "AND (workflow_activity.activity_login_user = ? OR (workflow_activity.shared_user_ids LIKE '%' + ? || '%')) AND (workflow_flow_action_role.action_user != ? AND workflow_flow_action_role.action_user_exclude = ? AND (workflow_activity.shared_user_ids NOT LIKE '%' + ? || '%') OR workflow_flow_action_role.action_role NOT IN (?) AND workflow_flow_action_role.action_role_exclude = ? AND (workflow_activity.shared_user_ids NOT LIKE '%' + ? || '%') OR workflow_activity_action.action_handler != ? AND (workflow_activity.shared_user_ids NOT LIKE '%' + ? || '%') OR (workflow_activity.shared_user_ids LIKE '%' + ? || '%') AND workflow_flow_action_role.action_user != workflow_activity.activity_login_user AND workflow_flow_action_role.action_user_exclude = ? OR (workflow_activity.shared_user_ids LIKE '%' + ? || '%') AND workflow_activity_action.action_handler != workflow_activity.activity_login_user)"  
        ret = WorkActivity.query_activities_by_tab_is_wait(query)
        assert str(ret).find(expected)
    
    current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = True
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email,
                _WorkFlow.flows_name,
                _Action.action_name,
                Role.name
            ).outerjoin(_Flow).outerjoin(
                _WorkFlow,
                and_(_Activity.workflow_id == _WorkFlow.id,)
            ).outerjoin(_Action).outerjoin(_FlowAction).outerjoin(_FlowActionRole).outerjoin(
                ActivityAction,
                and_(
                    ActivityAction.activity_id == _Activity.activity_id,
                    ActivityAction.action_id == _Activity.action_id,
                )
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                    _Activity.shared_user_ids == [],
                )
                )
        expected = "AND (workflow_activity.activity_login_user = ?) AND ((workflow_flow_action_role.action_user != ? AND workflow_flow_action_role.action_user_exclude = '0') OR (workflow_flow_action_role.action_role NOT IN (?) AND workflow_flow_action_role.action_role_exclude = '0') OR (workflow_activity_action.action_handler != ? ))"
        ret = WorkActivity.query_activities_by_tab_is_wait(query)
        assert str(ret).find(expected)
    
# def query_activities_by_tab_is_all(query, is_community_admin, community_user_ids)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_all(users, db):
    is_community_admin=False
    community_user_ids=[]
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                )
            )
        
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%') AND workflow_flow_action.action_id != ?"
        ret = WorkActivity.query_activities_by_tab_is_all(query, is_community_admin, community_user_ids)
        assert str(ret).find(expected)
        
        is_community_admin = True
        community_user_ids = [3]
        expected = "(workflow_activity.activity_update_user LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_all(query, is_community_admin, community_user_ids)
        assert str(ret).find(expected)

# def query_activities_by_tab_is_todo(query, is_admin)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_todo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_todo(users, db):
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                _FlowActionRole
            )
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_todo(query, False)
        assert str(ret).find(expected)

        current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = True
        expected = "(workflow_activity.action_handler LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_todo(query, True)
        assert str(ret).find(expected)

        current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = False
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_todo(query, True)
        assert str(ret).find(expected)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_action_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_id, action_order, expected_index, expected_included', [
    (4, 6, 'deny', True),
    (5, 4, 'allow', True),
    (7, 5, 'deny', False),
    (6, 3, 'allow', False),
])
def test_WorkActivity_get_activity_action_role(app, activity_with_roles, action_id, action_order, expected_index, expected_included):
    activity = activity_with_roles["activity"]
    item_metadata = activity_with_roles['itemMetadata']
    owner_id = int(item_metadata['owner'])

    workflow_activity = WorkActivity()
    _, users = workflow_activity.get_activity_action_role(str(activity.id), action_id, action_order)
    print(users)
    assert (owner_id in users[expected_index]) == expected_included

# for roles
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_action_role2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_id, action_order, expected_index, expected_included', [
    (6, 3, 'allow', True),
    (5, 4, 'deny', True),
])
def test_WorkActivity_get_activity_action_role2(app, activity_with_roles_for_request_mail, action_id, action_order, expected_index, expected_included):
    activity = activity_with_roles_for_request_mail["activity"]
    item_metadata = activity_with_roles_for_request_mail['itemMetadata']
    owner_id = int(item_metadata['owner'])

    workflow_activity = WorkActivity()
    roles, _ = workflow_activity.get_activity_action_role(str(activity.id), action_id, action_order)
    assert (owner_id in roles[expected_index]) == expected_included

# for request_mail
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_action_role3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_id, action_order, expected_index, expected_included', [
    (7, 5, 'allow', True),
    (4, 6, 'deny', True),
    (3, 2, 'allow', True)
])
def test_WorkActivity_get_activity_action_role3(app, activity_with_roles_for_request_mail, action_id, action_order, expected_index, expected_included):
    activity = activity_with_roles_for_request_mail["activity"]
    item_metadata = activity_with_roles_for_request_mail['itemMetadata']
    owner_id = int(item_metadata['owner'])

    workflow_activity = WorkActivity()
    _, users = workflow_activity.get_activity_action_role(str(activity.id), action_id, action_order)
    assert (owner_id in users[expected_index]) == expected_included

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_query_activities_by_tab_is_todo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('action_item_registrant, users_idx, expected_activity_included', [
    (True, 0, True),
    (True, 4, False),
    (False, 0, False),
    (False, 4, False),
])
def test_WorkActivity_query_activities_by_tab_is_todo(app, workflow, db, users, item_type, action_item_registrant, users_idx, expected_activity_included):
    with app.test_request_context():
        login_user(users[users_idx]["obj"])

        # flow action role
        flow_actions = workflow['flow_action']
        flow_action_roles = [
            FlowActionRole(id = 4,
                        flow_action_id = flow_actions[5].id,
                        action_user_exclude = False,
                        action_item_registrant = action_item_registrant),
        ]
        with db.session.begin_nested():
            db.session.add_all(flow_action_roles)
        db.session.commit()

        # item_metadata
        item_metdata = ItemsMetadata.create(
            data = {
                "id": "1",
                "pid": {
                    "type": "depid",
                    "value": "1",
                    "revision_id": 0
                },
                "lang": "ja",
                "owner": str(users[0]["obj"].id),
                "title": "sample01",
                "owners": [
                    users[0]["obj"].id
                ],
                "status": "published",
                "$schema": "/items/jsonschema/" + str(item_type[0].get("id")),
                "pubdate": "2020-08-29",
                "created_by": users[0]["obj"].id,
                "owners_ext": {
                    "email": "sample@nii.ac.jp",
                    "username": "sample",
                    "displayname": "sample"
                },
                "shared_user_ids": [],
                "item_1617186331708": [
                    {
                    "subitem_1551255647225": "sample01",
                    "subitem_1551255648112": "ja"
                    }
                ],
                "item_1617258105262": {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper"
                }
            },
            item_type_id = item_type[0].get("id"),
        )

        # set activity
        activity = Activity(
            activity_id='1', workflow_id=workflow["workflow"].id,
            flow_id=workflow["flow"].id,
            action_id=4,
            activity_login_user=users[0]['obj'].id,
            activity_status=ActionStatusPolicy.ACTION_BEGIN,
            activity_update_user=1,
            activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
            activity_community_id=3,
            activity_confirm_term_of_use=True,
            title='test', shared_user_ids=[], extra_info={},
            action_order=6, item_id=item_metdata.model.id,
        )
        with db.session.begin_nested():
            db.session.add(activity)
        db.session.commit()

        activity_action = ActivityAction(activity_id=activity.activity_id,
                                        action_id=4,action_status="M",
                                        action_handler=1, action_order=6)

        with db.session.begin_nested():
            db.session.add(activity_action)
        db.session.commit()

        actual_query = WorkActivity.query_activities_by_tab_is_todo(
            Activity.query, False)
        actual = actual_query.all()

        assert (len(actual) > 0) == expected_activity_included


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_query_activities_by_tab_is_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_idx, expected_included', [
    (0, True),
    (4, False),
])
def test_WorkActivity_query_activities_by_tab_is_all(app, users, activity_with_roles, users_idx, expected_included):
    with app.test_request_context():
        login_user(users[users_idx]["obj"])

        actual_query = WorkActivity.query_activities_by_tab_is_all(
            Activity.query, False, [])
        actual = actual_query.all()
        assert (len(actual) > 0) == expected_included

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_request_mail_list_create_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_request_mail_list_create_and_update(app, workflow, db, mocker):
    activity = WorkActivity()
    _request_maillist1 = []
    _request_maillist2 = [{"email": "test@example.com", "author_id": ""}]
    activity.create_or_update_activity_request_mail("1", _request_maillist1, True)
    assert activity.get_activity_request_mail("1")
    activity.create_or_update_activity_request_mail("1", _request_maillist2, True)
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2
    activity.create_or_update_activity_request_mail("1111111", _request_maillist1, "aaa")
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2

# def get_user_ids_of_request_mails_by_activity_id
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_user_ids_of_request_mails_by_activity_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_user_ids_of_request_mails_by_activity_id(workflow, users, mocker):
    activity = WorkActivity()
    activityrequestmails = [
        ActivityRequestMail(
        id = 1,
        activity_id = 1,
        display_request_button = True,
        request_maillist = []
    ),
        ActivityRequestMail(
            id = 2,
            activity_id = 2,
            display_request_button = False,
            request_maillist = [{}]
    ),
        ActivityRequestMail(
            id = 3,
            activity_id = 3,
            display_request_button = True,
            request_maillist = [{"email":"not_user","author_id":""},
                                {"email":"user@test.org","author_id":""},
                                {"email":"contributor@test.org","author_id":""}]
    )]
    with patch("weko_workflow.api.WorkActivity.get_activity_detail", return_value = _Activity(extra_info={"record_id":1, "is_restricted_access":True})):
        mock = mocker.patch("weko_workflow.api.WorkActivity.get_user_ids_of_request_mails_by_record_id")
        activity.get_user_ids_of_request_mails_by_activity_id(1)
        mock.assert_called()
    mocker.patch("weko_workflow.api.WorkActivity.get_activity_detail", return_value = _Activity(extra_info={}))
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = None):
        assert activity.get_user_ids_of_request_mails_by_activity_id(1) == []
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = activityrequestmails[0]):
        assert activity.get_user_ids_of_request_mails_by_activity_id(1) == []
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = activityrequestmails[1]):
        assert activity.get_user_ids_of_request_mails_by_activity_id(2) == []
    with patch("weko_workflow.api.WorkActivity.get_activity_request_mail", return_value = activityrequestmails[2]):
        ids = activity.get_user_ids_of_request_mails_by_activity_id(3)
        assert ids == [User.query.filter_by(email="contributor@test.org").one_or_none().id]

# def get_user_ids_of_request_mails_by_record_id
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_user_ids_of_request_mails_by_record_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_user_ids_of_request_mails_by_record_id(workflow, users, mocker):
    activity = WorkActivity()
    requestmails = [[],[{}],[{"email":"not_user","author_id":""},
                                {"email":"user@test.org","author_id":""},
                                {"email":"contributor@test.org","author_id":""}]]
    mocker.patch("weko_workflow.api.PersistentIdentifier.get")
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_assigned_object")
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=None):
        assert not activity.get_user_ids_of_request_mails_by_record_id(0)
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=requestmails[0]):
        assert not activity.get_user_ids_of_request_mails_by_record_id(0)
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=requestmails[1]):
        assert not activity.get_user_ids_of_request_mails_by_record_id(0)
    with patch("weko_workflow.api.RequestMailList.get_mail_list_by_item_id", return_value=requestmails[2]):
        ids = activity.get_user_ids_of_request_mails_by_record_id(0)
        assert ids == [User.query.filter_by(email="contributor@test.org").one_or_none().id]
    


# def check_user_role_for_mail
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_check_user_role_for_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_user_role_for_mail(users):
    activity = WorkActivity()
    # user is admin
    roles={'allow':[5],'deny':[]}
    assert activity.check_user_role_for_mail(users[2]["id"], roles)

    # user is cont, cont in allow 
    roles={'allow':[3],'deny':[]}
    assert activity.check_user_role_for_mail(users[0]["id"], roles)

    # user is cont, cont not in allow
    roles={'allow':[2],'deny':[]}
    assert not activity.check_user_role_for_mail(users[0]["id"], roles)

    # user is cont, cont in deny
    roles={'allow':[],'deny':[3]}
    assert not activity.check_user_role_for_mail(users[0]["id"], roles)

    # user is cont, cont not in deny
    roles={'allow':[],'deny':[2]}
    assert activity.check_user_role_for_mail(users[0]["id"], roles)
                             
# def get_recirds_for_request_mail_by_mailaddress
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_recirds_for_request_mail_by_mailaddress -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_recirds_for_request_mail_by_mailaddress(db,mocker):
    activity = WorkActivity()
    request_mail_list=[
        _RequestMailList(item_id="1234",mail_list=[{"email": "wekosoftware@nii.ac.jp", "author_id": ""}]),
        _RequestMailList(item_id="1235",mail_list=[{"email": "wekosoftware@nii.ac.jp", "author_id": ""}])
    ]
    mocker.patch("weko_workflow.api.RequestMailList.get_request_mail_by_mailaddress",return_value = request_mail_list)
    
    with patch("weko_workflow.api.PersistentIdentifier.get_by_object", return_value = PersistentIdentifier(pid_value = 1)):
        recids_list = activity.get_recids_for_request_mail_by_mailaddress("wekosoftware@nii.ac.jp")
        assert recids_list
    assert not activity.get_recids_for_request_mail_by_mailaddress("wekosoftware@nii.ac.jp")

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_item_application_create_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_item_application_create_and_update(app, workflow, db, mocker):
    activity = WorkActivity()
    _item_application1 = {}
    _item_application2 = {"workflow":"1", "terms":"term_free", "termsDescription":"test"}

    # create
    activity.create_or_update_activity_item_application("1", _item_application1, True)
    assert activity.get_activity_item_application("1")

    # update
    activity.create_or_update_activity_item_application("1", _item_application2, True)
    assert activity.get_activity_item_application("1").item_application == _item_application2

    # error
    activity.create_or_update_activity_item_application("1111111", _item_application1, "aaaaa")
    assert activity.get_activity_item_application("1").item_application == _item_application2

    # not hit search
    assert not activity.get_activity_item_application("1111")
