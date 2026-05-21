import json
import os
import pathlib
import subprocess

import pytest
import yaml
from box import Box
from bs4 import BeautifulSoup
from requests import session

from contextlib import closing

from helper.config import DATABASE, USERS, SKIP_HOOK_MARK
from helper.common.connect_helper import connect_db, connect_redis

with open('test/config.yaml', 'r') as f:
    conf = yaml.safe_load(f)


@pytest.fixture
def login_sysadmin():
    """ Log in as System Administrator

    Returns:
        Box: cookie and csrf_token
    """
    sysadmin = USERS['sysadmin']
    return login(sysadmin['email'], sysadmin['password'])


@pytest.fixture
def login_repoadmin():
    """ Log in as Repository Administrator

    Returns:
        Box: cookie and csrf_token
    """
    repoadmin = USERS['repoadmin']
    return login(repoadmin['email'], repoadmin['password'])


@pytest.fixture
def login_comadmin():
    """ Log in as Community Administrator

    Returns:
        Box: cookie and csrf_token
    """
    comadmin = USERS['comadmin']
    return login(comadmin['email'], comadmin['password'])


@pytest.fixture
def login_contributor():
    """ Log in as Contributor

    Returns:
        Box: cookie and csrf_token
    """
    contributor = USERS['contributor']
    return login(contributor['email'], contributor['password'])


@pytest.fixture
def login_user():
    """ Log in as user who has no role

    Returns:
        Box: cookie and csrf_token
    """
    user = USERS['user']
    return login(user['email'], user['password'])


@pytest.fixture
def mail_settings():
    """ Set mail settings for testing"""
    # Connect to database
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cur:
            try:
                # Get mail settings
                cur.execute('SELECT * FROM mail_config')
                mail_config = cur.fetchone()
                if mail_config:
                    id = mail_config[0]
                    cur.execute(
                        'UPDATE mail_config SET mail_server = %s, mail_port = %s, ' \
                        'mail_use_tls = %s, mail_use_ssl = %s, mail_username = %s, ' \
                        'mail_password = %s, mail_local_hostname = %s, mail_default_sender = %s WHERE id = %s',
                        (DATABASE['host'], 25, False, False, '', '', '', 'wekosoftware@nii.ac.jp', id))
                else:
                    cur.execute(
                        'INSERT INTO mail_config (mail_server, mail_port, mail_use_tls, ' \
                        'mail_use_ssl, mail_username, mail_password, mail_local_hostname, ' \
                        'mail_default_sender) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (DATABASE['host'], 25, False, False, '', '', '', 'wekosoftware@nii.ac.jp'))
                conn.commit()
            except Exception as e:
                print('Error setting mail settings:', e)
                raise e
    yield None
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cur:
            try:
                # Reset mail settings to default
                if mail_config:
                    cur.execute(
                        'UPDATE mail_config SET mail_server = %s, mail_port = %s, ' \
                        'mail_use_tls = %s, mail_use_ssl = %s, mail_username = %s, ' \
                        'mail_password = %s, mail_local_hostname = %s, mail_default_sender = %s WHERE id = %s',
                        (mail_config[1], mail_config[2], mail_config[3], mail_config[4],
                         mail_config[5], mail_config[6], mail_config[7], mail_config[8], id))
                else:
                    cur.execute('DELETE FROM mail_config')
                conn.commit()
            except Exception as e:
                print('Error getting mail settings:', e)
                raise e


def login(mail, password):
    """Log in

    Args:
        mail(str): email address
        password(str): password

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
    """Prepare records for testing"""
    with closing(connect_db()) as conn:
        with closing(conn.cursor()) as cur:
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


def delete_item_documents():
    """Delete all documents from item index in OpenSearch"""
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
    """Delete all documents from author index in OpenSearch"""
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


def delete_redis_values():
    """Delete all values in Redis databases used for testing"""
    conn_0 = connect_redis(db=0)
    conn_0.flushdb()
    conn_0.connection_pool.disconnect()

    conn_4 = connect_redis(db=4)
    conn_4.flushdb()
    conn_4.connection_pool.disconnect()

def pytest_tavern_beta_before_every_test_run(test_dict, variables):
    """Run before every test

    Args:
        test_dict(dict): test information written in yaml
        variables(dict): information on executed fixtures
    """
    test_marks = test_dict.get("marks", [])
    if SKIP_HOOK_MARK in test_marks:
        return

    test_name = test_dict.get("test_name", "")
    if test_name == "マッピング画面表示_アイテムタイプ0件":
        # テーブルtruncateだけ実行
        with open('prepare_data/truncate_tables.sql', 'r', encoding='utf-8') as f:
            script = f.read()
            with closing(connect_db()) as conn:
                with closing(conn.cursor()) as cur:
                    cur.execute(script)
                    conn.commit()
    else:
        # Prepare records
        prepare_records()

        # Delete all documents from item index in OpenSearch
        delete_item_documents()

        # Delete all documents from author index in OpenSearch
        delete_author_documents()

        # Delete all values in Redis databases used for testing
        delete_redis_values()

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
