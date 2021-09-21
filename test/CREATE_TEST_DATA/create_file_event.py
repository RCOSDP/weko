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

event_type = ['file-download', 'file-preview']
event_counter = {'file-download': 0, 'file-preview': 0}

def main():
    for i in range(settings.FILE_LIMIT):
        create_event()
        if i % 1000 == 0 and i != 0:
            print('{} file event created'.format(i))
    print(event_counter)


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
    file_obj = None
    while not file_obj:
        max_record_id = db.session.query(func.max(RecordIdentifier.recid)).one_or_none()[0]
        record_id = random.randint(1, max_record_id)
        try:
            record = WekoRecord.get_record_by_pid(record_id)
            if len(record.files) > 0:
                file_obj = record.files[random.randint(0, len(record.files) - 1)]
        except:
            pass

    ip_address = '{}.{}.{}.{}'.format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255))

    index_list = ''
    record_navs = []
    with app.test_request_context() as ctx:
        record_navs = record.navi
    if len(record_navs) > 0:
        for index in record_navs:
            index_list += index[3] + '|'
    index_list = index_list[:len(index_list) - 1]

    user = random.randint(0, 100) % len(settings.USERS)

    doc_event = dict(
        timestamp=event_date,
        unique_session_id=get_hash_id(date),
        referrer='https://localhost/records/{}'.format(record['recid']),
        country=settings.COUNTRYS[random.randint(0, 100) % len(settings.COUNTRYS)],
        is_robot=False,
        is_restricted=False,
        cur_user_id=settings.USERS[user]['id'],
        hostname=None,
        remote_addr=ip_address,
        site_license_flag=False,
        site_license_name=None,
        userrole=settings.USERS[user]['role'],
        user_group_list=None,
        item_title=record['title'][0],
        item_id=record['recid'],
        bucket_id=file_obj.data['bucket'],
        file_id=str(file_obj.file.id),
        file_key=file_obj.data['key'],
        is_billing_item=False,
        billing_file_price='',
        size=file_obj.data['size'],
        accessrole=file_obj.data['accessrole'],
        index_list=index_list,
        visitor_id=get_hash_id(date)
    )
    doc_event = build_unique_id(doc_event)
    type = event_type[random.randint(0, 1)]
    event_counter[type] += 1
    current_stats.publish(type, [doc_event])


def build_unique_id(doc):
    """Build unique identifier."""
    key = '{0}_{1}_{2}_{3}'.format(
        doc['bucket_id'],
        doc['file_id'],
        doc['remote_addr'],
        doc['unique_session_id'])

    doc['unique_id'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, key))

    return doc

def get_hash_id(date_obj):
    salt = get_anonymization_salt(date_obj)
    hash_id = hashlib.sha224(salt.encode('utf-8'))
    hash_id = hash_id.hexdigest()
    return hash_id

if __name__ == '__main__':
    main()
