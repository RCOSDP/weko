# import mock
# import pytest
# from pytest_invenio.fixtures import database, app
# from weko_workflow.utils import is_usage_application_item_type
# from weko_workflow.api import WorkFlow,WorkActivity
# from weko_index_tree.api import Indexes
# from weko_index_tree.utils import get_index_id
# from weko_workflow.models import Activity

# def current_user():
#     role = Role(id=1, name='General')
#     user = User(email='User001@inveniosoftware.org', password='123456', active=True, roles=[admin_role])
#     return user

# @mock.patch('flask_login.current_user', side_effect=current_user)
# def test_get_activity_list():
#     """ Not is admin """
#     role1 = Role(id=1, name='General')
#     current_user = User(id=1, 
#                         email='User001@inveniosoftware.org', 
#                         password='123456', 
#                         active=True, 
#                         roles=[admin_role])
#     insert_workflow(database,1,flow_id,"Flow Name",1,1,1)
#     insert_activity(database,"A-20200108-00100",item_id,1,1,8)
    
#     with mock.patch('flask_login.current_user', return_ current_user),
#         mock.patch('weko_workflow.api..activities', return current_user):
#         from weko_workflow.api import get_activity_list
#         get_activity_list(0)
#     print('Test')
