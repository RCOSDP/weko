from datetime import date, datetime, timedelta

def login_user_via_session(client, user_id):
    """Login a user via the session."""
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['_fresh'] = True


def login(app, client, email=None, password=None):
    """Log the user in with the test client."""
    from flask import url_for
    with app.test_request_context():
        login_url = url_for('security.login')

    client.post(login_url, data=dict(
        email=email or app.config['TEST_USER_EMAIL'],
        password=password or app.config['TEST_USER_PASSWORD'],
    ))

def insert_user_to_db(database):
    from invenio_accounts.models import User, Role
    from weko_user_profiles import UserProfile

    # insert role of admin
    admin_role = Role(id=1, name='Administrator')
    database.session.add(admin_role)

    admin = User(email='info@inveniosoftware.org', password='123456', active=True,
                 roles=[admin_role])  
    admin2 = User(email='admin@inveniosoftware.org', password='123456', active=True,
                 roles=[admin_role])    
    admin_profile= UserProfile(user_id=1,user=admin,_username='admin',position='Professor')

    non_admin = User(email='non_admin@invenio.org', password='123456',
                     active=True)
    non_admin_profile= UserProfile(user_id=2,user=non_admin,_username='user1',position='Professor')
    non_admin2 = User(email='non_admin2@invenio.org', password='123456',
                     active=True)
    non_admin_profile2= UserProfile(user_id=3,user=non_admin2,_username='user2',position='Professor')

    database.session.add(admin)
    database.session.add(admin2)
    database.session.add(non_admin)
    database.session.add(non_admin_profile) 
    database.session.add(admin_profile)
    database.session.add(non_admin2)
    database.session.add(non_admin_profile2)
    database.session.commit()

def insert_item_type_name(database,name,has_site_license,is_active):
    from weko_records.models import ItemTypeName
    item_name = ItemTypeName(name=name,has_site_license=has_site_license,is_active=is_active)
    database.session.add(item_name) 
    database.session.commit()

def insert_item_type(database,name_id,schema,form,render,tag,version_id,is_deleted):
    from weko_records.models import ItemType
    item_type = ItemType(name_id=name_id, harvesting_type=False, schema={}, form={}, render={}, tag=tag,version_id=version_id, is_deleted=is_deleted)
    database.session.add(item_type) 
    database.session.commit()

def insert_flow(database,_id,flow_id,flow_name,flow_user,flow_status):
    from weko_workflow.models import FlowDefine
    flow = FlowDefine(id=_id,flow_id=flow_id,flow_name=flow_name,flow_user=flow_user,flow_status=flow_status)
    database.session.add(flow) 
    database.session.commit()

def insert_index(database,id,parent,position,index_name,index_name_english,index_link_name_english):
    from weko_index_tree.models import Index
    index = Index(id=id,parent=parent ,position=position,index_name=index_name,index_name_english=index_name_english,index_link_name_english=index_link_name_english)
    database.session.add(index) 
    database.session.commit()

def insert_workflow(database,id,flows_id,flows_name,itemtype_id,flow_id,index_tree_id):
    from weko_workflow.models import WorkFlow
    workflow = WorkFlow(id =id,flows_id=flows_id,flows_name=flows_name,itemtype_id=itemtype_id,flow_id=flow_id,index_tree_id=index_tree_id)
    database.session.add(workflow) 
    database.session.commit()

def insert_activity(database,activity_id, item_id, workflow_id, flow_id,current_action_id):
    from weko_workflow.models import Activity
    activity = Activity(activity_id=activity_id, item_id=item_id, workflow_id=workflow_id, flow_id=flow_id,activity_start="2020-01-08 09:14:14",activity_confirm_term_of_use=False,action_id=current_action_id)
    database.session.add(activity) 
    database.session.commit()
    return activity

def insert_record_metadata(database,id,jsondata):
    from invenio_records.models import RecordMetadata
    # jsondata = {"item_1575270782459": {"attribute_name": "Stop/Continue","attribute_value_mlt": [{ "subitem_stop/continue": "Continue" } ]}}
    recordMetadata = RecordMetadata(id=id, json =jsondata, version_id =1)
    database.session.add(recordMetadata) 
    database.session.commit()

def insert_flow_action(database,flow_id,action_id,action_order):
    from weko_workflow.models import FlowAction
    flow_action = FlowAction(flow_id=flow_id,action_id=action_id,action_order=action_order,action_status="A",action_date="2020-01-08 09:14:14")
    database.session.add(flow_action) 
    database.session.commit()

def insert_activity_action(database,activity_id,action_id,action_handler):
    from weko_workflow.models import ActivityAction,ActionStatus
    activity_action = ActivityAction(activity_id=activity_id,action_id=action_id,action_status="A",action_handler=action_handler)
    database.session.add(activity_action) 
    database.session.commit()

def run_sql(sql):
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    conn = psycopg2.connect(database='test', user='invenio',
                            password='dbpass123', host='postgresql')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()

def insert_access():
    run_sql(
        "INSERT INTO access_actionsroles(action,exclude,role_id) values ('superuser-access','f',1)")
    run_sql(
        "INSERT INTO access_actionsroles(action,exclude,role_id) values ('item-access','f',1)")

def insert_activity_backup():
    run_sql(
        "INSERT INTO workflow_workflow(id,flows_id,status,created,updated,flows_name,itemtype_id,flow_id,index_tree_id) values (24,'79713a4d-1ef1-4661-b73c-a4d0975b086e','N',now(),now(),'Life Usage Application - Student',1,1,1578472847540)")
    run_sql(
        "INSERT INTO workflow_activity(id,activity_id,status,workflow_id,flow_id,created,updated,activity_start) values (1,'A-20200113-00004','N',24,1,now(),now(),now())")
    run_sql(
        "INSERT INTO workflow_activity_action(status,created,updated,activity_id,action_id,action_status,action_handler) values \
         ('N',now(),now(), 'A-20200113-00004',2,'M',1)")


def insert_action_to_db(database):
    from weko_workflow.models import Action, FlowDefine, FlowAction
    action_start = Action(status='N', id=1, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Start', action_desc='Indicates that the action has started.', action_endpoint='begin_action', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_end = Action(status='N', id=2, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='End', action_desc='Indicates that the action has been completed.', action_endpoint='end_action', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_item_registration = Action(status='N', id=3, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Item Registration', action_desc='Registering items.', action_endpoint='item_login', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_approval = Action(status='N', id=4, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Approval', action_desc='Approval action for approval requested items.', action_endpoint='approval', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_item_registration_application = Action(status='N', id=8, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Item Registration for Usage Application', action_desc='Item Registration for Usage Application.', action_endpoint='item_login_application', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00',action_is_need_agree=True)
    action_item_link = Action(status='N', id=5, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Item Link', action_desc='Plug-in for link items.', action_endpoint='item_link', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_oa_policy = Action(status='N', id=6, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='OA Policy Confirmation', action_desc='Action for OA Policy confirmation.', action_endpoint='oa_policy', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_grant = Action(status='N', id=7, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Identifier Grant', action_desc='Select DOI issuing organization and CNRI.', action_endpoint='identifier_grant', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_approval_guarantor = Action(status='N', id=9, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Approval by Guarantor', action_desc='Approval action performed by Guarantor.', action_endpoint='approval_guarantor', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_approval_advisor = Action(status='N', id=10, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Approval by Advisor', action_desc='Approval action performed by Advisor.', action_endpoint='approval_advisor', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    action_approval_admin = Action(status='N', id=11, created='2019-11-20 12:06:14', updated='2019-11-20 12:06:14', action_name='Approval by Administrator', action_desc='Approval action performed by Administrator.', action_endpoint='approval_administrator', action_version='2018-05-15 00:00:00', action_lastdate='2018-05-15 00:00:00')
    database.session.add(action_start)
    database.session.add(action_end)
    database.session.add(action_item_registration)
    database.session.add(action_item_registration_application)
    database.session.add(action_approval)
    database.session.add(action_item_link)
    database.session.add(action_oa_policy)
    database.session.add(action_grant)
    database.session.add(action_approval_guarantor)
    database.session.add(action_approval_advisor)
    database.session.add(action_approval_admin)
    database.session.commit()

def insert_flow_action1():
    run_sql("INSERT INTO public.workflow_flow_action(status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date) VALUES('N', '2020-01-08 08:19:33.493', '2020-01-08 08:19:33.493', 1, '2b40b793-0414-4e1b-8704-1314c093394b', 1, '1.0.0', 1, NULL, 'A', '2020-01-08 08:19:33.493')")
    run_sql("INSERT INTO public.workflow_flow_action(status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date) VALUES('N', '2020-01-08 08:20:52.495', '2020-01-08 08:20:52.496', 3, '2b40b793-0414-4e1b-8704-1314c093394b', 8, '1.0.0', 2, NULL, 'A', '2020-01-08 08:20:52.496')")
    run_sql("INSERT INTO public.workflow_flow_action(status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date) VALUES('N', '2020-01-08 08:20:52.502', '2020-01-08 08:20:52.502', 4, '2b40b793-0414-4e1b-8704-1314c093394b', 11, '1.0.0', 3, NULL, 'A', '2020-01-08 08:20:52.502')")
    run_sql("INSERT INTO public.workflow_flow_action(status, created, updated, id, flow_id, action_id, action_version, action_order, action_condition, action_status, action_date) VALUES('N', '2020-01-08 08:19:33.495', '2020-01-08 08:20:52.505', 2, '2b40b793-0414-4e1b-8704-1314c093394b', 2, '1.0.0', 4, NULL, 'A', '2020-01-08 08:19:33.495')")

def insert_flow_define():
    run_sql("INSERT INTO public.workflow_flow_define(status, created, updated, id, flow_id, flow_name, flow_user, flow_status) VALUES('N', '2020-01-08 08:33:42.014', '2020-01-14 07:04:50.432', 5, '18f974eb-bb67-446e-9ce1-db57110a74ca', 'JGSSデータ登録', 1, 'A')")

def insert_flow_role():
    run_sql("INSERT INTO public.workflow_flow_define(status, created, updated, id, flow_id, flow_name, flow_user, flow_status)VALUES('N', '2020-01-08 08:33:42.014', '2020-01-14 07:04:50.432', 5, '2b40b793-0414-4e1b-8704-1314c093394b', 'JGSSデータ登録', 1, 'A');")