import json
import copy
import uuid
from os.path import dirname, join

from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
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
        recid = PersistentIdentifier.create(
            'recid',
            record_data['recid'],
            object_type='rec',
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED
        )
        depid = PersistentIdentifier.create(
            'depid',
            record_data['recid'],
            object_type='rec',
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED
        )
        record = WekoRecord.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
    return recid, record, item
