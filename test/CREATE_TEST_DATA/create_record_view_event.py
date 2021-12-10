from invenio_stats import current_stats
from invenio_stats.utils import get_anonymization_salt
from invenio_pidstore.models import RecordIdentifier, PersistentIdentifier
from weko_deposit.api import WekoRecord
from invenio_db import db
from datetime import datetime
from sqlalchemy.sql.expression import func
import hashlib
import random
import settings
import uuid

event_type = 'record-view'

def main():
    for i in range(settings.RECORD_VIEW_LIMIT):
        create_event()
        if i % 1000 == 0 and i != 0:
            print('{} search event created'.format(i))


def create_event():
    month = random.randint(1, 12)
    year = 2021 if month < 9 else 2020
    if month in [1, 3, 5, 7, 8, 10, 12]:
        day = random.randint(1, 31)
    elif month in [4, 6, 9, 11]:
        day = random.randint(1, 30)
    else:
        day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(1, 59)
    second = random.randint(1, 59)
    date = datetime(year, month, day, hour, minute, second)
    event_date = datetime.strftime(date, '%Y-%m-%d %H:%M:%S.%f')

    record = None
    while not record:
        max_record_id = db.session.query(func.max(RecordIdentifier.recid)).one_or_none()[0]
        record_id = random.randint(1, max_record_id)
        try:
            record = WekoRecord.get_record_by_pid(record_id)
        except:
            record = None

    ip_address = '{}.{}.{}.{}'.format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255))

    index_list = []
    record_navs = []
    with app.test_request_context() as ctx:
        record_navs = record.navi
    if record_navs:
        for index in record_navs:
            index_list.append(dict(
                index_id=str(index[1]),
                index_name=index[3],
                index_name_en=index[4]
            ))

    doc_event = dict(
        timestamp=event_date,
        unique_session_id=get_hash_id(date),
        referrer='https://localhost/records/{}'.format(record['recid']),
        country=settings.COUNTRYS[random.randint(0, 100) % len(settings.COUNTRYS)],
        is_robot=False,
        is_restricted=False,
        cur_user_id=settings.USERS[random.randint(0, 100) % len(settings.USERS)]['id'],
        hostname=None,
        remote_addr=ip_address,
        pid_type='recid',
        pid_value=record['recid'],
        record_name=record['title'][0],
        site_license_flag=False,
        site_license_name=None,
        record_id=str(record.id),
        record_index_list=index_list,
        visitor_id=get_hash_id(date)
    )
    doc_event = build_unique_id(doc_event)

    current_stats.publish(event_type, [doc_event])


def build_unique_id(doc):
    """Build unique identifier."""
    key = '{0}_{1}_{2}_{3}_{4}'.format(
        doc['pid_type'],
        doc['pid_value'],
        doc['remote_addr'],
        doc['unique_session_id'],
        doc['visitor_id'])

    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc

def get_hash_id(date_obj):
    salt = get_anonymization_salt(date_obj)
    hash_id = hashlib.sha224(salt.encode('utf-8'))
    hash_id = hash_id.hexdigest()
    return hash_id

if __name__ == '__main__':
    main()
