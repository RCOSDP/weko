import json
import copy
from unittest.mock import Mock
import uuid
from os.path import dirname, join

from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_records import Record
from weko_records.api import ItemsMetadata 
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
