import json
import copy
from unittest.mock import Mock
import uuid
from os.path import dirname, join
from datetime import datetime

from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_records import Record
from invenio_records.models import RecordMetadata
from weko_records.api import ItemsMetadata 
from weko_records.models import ItemMetadata
from weko_deposit.pidstore import weko_deposit_minter
from weko_deposit.api import WekoDeposit, WekoIndexer,WekoRecord
from invenio_search import InvenioSearch, RecordsSearch, current_search, current_search_client
from invenio_search import current_search
import pytest
from mock import patch
from unittest.mock import MagicMock
from invenio_pidrelations.models import PIDRelation
from invenio_records_files.api import Record
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect, RecordIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError

from weko_workflow.models import FlowDefine, FlowAction, FlowActionRole, WorkFlow, Activity, ActivityAction
def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


# def create_record(record_data, item_data):
#     """Create a test record."""
#     with db.session.begin_nested():
#         record_data = copy.deepcopy(record_data)
#         item_data = copy.deepcopy(item_data)
#         rec_uuid = uuid.uuid4()
        
#         PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
#         depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
#         if '.' in record_data["recid"]:
#             PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
#         record = Record.create(record_data, id_=rec_uuid)
#         item = ItemsMetadata.create(item_data, id_=rec_uuid)
        
#     return depid, record, item

# def create_record(record_data, item_data):
#     """Create a test record."""
#     with db.session.begin_nested():
#         record_data = copy.deepcopy(record_data)
#         item_data = copy.deepcopy(item_data)
#         rec_uuid = uuid.uuid4()
# 
#         recid = PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
#         depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
#         rel = PIDRelation.create(recid,depid,3)
#         db.session.add(rel)
#         parent = None
#         doi = None
#         if not ('.' in record_data["recid"]):
#             parent = PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
#             rel = PIDRelation.create(parent,recid,2,0)
#             db.session.add(rel)
#             if(int(record_data["recid"])%2==1):
#                 doi = PersistentIdentifier.create('doi', " https://doi.org/10.xyz/{}".format((str(record_data["recid"])).zfill(10)),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
#         else:
#             parent = PersistentIdentifier.get('parent','parent:{}'.format((str(record_data["recid"])).split('.')[0]))
#             if ('.0' in record_data["recid"]):
#                 rel = PIDRelation.create(parent,recid,3,2)
#                 db.session.add(rel)
#             else:
#                 rel = PIDRelation.create(parent,recid,2,(str(record_data["recid"])).split('.')[1])
#                 db.session.add(rel)
#             
#         record = WekoRecord.create(record_data, id_=rec_uuid)
#         deposit = WekoDeposit(record, record.model)
# 
#         deposit.commit()
# 
#         item = ItemsMetadata.create(item_data, id_=rec_uuid)
#     
#     return depid, recid,parent,doi,record, item


def create_record(record_data, item_data):
    """Create a test record."""
    with db.session.begin_nested():
        record_data = copy.deepcopy(record_data)
        item_data = copy.deepcopy(item_data)
        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid,3)
        db.session.add(rel)
        parent=None
        doi = None
        if "item_1617186819068" in record_data:
            doi_url = "https://doi.org/"+record_data["item_1617186819068"]["attribute_value_mlt"][0]["subitem_identifier_reg_text"]
            try:
                PersistentIdentifier.get("doi",doi_url)
            except PIDDoesNotExistError:
                doi = PersistentIdentifier.create('doi',doi_url,object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        if '.' in record_data["recid"]:
            parent = PersistentIdentifier.get("recid",int(float(record_data["recid"])))
            recid_p = PIDRelation.get_child_relations(parent).one_or_none()
            PIDRelation.create(recid_p.parent, recid,2)
        else:
            parent = PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(parent, recid,2,0)
            db.session.add(rel)
            RecordIdentifier.next()
        record = WekoRecord.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
        deposit = WekoDeposit(record, record.model)

        deposit.commit()

    return recid, depid, record, item, parent, doi, deposit


def fill_oauth2_headers(json_headers, token):
    """Create authentication headers (with a valid oauth2 token)."""
    headers = copy.deepcopy(json_headers)
    headers.append(
        ('Authorization', 'Bearer {0}'.format(token.access_token))
    )
    return headers


def create_activity(db, item_title, recid, path, login_user, shared_user, workflow, status, action_order):
    item_id = uuid.uuid4()
    if action_order > 2:
        record_metadata={
            "path":path,
            "owner":str(login_user.id),
            "recid":str(recid),
            "title":[item_title],
            "pubdate":{"attribute_name":"PubDate","attribute_value":"2024-01-11"},
            "_deposit":{"id":str(recid),"owner":[int(login_user.id)],"status":"draft","created_by":login_user.id,"owners_ext":{"email":login_user.email,"username":"","displayname":""}},
            "item_title":item_title,
            "author_link":[],
            "item_type_id":"1",
            "publish_date":"2024-01-11",
            "control_number":str(recid),
            "publish_status":"2",
            "weko_shared_id":shared_user,
            "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{"subitem_1551255647225": item_title,"subitem_1551255648112": "ja"}]},
            "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
            "relation_version_is_last": True
        }
    elif path is not None:
        record_metadata = {
            "recid":str(recid),
            "$schema":"https://127.0.0.1/schema/deposits/deposit-v1.0.0.json",
            "_deposit":{"id":str(recid),"owners":[int(login_user.id)],"status":"draft","created_by":login_user.id,"owners_ext":{"email":login_user.email,"usernamem":"","displayname":""}}
        }
    else:
        record_metadata = None
        
    if record_metadata:
        record = RecordMetadata(id=item_id,json=record_metadata)
        db.session.add(record)
    item_metadata = {
        "lang": "ja",
        "owner": str(login_user.id),
        "title": item_title,
        "$schema": "/items/jsonschema/1",
        "pubdate": "2023-12-26",
        "shared_user_id": shared_user,
        "item_1617186331708": [{"subitem_1551255647225": item_title,"subitem_1551255648112": "ja"}],
        "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}
    } if action_order > 2 else None
    if item_metadata:
        item = ItemMetadata(id=item_id,item_type_id=1,json=item_metadata)
        db.session.add(item)
    actions = FlowAction.query.filter_by(flow_id=workflow.flow_define.flow_id).order_by(FlowAction.action_order).all()
    now_action = actions[action_order-1]
    activity_id=f"A-00000001-{recid:05}"
    item_id = item_id if record_metadata else None
    activity = Activity(id=recid,activity_id=activity_id,item_id=item_id,workflow_id=workflow.id,flow_id=workflow.flow_id,
                        action_id=now_action.action_id,action_status=status,activity_status=status,
                        activity_login_user=login_user.id,activity_update_user=login_user.id,
                        activity_start=datetime.strptime('2024/01/11 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                        title=item_title,shared_user_id=shared_user,extra_info={},action_order=action_order
                        )
    db.session.add(activity)
    db.session.commit()
    for action in actions:
        if action.action_order == action_order:
            status = 'M'
        else:
            status = 'F'
        action_handler = login_user.id if action.action_id!=4 else -1
        activity_action = ActivityAction(activity_id=activity_id,action_id=action.action_id,action_status=status,action_handler=action_handler,action_order=action.action_order)
        db.session.add(activity_action)
    db.session.commit()
    
    return activity
    
def create_flow(db, define_id, flow_name, workflow_name, action_role, action_user, item_type):
    flow = FlowDefine(id=define_id,flow_id=uuid.uuid4(),flow_name=flow_name,flow_user=1)
    db.session.add(flow)
    db.session.commit()
    flow_actions=[
        FlowAction(flow_id=flow.flow_id, action_id=1, action_order=1),# start
        FlowAction(flow_id=flow.flow_id, action_id=3, action_order=2),# item registration
        FlowAction(flow_id=flow.flow_id, action_id=5, action_order=3),# item_link
        FlowAction(flow_id=flow.flow_id, action_id=4, action_order=4),# approval
        FlowAction(flow_id=flow.flow_id, action_id=2, action_order=5),# end
    ]
    db.session.add_all(flow_actions)
    db.session.commit()
    workflow = WorkFlow(flows_id=uuid.uuid4(),flows_name=workflow_name,itemtype_id=item_type.id,flow_id=flow.id)
    db.session.add(workflow)
    db.session.commit()
    if action_role:
        # {action_id:{value:[],flg:true}}
        for action_id, data in action_role.items():
            flow_action = FlowAction.query.filter_by(flow_id=flow.flow_id,action_id=action_id).one()
            db.session.add(
                FlowActionRole(flow_action_id=flow_action.id,action_role=data["value"],action_role_exclude=data["flg"])
            )
    if action_user:
        for action_id, data in action_user.items():
            flow_action = FlowAction.query.filter_by(flow_id=flow.flow_id,action_id=action_id).one()
            db.session.add(
                FlowActionRole(flow_action_id=flow_action.id,action_user=data["value"],action_user_exclude=data["flg"])
            )
    db.session.commit()
    return workflow