from flask_login.utils import login_user, logout_user
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
from mock import patch
import math

from invenio_records.models import RecordMetadata
from invenio_accounts.models import User
from weko_workflow.api import Flow, WorkActivity, UpdateItem
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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_UpdateItem_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_UpdateItem_publish(app, db_records):
    updated_item = UpdateItem()
    dep = db_records[0][6]
    updated_item.publish(dep, PublishStatus.PRIVATE.value)
    assert dep.get('publish_status') == PublishStatus.PRIVATE.value
    updated_item.publish(dep, PublishStatus.PUBLIC.value)
    assert dep.get('publish_status') == PublishStatus.PUBLIC.value
