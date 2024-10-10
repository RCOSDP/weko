import json
import copy
import uuid
from os.path import dirname, join
from flask import url_for
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, RecordIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidrelations.models import PIDRelation
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_records.api import ItemsMetadata, WekoRecord


def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


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

def login(app, client, obj = None, email=None, password=None):
    """Log the user in with the test client."""
    with app.test_request_context():
        login_url = url_for('security.login')

    if obj:
        email = obj.email
        password = obj.password_plaintext
        client.post(login_url, data=dict(
            email=email or app.config['TEST_USER_EMAIL'],
            password=password or app.config['TEST_USER_PASSWORD'],
        ))
    else:
        client.post(login_url, data=dict(
            email=email or app.config['TEST_USER_EMAIL'],
            password=password or app.config['TEST_USER_PASSWORD'],
        ))

def logout(app,client):
    with app.test_request_context():
        logout_url = url_for("security.logout")
    client.get(logout_url)
