import uuid
import copy
import json

from invenio_db import db as db_
from invenio_pidstore import current_pidstore
from invenio_records import Record


def create_record(data):
    """Create a test record."""
    with db_.session.begin_nested():
        data = copy.deepcopy(data)
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid'](rec_uuid, data)
        record = Record.create(data, id_=rec_uuid)
    return pid, record
