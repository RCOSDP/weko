from pytest_invenio.fixtures import database, app, es_clear
from mock import mock, patch
from weko_workflow.models import WorkFlow,Action
from weko_records.api import ItemsMetadata
from helpers import login_user_via_session, insert_user_to_db


def insert_data_for_activity(database):
    from weko_workflow.models import ActivityAction,ActionStatus
    from helpers import insert_activity, insert_flow, insert_record_metadata, insert_workflow, insert_action_to_db, \
        insert_flow_action, insert_item_type_name, insert_item_type, insert_activity_action
    #####Usage Application
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d647"
    item_id = "f7ab31d0-f401-4e60-adc9-000000000111"
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location', 'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19', 'title': 'username'}}
    insert_record_metadata(database,item_id,record)
    insert_flow(database,1,flow_id,"Usage Application",1,"A")
    insert_item_type_name(database,"地点情報利用申請",True,True)
    insert_item_type(database,1,{},{},{},1,1,True)
    insert_action_to_db(database)
    #Insert a flow contain 5 steps
    insert_flow_action(database,flow_id,1,1)
    insert_flow_action(database,flow_id,2,5)
    insert_flow_action(database,flow_id,8,2)
    insert_flow_action(database,flow_id,9,3)
    insert_flow_action(database,flow_id,11,4)
    
    insert_workflow(database,1,flow_id,"Usage Application",1,1,1)
    insert_activity(database,"A-20200108-00100",item_id,1,1,8)
    action_status = ActionStatus(action_status_id="A",action_status_name="Name")
    database.session.add(action_status)
    database.session.commit()
    insert_activity_action(database,"A-20200108-00100",8,2)

    #####Output Registration
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d648"
    item_id = "f7ab31d0-f401-4e60-adc9-000000000112"
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location', 'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19', 'title': 'username'}}
    insert_record_metadata(database,item_id,record)
    insert_flow(database,2,flow_id,"Output Registration",1,"A")
    insert_item_type_name(database,"成果物登録",True,True)
    insert_item_type(database,2,{},{},{},2,2,True)
    #Insert a flow contain 5 steps
    insert_flow_action(database,flow_id,1,1)
    insert_flow_action(database,flow_id,2,5)
    insert_flow_action(database,flow_id,8,2)
    insert_flow_action(database,flow_id,9,3)
    insert_flow_action(database,flow_id,11,4)
    
    insert_workflow(database,2,flow_id,"Output Registration",2,2,1)
    insert_activity(database,"A-20200108-00101",item_id,2,2,8)
    database.session.add(action_status)
    database.session.commit()
    insert_activity_action(database,"A-20200108-00101",8,2)


    ####Usage Report
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d649"
    item_id = "f7ab31d0-f401-4e60-adc9-000000000116"
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location', 'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19', 'title': 'username'}}
    insert_record_metadata(database,item_id,record)
    insert_flow(database,3,flow_id,"Usage Report",1,"A")
    insert_item_type_name(database,"利用報告",True,True)
    insert_item_type(database,3,{},{},{},3,3,True)
    insert_flow_action(database,flow_id,1,1)
    insert_flow_action(database,flow_id,2,5)
    insert_flow_action(database,flow_id,8,2)
    insert_flow_action(database,flow_id,9,3)
    insert_flow_action(database,flow_id,11,4)
    
    insert_workflow(database,3,flow_id,"Usage Report",3,3,1)
    insert_activity(database,"A-20200108-00102",item_id,3,3,8)
    database.session.add(action_status)
    database.session.commit()
    insert_activity_action(database,"A-20200108-00102",8,2)

def test_auto_fill_title(app, database, client,es_clear):
    #login before making request
    insert_user_to_db(database)
    login_user_via_session(client, 1)
    insert_data_for_activity(database)
    steps = 'weko_workflow/term_and_condition.html', 'need_file', 'record', 'json_schema', 'schema_form', 'item_save_uri', 'files', 'endpoints', 'need_thumbnail', 'files_thumbnail','allow_multi_thumbnail'
    with mock.patch('weko_workflow.views.item_login', return_value=steps):
        res1 = client.get('/workflow/activity/detail/A-20200108-00100?status=ToDo?itemtitle=titletest')
        assert res1.status_code == 200
        res1 = client.get('/workflow/activity/detail/A-20200108-00101?status=ToDo?itemtitle=titletest')
        assert res1.status_code == 200
        res1 = client.get('/workflow/activity/detail/A-20200108-00102?status=ToDo?itemtitle=titletest')
        assert res1.status_code == 200