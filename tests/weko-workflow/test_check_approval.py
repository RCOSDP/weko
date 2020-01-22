from mock import mock
import pytest
from helpers import login_user_via_session, insert_user_to_db
from weko_workflow.views import check_approval


def test_approval(app, database, client):
    insert_user_to_db(database)
    insert_test_data(database)
    login_user_via_session(client, 1)
    #check error case

    # chặn console lỗi :
    # with pytest.raises(Exception) as ex:
    #     client.get('/workflow/check_approval/A-20200108-00101')

    res = client.get('/workflow/check_approval/A-20200108-00101')
    #check end usage case
    res = client.get('/workflow/check_approval/A-20200108-00102')
    #check continue usage case
    res = client.get('/workflow/check_approval/A-20200108-00100')
    #check turn off config case
    with app.app_context():
        app.config['WEKO_WORKFLOW_CONTINUE_APPROVAL']=False
        res = client.get('/workflow/check_approval/A-20200108-00100')
    assert 1 == 1

def insert_test_data(database):
    from weko_records.models import ItemTypeName
    from weko_records.models import ItemType
    from weko_workflow.models import FlowDefine, WorkFlow
    from weko_index_tree.models import Index
    from weko_workflow.models import Activity
    from invenio_records.models import RecordMetadata

    item_name = ItemTypeName(id=10,name="ItemName",has_site_license=True,is_active=True)
    item_type = ItemType(id=10, name_id=10, harvesting_type=False, schema={}, form={}, render={}, tag=1 ,version_id=1 , is_deleted=False)
    flow = FlowDefine(id = 10,flow_id="b9eb6124-2bd1-4422-96d2-2d424105fb3e",flow_name="Flow",flow_user=1,flow_status="A")
    index = Index(id=10,parent=0 ,position=0 ,index_name="Index" ,index_name_english="English" ,index_link_name_english="English")
    workflow = WorkFlow(id = 10,flows_id="b9eb6124-2bd1-4422-96d2-2d424105fb3e",flows_name="Usage Report",itemtype_id=10,flow_id=10,index_tree_id=10)
    activity = Activity(id=10, activity_id="A-20200108-00100", item_id="f7ab31d0-f401-4e60-adc9-000000000041", workflow_id=10, flow_id=10,activity_start="2020-01-08 09:14:14")
    activity2 = Activity(id=20, activity_id="A-20200108-00102", item_id="f7ab31d0-f401-4e60-adc9-000000000042", workflow_id=10, flow_id=10,activity_start="2020-01-08 09:14:14")
    jsondata = {"item_1575270782459": {"attribute_name": "Stop/Continue","attribute_value_mlt": [{ "subitem_stop/continue": "Continue" } ]}}
    recordMetadata = RecordMetadata(id="f7ab31d0-f401-4e60-adc9-000000000041", json =jsondata, version_id =1)
    recordMetadata2 = RecordMetadata(id="f7ab31d0-f401-4e60-adc9-000000000042", json ={}, version_id =1)

    database.session.add(item_name)
    database.session.add(item_type)
    database.session.add(flow)
    database.session.add(index)
    database.session.add(workflow) 
    database.session.add(activity) 
    database.session.add(activity2) 
    database.session.add(recordMetadata) 
    database.session.add(recordMetadata2) 
    database.session.commit()