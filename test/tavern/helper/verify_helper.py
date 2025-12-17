from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta, timezone
import difflib
from email.header import decode_header
import json
import pprint
from urllib.parse import urlparse, urlunparse

from helper.config import INVENIO_WEB_HOST_NAME
from helper.verify_database_helper import connect_db, compare_db_data

def response_verify_common_response(response, file_name, key):
    """Verify common response

    Args:
        response (requests.models.Response): response from {host}/api/items/validate
        file_name (str): name of the file containing the data to be compared
        key (str): key to access the expected data in the JSON file

    Returns:
        None
    """
    with open('response_data/' + file_name, 'r') as f:
        expect = json.loads(f.read()).get(key)
    
    if expect is None:
        raise ValueError(f"Expected data not found in {file_name}")

    try:
        assert response.json() == expect
    except AssertionError as e:
        assertion_error_handler(e, expect, response.json())

def response_verify_init_response(response, file_name, before_count=0):
    """Verify "{host}/workflow/activity/init"'s response

    Args:
        response (requests.models.Response): response from {host}/workflow/activity/init
        file_name (str): name of the file containing the data to be compared
        before_count (int): number of times the function has been called before this call, used to adjust the redirect URL

    Returns:
        None
    """
    with open('response_data/' + file_name, 'r') as f:
        expect = json.loads(f.read()).get('init')
    
    if not expect:
        raise ValueError(f"Expected data not found in {file_name}")

    now_date = date.today().strftime('%Y%m%d')
    expect['data']['redirect'] = expect['data']['redirect'].format(now_date)

    if before_count > 0:
        before_count_str = str(before_count + 1).zfill(5)
        expect['data']['redirect'] = expect['data']['redirect'].replace('00001', before_count_str)

    try:
        assert response.json() == expect
    except AssertionError as e:
        assertion_error_handler(e, expect, response.json())

def response_verify_iframe_save_model_response(response, file_name):
    """Verify "{host}/items/iframe/model/save"'s response
    
    Args:
        response (requests.models.Response): response from {host}/items/iframe/model/save
        file_name (str): name of the file containing the data to be compared
        
    Returns:
        None
    """
    with open('response_data/' + file_name, 'r') as f:
        expect = json.loads(f.read()).get('iframe_model_save')
    
    now_time = datetime.now(timezone.utc)
    now_time_str = now_time.strftime('%Y-%m-%d %H:%M:%S')
    second_before_time = now_time - timedelta(seconds=1)
    second_before_time_str = second_before_time.strftime('%Y-%m-%d %H:%M:%S')

    expect_now = {
        'code': expect['code'],
        'msg': expect['msg'].format(now_time_str),
    }
    expect_second_before = {
        'code': expect['code'],
        'msg': expect['msg'].format(second_before_time_str),
    }
    try:
        assert response.json() in [expect_now, expect_second_before]
    except AssertionError as e:
        assertion_error_handler(e, expect_now, response.json())

def response_verify_deposits_items_response(response, file_name, host, excepted=[]):
    """Verify "{host}/api/deposits/items"'s response
    
    Args:
        response (requests.models.Response): response from {host}/api/deposits/items
        file_name (str): name of the file containing the data to be compared
        host (str): host name
        excepted (list): list of keys that are expected to be in the response
        
    Returns:
        None
    """
    with open('response_data/' + file_name, 'r') as f:
        expect = json.loads(f.read()).get('deposits_items')
    
    # Replace the host in the expected data
    for k in expect['links']:
        expect['links'][k] = expect['links'][k].format(host)
    
    # Remove the expected keys from the response
    for k in excepted:
        if k in expect['links']:
            del expect['links'][k]
    
    now_time = datetime.now(timezone.utc)
    second_before_time = now_time - timedelta(seconds=2)
    created_time = datetime.strptime(response.json()['created'], '%Y-%m-%dT%H:%M:%S.%f%z')
    
    try:
        assert created_time >= second_before_time and created_time < now_time
        assert response.json()['id'] == expect['id']
        for k in expect['links']:
            if k == 'bucket':
                expect['links'][k].startswith(expect['links'][k])
            else:
                assert response.json()['links'][k] == expect['links'][k]
    except AssertionError as e:
        assertion_error_handler(e, expect, response.json())

def response_verify_records(response, folder_path, activity_id):
    """Verify records
    
    Args:
        response (requests.models.Response): response from {host}/records/{recid}
        folder_path (str): path to the folder containing the tsv files what contain the data to be compared
        activity_id (str): activity id
    
    Returns:
        None
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        # Connect to database
        conn = connect_db()
        cur = conn.cursor()

        cur.execute('SELECT item_id FROM workflow_activity WHERE activity_id = %s', (activity_id,))
        item_id = cur.fetchone()[0]

        cur.execute('SELECT * FROM records_buckets WHERE record_id IN (%s, %s)', (soup.find(id='record_id').text, item_id))
        records_buckets = cur.fetchall()

        # prepare data to replace
        replace_params = {
            'pidstore_pid': {
                'activity_id': activity_id,
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id
            },
            'records_metadata': {
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id,
                'bucket_uuid_2000001': records_buckets[0][1] if records_buckets[0][0] == soup.find(id='record_id').text else records_buckets[1][1],
                'bucket_uuid_2000001.1': records_buckets[0][1] if records_buckets[0][0] == item_id else records_buckets[1][1],
            }
        }

        # prepare column's type conversion params
        type_conversion_params = {
            'pidstore_pid': {
                'id': 'int'
            },
            'records_metadata': {
                'json': 'json',
                'version_id': 'int'
            }
        }
        
        compare_db_data(cur, folder_path, replace_params, type_conversion_params)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(e)
        raise e
    finally:
        cur.close()
        conn.close()

def response_verify_records_with_file(response, folder_path, activity_id, file_metadata):
    """Verify records with file
    
    Args:
        response (requests.models.Response): response from {host}/records/{recid}
        folder_path (str): path to the folder containing the tsv files what contain the data to be compared
        activity_id (str): activity id
        file_metadata (str): file metadata
        
    Returns:
        None"""

    def create_file_metadata(file_metadata, cur=None):
        """Create file metadata
        
        Args:
            file_metadata (str): file metadata
            cur (psycopg2.extensions.cursor): cursor
        
        Returns:
            str: file metadata
        """
        file_metadata_list = list(json.loads(file_metadata).values())[0]
        url = file_metadata_list[0]['url']['url']
        parsed_url = urlparse(url)
        new_url = urlunparse(parsed_url._replace(netloc=INVENIO_WEB_HOST_NAME))
        if cur:
            cur.execute('SELECT version_id FROM files_object WHERE file_id = (SELECT file_id FROM files_object WHERE version_id = %s) AND version_id != %s',
                        (file_metadata_list[0]['version_id'],file_metadata_list[0]['version_id']))
            version_id = cur.fetchone()[0]
            new_url = new_url.replace('2000001', '2000001.1')
            file_metadata_list[0]['version_id'] = version_id
            file_metadata_list[0]['mimetype'] = file_metadata_list[0]['format']
        file_metadata_list[0]['url']['url'] = new_url
        return json.dumps(file_metadata_list)

    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        # Connect to database
        conn = connect_db()
        cur = conn.cursor()

        cur.execute('SELECT item_id FROM workflow_activity WHERE activity_id = %s', (activity_id,))
        item_id = cur.fetchone()[0]

        cur.execute('SELECT * FROM records_buckets WHERE record_id IN (%s, %s)', (soup.find(id='record_id').text, item_id))
        records_buckets = cur.fetchall()

        # prepare data to replace
        replace_params = {
            'pidstore_pid': {
                'activity_id': activity_id,
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id
            },
            'records_metadata': {
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': soup.find(id='record_id').text,
                'uuid_2000001.1': item_id,
                'bucket_uuid_2000001': records_buckets[0][1] if records_buckets[0][0] == soup.find(id='record_id').text else records_buckets[1][1],
                'bucket_uuid_2000001.1': records_buckets[0][1] if records_buckets[0][0] == item_id else records_buckets[1][1],
                'file_metadata_2000001': create_file_metadata(file_metadata),
                'file_metadata_2000001.1': create_file_metadata(file_metadata, cur)
            }
        }

        # prepare column's type conversion params
        type_conversion_params = {
            'pidstore_pid': {
                'id': 'int'
            },
            'records_metadata': {
                'json': 'json',
                'version_id': 'int'
            }
        }
        
        compare_db_data(cur, folder_path, replace_params, type_conversion_params)
        
    except Exception as e:
        print(e)
        raise e
    finally:
        cur.close()
        conn.close()

def response_verify_login(response, id):
    """Verify login response

    Args:
        response (requests.models.Response): response from {host}/login/
        id (int): user id

    Returns:
        None
    """
    try:
        assert int(response.json()['response']['user']['id']) == id
    except AssertionError as e:
        assertion_error_handler(e, {'response': {'user': {'id': id}}}, response.json())

def response_verify_duplicate_item(response, host, file_name, created_count=1):
    """Verify duplicate item response
    
    Args:
        response (requests.models.Response): response from {host}/items/iframe/model/save
        host (str): host name
        file_name (str): name of the file containing the data to be compared
        
    Returns:
        None
    """
    with open('response_data/' + file_name, 'r') as f:
        expect = json.loads(f.read())

    template_link = '{}/records/{}'
    for i in range(1, created_count + 1):
        id = f'2{str(i).zfill(6)}'
        expect['duplicate_links'].append(template_link.format(host, id))
        expect['recid_list'].append(int(id))
    
    result = response.json()
    result['duplicate_links'].sort()
    result['recid_list'].sort()
    expect['duplicate_links'].sort()
    expect['recid_list'].sort()

    try:
        assert result == expect
    except AssertionError as e:
        assertion_error_handler(e, expect, result)

def response_verify_workflow_records(response, folder_path, activity_id, activity_start_time, file_name):
    """Verify workflow records
    
    Args:
        response (requests.models.Response): response from {host}/items/iframe/model/save
        folder_path (str): path to the folder containing the tsv files what contain the data to be compared
        activity_id (str): activity id
        activity_start_time (str): activity start time in 'YYYY-MM-DD HH:MM:SS' format
        file_name (str): name of the file containing the data to be compared
    
    Returns:
        None
    """
    with open('request_params/' + file_name, 'r') as f:
        expect = json.load(f)
    temp_data = {
        'endpoints': {
            'initialization': '/api/deposits/items'
        },
        'files': [],
        'metainfo': expect,
        'weko_link': {
            '1': '10'
        }
    }
    replace_params = {
        'workflow_activity': {
            'activity_id': activity_id,
            'activity_start': activity_start_time,
            'temp_data': json.dumps(temp_data)
        }
    }
    type_conversion_params = {
        'workflow_activity': {
            'id': 'int',
            'workflow_id': 'int',
            'flow_id': 'int',
            'action_id': 'int',
            'activity_login_user': 'int',
            'activity_update_user': 'int',
            'activity_confirm_term_of_use': 'bool',
            'shared_user_id': 'int',
            'extra_info': 'json',
            'action_order': 'int'
        }
    }

    datetime_columns = ['activity_start']

    try:
        conn = connect_db()
        cur = conn.cursor()

        compare_db_data(cur, folder_path, replace_params, type_conversion_params, datetime_columns)
    except Exception as e:
        print(e)
        raise e

def response_verify_temp_data_after_change_author_info(response, creator_key):
    """Verify temporary data after changing author information

    Args:
        response (requests.models.Response): response from {host}/workflow/activity/detail/{activity_id}?status=
        creator_key (str): key for the creator in the response JSON
    
    Returns:
        None
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    invenio_records = soup.find('invenio-records')
    authors = json.loads(invenio_records['record'])[creator_key]
    name_identifiers = authors[0]['nameIdentifiers']
    for name_identifier in name_identifiers:
        if name_identifier['nameIdentifierScheme'] == 'WEKO':
            assert name_identifier['nameIdentifier'] == '1'

def response_verify_changed_data(response, folder_path, activity_id):
    """Verify changed data in the database after an activity
    
    Args:
        response (requests.models.Response): response from {host}/api/deposits/items/{recid}
        folder_path (str): path to the folder containing the tsv files what contain the data to be compared
        activity_id (str): activity id
        
    Returns:
        None"""
    try:
        # Connect to database
        conn = connect_db()
        cur = conn.cursor()

        cur.execute('SELECT item_id FROM workflow_activity WHERE activity_id = %s', (activity_id,))
        item_id = cur.fetchone()[0]

        cur.execute('SELECT bucket_id FROM records_buckets WHERE record_id = %s', (item_id,))
        bucket_id = cur.fetchone()[0]

        replace_params = {
            'records_metadata': {
                'host_name': INVENIO_WEB_HOST_NAME,
                'uuid_2000001': item_id,
                'bucket_uuid_2000001': bucket_id
            }
        }

        # prepare column's type conversion params
        type_conversion_params = {
            'records_metadata': {
                'json': 'json',
                'version_id': 'int'
            }
        }

        compare_db_data(cur, folder_path, replace_params, type_conversion_params)
    except Exception as e:
        print(e)
        raise e
    finally:
        cur.close()
        conn.close()

def verify_approval_mail(response, approval_type, title_key, data):
    """Verify approval mail
    
    Args:
        response (requests.models.Response): response from {host}/workflow/activity/action/{activity_id}/7 or 4
        approval_type (str): type of approval ('request' or 'complete')
        title_key (str): key for the title in the response JSON
        data (str): JSON string containing the data to be verified
        
    Returns:
        None
    """
    data = json.loads(data)
    if len(title_key.split('.')) == 3:
        title = data[title_key.split('.')[0]][int(title_key.split('.')[1])][title_key.split('.')[2]]
    else:
        title = data[title_key.split('.')[0]][title_key.split('.')[1]]

    if approval_type == 'request':
        with open('mail/repoadmin', 'r') as f:
            request_mail = f.readlines()
            subject_idx = 0
            from_idx = 0
            for i, line in enumerate(request_mail):
                if line.startswith('Subject:'):
                    subject_idx = i
                elif line.startswith('From:'):
                    from_idx = i
            subject_list = request_mail[subject_idx:from_idx]
            subject = ''.join(s.replace('\n', '') for s in subject_list).strip()
            decoded_parts = decode_header(subject)
            decoded_subject = ''.join([
                part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
                for part, encoding in decoded_parts
            ])
            colon_idx = decoded_subject.find(':')
            assert decoded_subject[colon_idx + 1:].strip() == f"[Approval Request] Please review and approve the item \"{title}\""
    elif approval_type == 'complete':
        with open('mail/contributor', 'r') as f:
            request_mail = f.readlines()
            subject_idx = 0
            from_idx = 0
            for i, line in enumerate(request_mail):
                if line.startswith('Subject:'):
                    subject_idx = i
                elif line.startswith('From:'):
                    from_idx = i
            subject_list = request_mail[subject_idx:from_idx]
            subject = ''.join(s.replace('\n', '') for s in subject_list).strip()
            decoded_parts = decode_header(subject)
            decoded_subject = ''.join([
                part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
                for part, encoding in decoded_parts
            ])
            colon_idx = decoded_subject.find(':')
            assert decoded_subject[colon_idx + 1:].strip() == f"【Approval Complete】Your item \"{title}\" has been approved"

def assertion_error_handler(e, expect, actual):
    """Handle assertion error and print the difference between expected and actual data.

    Args:
        e (AssertionError): The assertion error raised.
        expect (dict): The expected data.
        actual (dict): The actual data.

    Returns:
        None
    """
    a_str = pprint.pformat(actual)
    b_str = pprint.pformat(expect)
    diff = '\n'.join(difflib.unified_diff(
        a_str.splitlines(), b_str.splitlines(),
        fromfile='actual', tofile='expected', lineterm=''
    ))
    print("差分:\n" + diff)
    raise e