# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp


from unittest.mock import MagicMock
import pytest
from mock import patch
from flask import Flask, json, jsonify, url_for, session, make_response
from invenio_accounts.testutils import login_user_via_session as login

from weko_workflow.admin import FlowSettingView,WorkFlowSettingView

# class FlowSettingView(BaseView):
class TestFlowSettingView:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_index_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
#     def index(self):
    def test_index_acl_guest(self,client,db_register2):
        url = url_for('flowsetting.index',_external=True)
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403),
        # (1, 200),
        # (2, 200),
        # (3, 200),
        # (4, 200),
        # (5, 200),
        # (6, 200),
    ])
    def test_index_acl(self,client,db_register2,users,users_index,status_code):
        login(client=client, email=users[users_index]['email'])
        url = url_for('flowsetting.index',_external=True)
        res =  client.get(url)
        assert res.status_code == status_code  

#     def flow_detail(self, flow_id='0'):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_flow_detail_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_flow_detail_acl_guest(self,client,db_register2):
        url = url_for('flowsetting.index',flow_id=str(1),_external=True)
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_flow_detail_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        # (0, 403),
        (1, 200),
        # (2, 200),
        # (3, 200),
        # (4, 200),
        # (5, 200),
        # (6, 200),
    ])
    def test_flow_detail_acl(self,client,workflow,db_register2,users,users_index,status_code):
        flow_define = workflow['flow']
        login(client=client, email=users[users_index]['email'])
        url = '/admin/workflowsetting/{}'.format(0)
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
        
        
        url = '/admin/workflowsetting/{}'.format(flow_define.flow_id)
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code  
    
#     def get_specified_properties():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_get_specified_properties -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_specified_properties(self,app,item_type):
        with app.test_request_context():
            assert FlowSettingView.get_specified_properties()==[{'value': 'parentkey.subitem_restricted_access_guarantor_mail_address', 'text': 'Guarantor'}]
        
#     def update_flow(flow_id):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_update_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_update_flow(self,app,workflow):
        with app.test_request_context():
            assert FlowSettingView.update_flow(0)==""

#     def new_flow(self, flow_id='0'):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_new_flow(self,app,workflow):
        with app.test_request_context():
            assert FlowSettingView.new_flow(0)==""

#     def del_flow(self, flow_id='0'):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_del_flow(self,app,workflow):
        with app.test_request_context():
            assert FlowSettingView.del_flow(0)==""

#     def get_actions():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_actions(self,app,workflow):
        with app.test_request_context():
            assert FlowSettingView.get_actions()==""
 
#     def upt_flow_action(self, flow_id=0):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestFlowSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_upt_flow_action(self,app,workflow):
        with app.test_request_context():
            assert FlowSettingView.upt_flow_action(0)==""
            
# class WorkFlowSettingView(BaseView):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
class TestWorkFlowSettingView:
    #     def index(self):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_index_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_index_acl_guest(self,client,db_register2):
        url = url_for('workflowsetting.index',_external=True)
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        # (0, 403),
        (1, 200),
        # (2, 200),
        # (3, 200),
        # (4, 200),
        # (5, 200),
        # (6, 200),
    ])
    def test_index_acl(self,client,db_register2,users,users_index,status_code):
        login(client=client, email=users[users_index]['email'])
        url = url_for('workflowsetting.index',_external=True)
        res =  client.get(url)
        assert res.status_code == status_code  

    #     def workflow_detail(self, workflow_id='0'):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_workflow_detail_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_workflow_detail_acl_guest(self,client,db_register2):
        url = url_for('workflowsetting.workflow_detail',workflow_id='0',_external=True)
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_workflow_detail_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        # (0, 403),
        (1, 200),
        # (2, 200),
        # (3, 200),
        # (4, 200),
        # (5, 200),
        # (6, 200),
    ])
    def test_workflow_detail_acl(self,client,db_register2,users,users_index,status_code):
        login(client=client, email=users[users_index]['email'])
        url = url_for('workflowsetting.workflow_detail',workflow_id='0',_external=True)
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code  

    #     def update_workflow(self, workflow_id='0'):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_update_workflow_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_update_workflow_acl_guest(self,client,db_register2):
        url = url_for('workflowsetting.update_workflow',workflow_id='0',_external=True)
        res =  client.post(url)
        assert res.status_code == 302
        
        res =  client.put(url)
        assert res.status_code == 302


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_update_workflow_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        # (0, 403),
        (1, 200),
        # (2, 200),
        # (3, 200),
        # (4, 200),
        # (5, 200),
        # (6, 200),
    ])
    def test_update_workflow_acl(self,client,db_register2,users,users_index,status_code):
        login(client=client, email=users[users_index]['email'])
        url = url_for('workflowsetting.update_workflow',workflow_id='0',_external=True)
        with patch("flask.templating._render", return_value=""):
            res =  client.post(url)
            assert res.status_code == status_code  
        
        with patch("flask.templating._render", return_value=""):
            res =  client.put(url)
            assert res.status_code == status_code  

    #  def delete_workflow(self, workflow_id='0'):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_delete_workflow_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_delete_workflow_acl_guest(self,client,db_register2):
        url = url_for('workflowsetting.delete_workflow',workflow_id='0',_external=True)
        res =  client.delete(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_delete_workflow_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        # (0, 403),
        (1, 200),
        # (2, 200),
        # (3, 200),
        # (4, 200),
        # (5, 200),
        # (6, 200),
    ])
    def test_delete_workflow_acl(self,client,db_register2,users,users_index,status_code):
        login(client=client, email=users[users_index]['email'])
        url = url_for('workflowsetting.delete_workflow',workflow_id='0',_external=True)
        with patch("flask.templating._render", return_value=""):
            res =  client.delete(url)
            assert res.status_code == status_code  

    # def get_name_display_hide(cls, list_hide, role):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_get_name_display_hide -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_name_display_hide(self,app,users):
        role0 = (users[0]['obj']).roles[0]
        role1 = (users[1]['obj']).roles[0]
        role2 = (users[2]['obj']).roles[0]
        role3 = (users[3]['obj']).roles[0]
        role4 = (users[4]['obj']).roles[0]
        
        with app.test_request_context():
            assert WorkFlowSettingView.get_name_display_hide([role0],[role0,role1,role2,role3,role4])==(['Repository Administrator', 'System Administrator', 'Community Administrator', 'General'], ['Contributor'])
         
    #  def get_displays(cls, list_hide, role):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_get_displays -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_displays(self,app,users):
        role0 = (users[0]['obj']).roles[0]
        role1 = (users[1]['obj']).roles[0]
        role2 = (users[2]['obj']).roles[0]
        role3 = (users[3]['obj']).roles[0]
        role4 = (users[4]['obj']).roles[0]
        
        with app.test_request_context():
            ret = WorkFlowSettingView.get_displays([role0],[role0,role1,role2,role3,role4])
            assert isinstance(ret,list)==True
            assert ret == [role1,role2,role3,role4]

    # def save_workflow_role(cls, wf_id, list_hide):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_save_workflow_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_save_workflow_role(self,app,users,workflow):
        role0 = (users[0]['obj']).roles[0]
        role1 = (users[1]['obj']).roles[0]
        role2 = (users[2]['obj']).roles[0]
        role3 = (users[3]['obj']).roles[0]
        role4 = (users[4]['obj']).roles[0]
        
        wf = workflow['workflow']
        
        with app.test_request_context():
            assert WorkFlowSettingView.save_workflow_role(wf.id,[role0.id,role1.id,role2.id,role3.id,role4.id])

    # def get_language_workflows(cls, key):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_admin.py::TestWorkFlowSettingView::test_get_language_workflows -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_language_workflows(self,users):
        with self.test_request_context():
            assert self.get_language_workflows("display")=="Display"
            assert WorkFlowSettingView.get_language_workflows("hide")=="Hide"
            assert WorkFlowSettingView.get_language_workflows("display_hide")=="Display/Hide"
            
        with self.test_request_context(headers=[("Accept-Language", "en")]):
            assert WorkFlowSettingView.get_language_workflows("display")=="Display"
            assert WorkFlowSettingView.get_language_workflows("hide")=="Hide"
            assert WorkFlowSettingView.get_language_workflows("display_hide")=="Display/Hide"
        
        with self.test_request_context(headers=[("Accept-Language", "ja")]):
            assert WorkFlowSettingView.get_language_workflows("display")=="表示"
            assert WorkFlowSettingView.get_language_workflows("hide")=="非表示"
            assert WorkFlowSettingView.get_language_workflows("display_hide")=="表示/非表示"
            
