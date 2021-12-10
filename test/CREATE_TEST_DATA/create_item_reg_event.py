from invenio_stats import current_stats
from invenio_stats.utils import get_anonymization_salt
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from datetime import datetime
import hashlib
import random
import settings
import uuid

event_type = 'item-create'

def main():
    pid_list = PersistentIdentifier.query.filter_by(pid_type='depid') \
        .filter(PersistentIdentifier.pid_value.like('%.%')).all()
    for pid in pid_list:
        create_event(pid)


def create_event(pid):
    ip_address = '{}.{}.{}.{}'.format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255))
    country = settings.COUNTRYS[random.randint(0, 100) % len(settings.COUNTRYS)]

    record = RecordMetadata.query.filter_by(id=str(pid.object_uuid)).one_or_none()
    date = datetime.strptime(record.json['publish_date'], '%Y-%m-%d')
    event_date = datetime.strftime(date, '%Y-%m-%d %H:%M:%S.%f')
    hash_id = get_hash_id(date)

    pid_value = record.json['recid'].split('.')[0]
    doc_event = dict(
        timestamp=event_date,
        unique_session_id=hash_id,
        referrer='https://localhost:4403/items/iframe/index/{}'.format(pid_value),
        country=country,
        is_robot=False,
        is_restricted=False,
        cur_user_id=record.json['owner'],
        hostname=None,
        remote_addr=ip_address,
        pid_type='depid',
        pid_value=pid_value,
        record_name=record.json['title'][0],
        username="None",
        visitor_id=hash_id
    )
    doc_event = build_unique_id(doc_event)
    current_stats.publish(event_type, [doc_event])

    pid_value = record.json['recid']
    doc_event = dict(
        timestamp=event_date,
        unique_session_id=hash_id,
        referrer='https://localhost:4403/workflow/',
        country=country,
        is_robot=False,
        is_restricted=False,
        cur_user_id=record.json['owner'],
        hostname=None,
        remote_addr=ip_address,
        pid_type='depid',
        pid_value=pid_value,
        record_name=record.json['title'][0],
        username=None,
        visitor_id=hash_id
    )
    doc_event = build_unique_id(doc_event)
    current_stats.publish(event_type, [doc_event])

def build_unique_id(doc):
    """Build unique identifier."""
    key = '{0}_{1}_{2}'.format(
        "item", "create", doc['pid_value'])

    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc

def get_hash_id(date_obj):
    salt = get_anonymization_salt(date_obj)
    hash_id = hashlib.sha224(salt.encode('utf-8'))
    hash_id = hash_id.hexdigest()
    return hash_id

if __name__ == '__main__':
    main()
