# .tox/c1/bin/pytest --cov=weko_workflow tests/test_sessions.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
from weko_workflow.sessions import upt_activity_item

#def upt_activity_item(app, user_id, item_id, item_title):
def test_upt_activity_item(app,client,users,db_records):
    user = users[1]['obj']
    item = db_records[0][1]
    with app.test_request_context():
        with client.session_transaction() as session:
             upt_activity_item(app,user,item,"","TEST")
             
             session['activity_info'] =  {'activity_id': 'A-20220818-00001', 'action_id': 3, 'action_version': '1.0.1', 'action_status': 'M', 'commond': ''}
             upt_activity_item(app,user,item,"")
             
         