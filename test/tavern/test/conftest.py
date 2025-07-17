from box import Box
from bs4 import BeautifulSoup
import json
import os
import pathlib
import psycopg2
import pytest
from requests import session
import subprocess
import yaml

from helper.config import DATABASE, USERS

with open('test/config.yaml', 'r') as f:
    conf = yaml.safe_load(f)

@pytest.fixture
def login_sysadmin():
    """ Log in as System Administrator
    
    Args:
        None
    
    Returns:
        Box: cookie and csrf_token
    """
    sysadmin = USERS['sysadmin']
    return login(sysadmin['email'], sysadmin['password'])

@pytest.fixture
def login_repoadmin():
    """ Log in as Repository Administrator
    
    Args:
        None
        
    Returns:
        Box: cookie and csrf_token
    """
    repoadmin = USERS['repoadmin']
    return login(repoadmin['email'], repoadmin['password'])

@pytest.fixture
def login_comadmin():
    """ Log in as Community Administrator

    Args:
        None

    Returns:
        Box: cookie and csrf_token
    """
    comadmin = USERS['comadmin']
    return login(comadmin['email'], comadmin['password'])

@pytest.fixture
def login_contributor():
    """ Log in as Contributor

    Args:
        None

    Returns:
        Box: cookie and csrf_token
    """
    contributor = USERS['contributor']
    return login(contributor['email'], contributor['password'])

@pytest.fixture
def login_user():
    """ Log in as user who has no role

    Args:
        None

    Returns:
        Box: cookie and csrf_token
    """
    user = USERS['user']
    return login(user['email'], user['password'])

@pytest.fixture
def mail_settings():
    """ Set mail settings for testing

    Args:
        None

    Returns:
        None
    """
    # Connect to database
    conn = psycopg2.connect(
        dbname=DATABASE['dbname'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        host=DATABASE['host'],
        port=DATABASE['port'],
    )
    cur = conn.cursor()
    try:
        # Get mail settings
        cur.execute('SELECT * FROM mail_config')
        mail_config = cur.fetchone()
        if mail_config:
            id = mail_config[0]
            cur.execute('UPDATE mail_config SET mail_server = %s, mail_port = %s, mail_use_tls = %s, mail_use_ssl = %s, mail_username = %s, mail_password = %s, mail_local_hostname = %s, mail_default_sender = %s WHERE id = %s',
                        (DATABASE['host'], 25, False, False, '', '', '', 'wekosoftware@nii.ac.jp', id))
        else:
            cur.execute('INSERT INTO mail_config (mail_server, mail_port, mail_use_tls, mail_use_ssl, mail_username, mail_password, mail_local_hostname, mail_default_sender) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (DATABASE['host'], 25, False, False, '', '', '', 'wekosoftware@nii.ac.jp'))
        conn.commit()
        cur.close()
        conn.close()
        yield None
        conn = psycopg2.connect(
            dbname=DATABASE['dbname'],
            user=DATABASE['user'],
            password=DATABASE['password'],
            host=DATABASE['host'],
            port=DATABASE['port'],
        )
        cur = conn.cursor()
        # Reset mail settings to default
        if mail_config:
            cur.execute('UPDATE mail_config SET mail_server = %s, mail_port = %s, mail_use_tls = %s, mail_use_ssl = %s, mail_username = %s, mail_password = %s, mail_local_hostname = %s, mail_default_sender = %s WHERE id = %s',
                        (mail_config[1], mail_config[2], mail_config[3], mail_config[4], mail_config[5], mail_config[6], mail_config[7], mail_config[8], id))
        else:
            cur.execute('DELETE FROM mail_config')
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print('Error getting mail settings:', e)
        raise e

def login(mail, password):
    """ Log in

    Args:
        mail (str): email address
        password (str): password

    Returns:
        Box: cookie and csrf_token
    """
    with session() as s:
        # Go to login page to get csrf token
        url = conf['variables']['host']
        res = s.get(url + '/login/', verify=False)
        soup = BeautifulSoup(res.content, 'html.parser')
        csrf = soup.find(id='csrf_token')['value']

        # Login and get cookie
        data = {
            'email': mail,
            'password': password,
            'next': '/',
            'csrf_token': csrf
        }
        res = s.post(url + '/login/', data=data, verify=False)
        return Box({
            'cookie': s.cookies.get_dict(),
            'csrf_token': csrf
        })

def prepare_records():
    """ Prepare records for testing

    Args:
        None

    Returns:
        None
    """
    # Connect to database
    conn = psycopg2.connect(
        dbname=DATABASE['dbname'],
        user=DATABASE['user'],
        password=DATABASE['password'],
        host=DATABASE['host'],
        port=DATABASE['port'],
    )
    cur = conn.cursor()

    try:
        # Prepare remove temp files
        cur.execute('SELECT uri FROM files_files')
        tmp_files = cur.fetchall()

        cur.execute('SELECT uri FROM files_location')
        tmp_locations = cur.fetchall()

        remove_directories = []
        for f in tmp_files:
            for l in tmp_locations:
                if f[0].startswith(l[0]):
                    location_level = l[0].count('/')
                    if l[0].startswith('/'):
                        location_level += 1
                    remove_directories.append('/'.join(f[0].split('/')[:location_level + 1]))

        # Truncate tables
        with open('prepare_data/truncate_tables.sql', 'r', encoding='utf-8') as f:
            script = f.read()
            cur.execute(script)
        
        # Insert records
        with open('prepare_data/execute_order.txt', 'r', encoding='utf-8') as f:
            order = f.read().splitlines()
            for o in order:
                with open('prepare_data/' + o, 'r', encoding='utf-8') as f:
                    script = f.read()
                    cur.execute(script)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def delete_item_documents():
    """ Delete all documents from item index in OpenSearch
    
    Args:
        None

    Returns:
        None
    """
    # Get prefix from environment variable
    prefix = os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1')
    index = prefix + '-weko-item-v1.0.0'
    query = {'query': {'match_all': {}}}
    
    url = conf['variables']['host'].replace('https://', 'http://')
    user = 'admin:{}'.format(os.environ.get('OPENSEARCH_INITIAL_ADMIN_PASSWORD'))
    # Delete all documents from item index in OpenSearch
    result = subprocess.run([
        'curl',
        '-XPOST',
        url + ':29201/' + index + '/_delete_by_query',
        '-H',
        'Content-Type: application/json',
        '-d',
        json.dumps(query),
        # '-ku',
        # user
    ])
    if result.returncode != 0:
        print('Failed to delete all documents from item index in OpenSearch')
        print('stderr: ', result.stderr)
        raise Exception('Failed to delete all documents from item index in OpenSearch') 

def delete_author_documents():
    """ Delete all documents from author index in OpenSearch
    
    Args:
        None

    Returns:
        None
    """
    # Get prefix from environment variable
    prefix = os.environ.get('SEARCH_INDEX_PREFIX', 'tenant1')
    index = prefix + '-authors-author-v1.0.0'
    query = {'query': {'match_all': {}}}
    
    url = conf['variables']['host'].replace('https://', 'http://')
    user = 'admin:{}'.format(os.environ.get('OPENSEARCH_INITIAL_ADMIN_PASSWORD'))
    # Delete all documents from item index in OpenSearch
    result = subprocess.run([
        'curl',
        '-XPOST',
        url + ':29201/' + index + '/_delete_by_query',
        '-H',
        'Content-Type: application/json',
        '-d',
        json.dumps(query),
        # '-ku',
        # user
    ])
    if result.returncode != 0:
        print('Failed to delete all documents from author index in OpenSearch')
        print('stderr: ', result.stderr)
        raise Exception('Failed to delete all documents from author index in OpenSearch') 

def pytest_tavern_beta_before_every_test_run(test_dict, variables):
    """ Run before every test
    
    Args:
        test_dict (dict): test information written in yaml
        variables (dict): information on executed fixtures
        
    Returns:
        None
    """
    # Prepare records
    prepare_records()

    # Delete all documents from item index in OpenSearch
    delete_item_documents()

    # Delete all documents from author index in OpenSearch
    delete_author_documents()

    # Set cookie and csrf_token
    for k in variables.keys():
        if k.startswith('login_'):
            for i in range(len(test_dict['stages'])):
                test_dict['stages'][i]['request']['headers'] = {
                    'Cookie': 'session=' + variables[k]['cookie']['session'],
                    'X-CSRFToken': variables[k]['csrf_token']
                }
    
    # Delete all mail
    check_dir = pathlib.Path('mail')
    for file in check_dir.iterdir():
        if file.is_file():
            file.unlink()
