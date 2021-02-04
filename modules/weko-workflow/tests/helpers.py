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
    from flask_security.utils import hash_password

    # insert role of admin
    admin_role = Role(id=1, name='Administrator')
    database.session.add(admin_role)
    
    password = hash_password('123456')

    admin = User(email='info@inveniosoftware.org', password=password, active=True,
                 roles=[admin_role])  
    admin2 = User(email='admin@inveniosoftware.org', password=password, active=True,
                 roles=[admin_role])    
    admin_profile= UserProfile(user_id=1,user=admin,_username=password,position='Professor')

    non_admin = User(email='non_admin@invenio.org', password=password,
                     active=True)
    non_admin_profile= UserProfile(user_id=2,user=non_admin,_username='user1',position='Professor')
    non_admin2 = User(email='non_admin2@invenio.org', password=password,
                     active=True)
    non_admin_profile2= UserProfile(user_id=3,user=non_admin2,_username='user2',position='Professor')
    student_role = Role(id=3, name='Student')
    database.session.add(student_role)

    student = User(email='student@invenio.org', password=password,
                   active=True, roles=[student_role])
    database.session.add(admin)
    database.session.add(admin2)
    database.session.add(non_admin)
    database.session.add(non_admin_profile) 
    database.session.add(admin_profile)
    database.session.add(non_admin2)
    database.session.add(non_admin_profile2)
    database.session.add(student)
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


def insert_file_permission_to_db(database):
    """Insert file permission to db."""
    from weko_records_ui.models import FilePermission
    file_permission = FilePermission(
        user_id=3, record_id=1,
        file_name='file.txt',
        usage_application_activity_id='activity1',
        status=1)

    file_permission2 = FilePermission(
        user_id=4, record_id=1,
        file_name='file.txt',
        usage_application_activity_id='activity2',
        status=-1)
    file_permission3 = FilePermission(
        user_id=5, record_id=1,
        file_name='file.txt',
        usage_application_activity_id='activity3',
        status=1)
    database.session.add(file_permission)
    database.session.add(file_permission2)
    database.session.add(file_permission3)
    database.session.commit()


def create_default_location(database):
    """Insert location for buckets."""
    from invenio_files_rest.models import Location
    location = Location()
    location.id = 1
    location.name = 'local'
    location.uri = '/var/tmp'
    location.default = True
    database.session.add(location)
    database.session.commit()


def insert_deposit(database):
    """Insert a deposit."""
    from weko_deposit.api import WekoDeposit
    create_default_location(database)

    # 1 = activity id, there is only 1 activity in test
    deposit = WekoDeposit.create({}, recid=int(1))
    return deposit


def update_deposit(pid):
    """Update deposit."""
    item_status = {
        'index': [1578472847540],
        'actions': 'publish',
    }
    from weko_deposit.api import WekoDeposit
    sql = "UPDATE workflow_activity set item_id = '{}' where id = 100".format(
        pid.object_uuid)
    run_sql(sql)

    record = WekoDeposit.get_record(pid.object_uuid)
    deposit = WekoDeposit(record, record.model)
    from weko_records.api import ItemsMetadata
    item_metadata = ItemsMetadata.get_record(id_=pid.object_uuid).dumps()

    deposit.update(item_status, item_metadata)
    deposit.commit()
    return deposit['_buckets']['deposit']


def mapping_jpcoar():
    """Insert jpcoar mapping for item type."""
    import json
    usage_json = json.dumps(read_json('tests/jpcoar_usage.json'))
    sql_usage = (
        "INSERT INTO item_type_mapping(created,updated,id,item_type_id"
        ",version_id,{}) values (now(),now(),1,2,1,jsonb('{}')   ) ;") \
        .format('"mapping"', usage_json)
    run_sql(sql_usage)

    report_json = json.dumps(read_json('tests/jpcoar_report.json'))
    sql_report = (
        "INSERT INTO item_type_mapping(created,updated,id,item_type_id"
        ",version_id,{}) values (now(),now(),2,3,1,jsonb('{}')   ) ;") \
        .format('"mapping"', report_json)
    run_sql(sql_report)        



from json_helpers import read_json
def init_data(database):
    """Init data for test."""
    # prepare something ahead of all tests
    insert_user_to_db(database)
    insert_access()
    insert_index(database,1578472847540,0,1,'Usage Application Index','Usage Application Index','Usage Application Index')
    insert_index(database,1578473336705,0,2,'Usage Report Index','Usage Report Index','Usage Report Index')
    insert_action()
    insert_flow_actions()
    insert_item_type_usage_application(database)
    insert_item_type_output_report(database)
    insert_item_type_usage_report(database)
    mapping_jpcoar()
    insert_workflow_h()
    insert_activity_h()
    # insert_dumps_activities()
    insert_file_permission_to_db(database)    


def insert_action():
    """Insert default action."""
    run_sql(
        "INSERT INTO workflow_action(status,created,updated,action_makedate,"
        "action_lastdate,id,action_name,action_endpoint,action_is_need_agree) "
        "values ('N',now(),now(),now(),now(),1,'Start','begin_action', 'f')")
    run_sql(
        "INSERT INTO workflow_action(status,created,updated,action_makedate,"
        "action_lastdate,id,action_name,action_endpoint,action_is_need_agree) "
        "values ('N',now(),now(),now(),now(),2,"
        "'Item Registration for Usage Application',"
        "'item_login_application', 'f')")
    run_sql(
        "INSERT INTO workflow_action(status,created,updated,action_makedate,"
        "action_lastdate,id,action_name,action_endpoint,action_is_need_agree) "
        "values ('N',now(),now(),now(),now(),3,"
        "'Approval action performed by Administrator',"
        "'approval_administrator', 'f')")
    run_sql(
        "INSERT INTO workflow_action(status,created,updated,action_makedate,"
        "action_lastdate,id,action_name,action_endpoint,action_is_need_agree) "
        "values ('N',now(),now(),now(),now(),4,'End','end_action', 'f')")


def insert_flow_actions():
    """Insert flow."""
    run_sql(
        "INSERT INTO workflow_flow_define(status,created,updated,id,flow_id,"
        "flow_name,flow_status) values "
        "('N',now(),now(),1,'a14500c4-a984-43a0-acf2-31fcb5d13efa',"
        "'Approval by advisor and admin','A')")
    run_sql(
        "INSERT INTO workflow_flow_action(status,created,updated,flow_id,"
        "action_id,action_version,action_order,action_status,action_date) "
        "values ('N',now(),now(),'a14500c4-a984-43a0-acf2-31fcb5d13efa',1,"
        "'1.0.0',1,'A',now())")
    run_sql(
        "INSERT INTO workflow_flow_action(status,created,updated,flow_id,"
        "action_id,action_version,action_order,action_status,action_date) "
        "values ('N',now(),now(),'a14500c4-a984-43a0-acf2-31fcb5d13efa',"
        "2,'1.0.0',2,'A',now())")
    run_sql(
        "INSERT INTO workflow_flow_action(status,created,updated,flow_id,"
        "action_id,action_version,action_order,action_status,action_date) "
        "values ('N',now(),now(),'a14500c4-a984-43a0-acf2-31fcb5d13efa',"
        "3,'1.0.0',3,'A',now())")
    run_sql(
        "INSERT INTO workflow_flow_action(status,created,updated,flow_id,"
        "action_id,action_version,action_order,action_status,action_date) "
        "values ('N',now(),now(),'a14500c4-a984-43a0-acf2-31fcb5d13efa',"
        "4,'1.0.0',4,'A',now())")
    run_sql(
        "INSERT INTO workflow_action_status(status,created,updated,"
        "action_status_id,action_status_name,action_status_desc,action_scopes)"
        "values ('N',now(),now(),'B','action_begin',"
        "'Indicates that the action has started.','sys')")
    run_sql(
        "INSERT INTO workflow_action_status(status,created,updated,"
        "action_status_id,action_status_name,action_status_desc,action_scopes)"
        "values ('N',now(),now(),'F','action_done',"
        "'Indicates that the action has been completed.','sys,user')")
    run_sql(
        "INSERT INTO workflow_action_status(status,created,updated,"
        "action_status_id,action_status_name,action_status_desc,action_scopes)"
        "values ('N',now(),now(),'M','action_doing',"
        "'Indicates that the action is not completed','user')")


def insert_item_type_usage_application(database):
    """Insert item type usage application."""
    from weko_records.models import ItemType
    insert_item_type_name_h(database, 'ライフ利用申請', 2)
    itemtype = ItemType()
    itemtype.name_id = 2
    itemtype.id = 2
    itemtype.harvesting_type = False
    itemtype.form = read_json('tests/form_usage.json')
    itemtype.schema = read_json('tests/schema_usage.json')
    itemtype.tag = 1
    itemtype.version_id = 1
    database.session.add(itemtype)
    database.session.commit()


def insert_item_type_usage_report(database):
    """Insert item type usage report."""
    from weko_records.models import ItemType
    insert_item_type_name_h(database, 'Usage Report', 3)
    itemtype = ItemType()
    itemtype.name_id = 3
    itemtype.id = 3
    itemtype.harvesting_type = False
    itemtype.form = read_json('tests/form_report.json')
    itemtype.schema = read_json('tests/schema_report.json')
    itemtype.tag = 1
    itemtype.version_id = 1
    database.session.add(itemtype)
    database.session.commit()


def insert_item_type_output_report(database):
    """Insert item type usage application."""
    from weko_records.models import ItemType
    insert_item_type_name_h(database, '成果物登録', 4)
    itemtype = ItemType()
    itemtype.name_id = 4
    itemtype.id = 4
    itemtype.harvesting_type = False
    itemtype.form = read_json('tests/form_usage.json')
    itemtype.schema = read_json('tests/schema_usage.json')
    itemtype.tag = 1
    itemtype.version_id = 1
    database.session.add(itemtype)
    database.session.commit()


def insert_workflow_h():
    """Insert workflow."""
    run_sql(
        "INSERT INTO workflow_workflow(id,flows_id,status,created,updated,"
        "flows_name,itemtype_id,flow_id,index_tree_id) values "
        "(24,'79713a4d-1ef1-4661-b73c-a4d0975b086e','N',now(),now(),"
        "'Life Usage Application - Student',2,1,1578472847540)")
    run_sql(
        "INSERT INTO workflow_workflow(id,flows_id,status,created,updated,"
        "flows_name,itemtype_id,flow_id,index_tree_id) values "
        "(25,'25bb6ea2-cf94-44e8-b8b6-0dabb1ae786d','N',now(),now(),"
        "'Usage Report',3,1,1578473336705)")
    run_sql(
        "INSERT INTO workflow_workflow(id,flows_id,status,created,updated,"
        "flows_name,itemtype_id,flow_id,index_tree_id) values "
        "(26,'259e87c8-78b8-47d7-b6d0-339d82a5da4a','N',now(),now(),"
        "'Output Report',4,1,1578473336705)")


def insert_activity_h():
    """Insert a usage application activity."""
    run_sql(
        "INSERT INTO workflow_activity(id,activity_id,status,workflow_id,"
        "flow_id,created,updated,activity_start) values "
        "(100,'A-20200113-00004','N',24,1,now(),now(),now())")
    run_sql(
        "INSERT INTO workflow_activity_action(status,created,updated,"
        "activity_id,action_id,action_status,action_handler) values "
        "('N',now(),now(), 'A-20200113-00004',3,'M',1)")


def insert_dumps_activities():
    """Insert dump simple activity."""
    run_sql(
        "INSERT INTO workflow_activity(id,activity_id,status,workflow_id,"
        "flow_id,created,updated,activity_start,activity_login_user) values "
        "(150,'A-20200113-00005','N',24,1,now(),now(),now(),1)")
    run_sql(
        "INSERT INTO workflow_activity(id,activity_id,status,workflow_id,"
        "flow_id,created,updated,activity_start,activity_login_user) values "
        "(200,'A-20200113-00006','N',24,1,now(),now(),now(),1)")

    run_sql(
        "INSERT INTO workflow_activity(id,activity_id,status,workflow_id,"
        "flow_id,created,updated,activity_start,activity_login_user) values "
        "(300,'A-20200113-00007','N',26,1,now(),now(),now(),1)")

    run_sql(
        "INSERT INTO workflow_activity(id,activity_id,status,workflow_id,"
        "flow_id,created,updated,activity_start,activity_login_user) values "
        "(400,'A-20200113-00008','N',26,1,now(),now(),now(),1)")


def insert_item_type_h(database):
    """Insert item type."""
    from weko_records.models import ItemType
    from json_helpers import read_json
    insert_item_type_name_h(database, 'Test item type', 1)
    itemtype = ItemType()
    itemtype.id = 1
    itemtype.name_id = 1
    itemtype.harvesting_type = False
    itemtype.form = read_json('tests/schema_form.json')
    itemtype.tag = 1
    itemtype.version_id = 1
    database.session.add(itemtype)
    database.session.commit()    


def set_language(client, language):
    """Login a user via the session."""
    with client.session_transaction() as sess:
        sess['language'] = language  # Set language


def insert_item_type_name_h(database, name, name_id):
    """Insert item type name."""
    from weko_records.models import ItemTypeName
    itemtype_name = ItemTypeName()
    itemtype_name.name = name
    itemtype_name.id = name_id
    database.session.add(itemtype_name)
    database.session.commit()



def insert_user_to_db_h(database):
    """Insert some user to db."""
    from invenio_accounts.models import User, Role
    from flask_security.utils import hash_password
    # insert roles
    admin_role = Role(id=1, name='Administrator')
    student_role = Role(id=2, name='Student')
    graduated_student_role = Role(id=3, name='Graduated Student')

    # insert permission

    database.session.add(admin_role)
    database.session.add(student_role)
    database.session.add(graduated_student_role)

    password = hash_password('123456')

    admin = User(id=100, email='admin@invenio.org', password=password, active=True,
                 roles=[admin_role])
    student = User(id=200,email='student@invenio.org', password=password,
                   active=True, roles=[student_role])
    graduated_student = User(id=300,email='graduated_student@invenio.org',
                             password=password,
                             active=True, roles=[graduated_student_role])
    database.session.add(admin)
    database.session.add(student)
    database.session.add(graduated_student)
    database.session.commit()


def insert_record_metadata_h(database):
    """Insert record metadata."""
    from invenio_records.models import RecordMetadata
    from invenio_pidstore.models import PersistentIdentifier
    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value=str(1)
    ).first()

    insert_item_metadata(database, pid)
    usage_application_metadata = RecordMetadata()
    usage_application_metadata.id = pid.object_uuid
    usage_application_metadata.json = read_json(
        'tests/record_metadata_app.json')

    database.session.merge(usage_application_metadata)
    database.session.commit()    


def insert_item_metadata(database, pid):
    """Insert item metadata."""
    from weko_records.models import ItemMetadata
    meta_json = read_json('tests/item_metadata_app.json')
    item_metadata = ItemMetadata()
    item_metadata.json = meta_json

    item_metadata.id = pid.object_uuid
    item_metadata.item_type_id = 2
    item_metadata.version_id = 1
    database.session.add(item_metadata)
    database.session.commit()
    update_deposit(pid)