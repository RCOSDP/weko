from invenio_stats import current_stats
from invenio_stats.utils import get_anonymization_salt
from datetime import datetime
import hashlib
import random
import settings
import uuid

event_type = 'search'

def main():
    for i in range(settings.SEARCH_LIMIT):
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

    ip_address = '{}.{}.{}.{}'.format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255))

    search_key = chr(random.randint(97, 122)) + chr(random.randint(97, 122))

    search_detail = {
        "search_key": search_key,
        "search_type": random.randint(0, 1)
    }

    doc_event = dict(
        timestamp=event_date,
        unique_session_id=get_hash_id(date),
        referrer='https://localhost/',
        country=settings.COUNTRYS[random.randint(0, 100) % len(settings.COUNTRYS)],
        is_robot=False,
        is_restricted=False,
        site_license_flag=False,
        site_license_name=None,
        search_detail=search_detail,
        visitor_id=get_hash_id(date)
    )
    doc_event = build_unique_id(doc_event)

    current_stats.publish(event_type, [doc_event])


def build_unique_id(doc):
    """Build unique identifier."""
    key = '{0}_{1}_{2}_{3}'.format(
        doc['search_detail']['search_key'],
        doc['search_detail']['search_type'],
        doc['site_license_name'],
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
