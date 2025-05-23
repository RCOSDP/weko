from datetime import datetime
import pytest

from mock import Mock, patch
import math
import pytest
from flask import current_app, session
from flask_login.utils import login_user
from invenio_accounts.models import Role, User
from sqlalchemy import and_, or_, not_
from weko_records.api import ItemsMetadata

from invenio_records.models import RecordMetadata
from weko_workflow.api import Flow, WorkActivity, UpdateItem
from weko_workflow.models import Action as _Action
from weko_workflow.models import Activity as _Activity
from weko_workflow.models import ActivityAction
from weko_workflow.models import FlowAction as _FlowAction
from weko_workflow.models import FlowActionRole as _FlowActionRole
from weko_workflow.models import FlowDefine as _Flow
from weko_workflow.models import WorkFlow as _WorkFlow
from weko_workflow.models import ActionStatusPolicy, Activity, ActivityAction, FlowActionRole
from weko_schema_ui.models import PublishStatus

class TestFlow:
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestFlow::test_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_action(self,app, client, users, db, action_data):
        with app.test_request_context():
            login_user(users[2]["obj"])
            _flow = Flow()
            flow = _flow.create_flow({'flow_name': 'create_flow_test'})
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

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('conditions', conditions)
    def test_get_activity_list(self, app, users, db_register_activity, conditions):
        # test preparation
        activity = WorkActivity()

        # contributor
        with app.test_request_context():
            login_user(users[0]['obj'])
            activities, max_page, size, page, name_param, count = \
                activity.get_activity_list(None, conditions, False)
            
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
                activity.get_activity_list(None, conditions, False)

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
    def test_get_all_activity_list(self,app, client, users, db_register_full_action):
        with app.test_request_context():
            login_user(users[2]["obj"])
            activity = WorkActivity()
            activities = activity.get_all_activity_list()
            assert len(activities) == 13


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_activity_index_search(self,app, db_register_full_action):
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
    def test_upt_activity_detail(self,app, db_register_full_action, db_records):
        activity = WorkActivity()
        db_activity = activity.upt_activity_detail(db_records[2][2].id)
        assert db_activity == None


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_corresponding_usage_activities(self,app, db_register_full_action):
        activity = WorkActivity()
        usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
        assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
        assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::TestWorkActivity::test_check_community_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_check_community_permission(self,app,db_register_full_action):
        activity = WorkActivity()
        activities = db_register_full_action["activities"]
        not_itemid_act = activities[1]
        # not exist activity.item_id
        result = WorkActivity._check_community_permission(not_itemid_act, ["1"])

        assert result == True

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
    def test_get_activity_list(client, activity_acl, activity_acl_users):
        # {user_id:{tab:[activity_id,...],...}}
        result = {
            1:{# sysadmin
                "todo":[43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 28, 27, 26, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 7, 6, 5, 2, 1], 
                "wait":[5,2], 
                "all":[43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
            },
            3:{# test_role01_user
                "todo":[42, 38, 37, 34, 33, 32, 31, 27, 22, 21, 19, 18, 16, 14, 5], 
                "wait":[41, 40, 39, 36, 35, 28, 26, 23, 17], 
                "all":[42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 19, 18, 17, 16, 14, 5]
            },
            4:{# test_role01_comadmin
                "todo":[42, 41, 40, 38, 34, 32, 26, 23, 22, 18, 16, 14, 12, 11, 10, 7, 6, 5], 
                "wait":[39, 21, 20, 19, 17, 15, 13], 
                "all":[42, 41, 40, 39, 38, 34, 32, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5]
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
                        activities, max_page, size, page, name_param = activity.get_activity_list(conditions=conditions)
                        assert [ac.id for ac in activities] == acts[res_size*(res_page-1):res_size*res_page]
                        assert max_page == num_page
                        assert size == str(res_size)
                        assert page == str(res_page)
                
                num_page = math.ceil(len(acts)/20)
                conditions = {"tab":[tab]}
                # is_get_all = True
                activities, max_page, size, page, name_param = activity.get_activity_list(conditions=conditions,is_get_all=True)
                assert [ac.id for ac in activities] == acts
                assert max_page == num_page
                assert size == '20'
                assert page == '1'

                # activitylog = True
                activities, max_page, size, page, name_param = activity.get_activity_list(conditions=conditions,activitylog=True)
                assert [ac.id for ac in activities] == acts
                assert max_page == math.ceil(len(acts)/100000)
                assert size == 100000
                assert page == 1
        
        # count = 0
        user = User.query.filter_by(id=7).one()
        login_user(user)
        conditions={"tab":["todo"]}
        activities, max_page, size, page, name_param = activity.get_activity_list(conditions=conditions)
        assert activities == []
        assert max_page == 0
        assert size == '20'
        assert page == '1'
        assert 1==2

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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_activity_index_search(app, db_register_full_action):
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
def test_WorkActivity_upt_activity_detail(app, db_register_full_action, db_records):
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
def test_WorkActivity_get_corresponding_usage_activities(app, db_register_full_action):
    activity = WorkActivity()
    usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
    assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
    assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

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
        ret = WorkActivity.query_activities_by_tab_is_wait(query, True, [1])
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
        ret = WorkActivity.query_activities_by_tab_is_wait(query, False, [])
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
                "$schema": "/items/jsonschema/" + str(item_type.id),
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
            item_type_id = item_type.id,
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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_UpdateItem_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_UpdateItem_publish(app, db_records):
    updated_item = UpdateItem()
    dep = db_records[0][6]
    updated_item.publish(dep, PublishStatus.PRIVATE.value)
    assert dep.get('publish_status') == PublishStatus.PRIVATE.value
    updated_item.publish(dep, PublishStatus.PUBLIC.value)
    assert dep.get('publish_status') == PublishStatus.PUBLIC.value
