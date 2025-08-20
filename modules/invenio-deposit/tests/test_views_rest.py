# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Test deposit workflow."""

from __future__ import absolute_import, print_function

import json
from time import sleep
from mock import patch

import pytest
from flask import url_for
from flask_security import url_for_security
from invenio_accounts.testutils import login_user_via_view, login_user_via_session
from invenio_db import db
from invenio_search import current_search
from six import BytesIO

from invenio_deposit.api import Deposit


def test_publish_merge_conflict(api, es, users, location, deposit,
                                json_headers, fake_schemas):
    """Test publish with merge conflicts."""
    with api.test_request_context():
        with api.test_client() as client:
            user_info = dict(email=users[0]['email'], password='tester')
            # login
            res = client.post(url_for_security('login'), data=user_info)

            # create a deposit
            deposit = Deposit.create({"metadata": {
                "title": "title-1",
            }})
            deposit.commit()
            db.session.commit()
            # publish
            deposit.publish()
            db.session.commit()
            # # edit
            # deposit = deposit.edit()
            # db.session.commit()
            # # simulate a externally modification
            # rid, record = deposit.fetch_published()
            # rev_id = record.revision_id
            # record.update({'metadata': {
            #     "title": "title-2.1",
            # }})
            # record.commit()
            # db.session.commit()
            # assert rev_id != record.revision_id
            # # edit again and check the merging
            # deposit.update({"metadata": {
            #     "title": "title-2.2",
            # }})
            # deposit.commit()

            # current_search.flush_and_refresh('_all')

            # deposit_id = deposit.pid.pid_value
            # res = client.post(
            #     url_for('invenio_deposit_rest.depid_actions',
            #             pid_value=deposit_id, action='publish'),
            # )
            # assert res.status_code == 409


# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_views_rest.py::test_edit_deposit_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
@pytest.mark.parametrize('user_info,status', [
    # anonymous user
    (None, 401),
    # owner
    (dict(email='info@inveniosoftware.org', password='tester'), 200),
    # user that not have permissions
    (dict(email='test@inveniosoftware.org', password='tester2'), 403),
])
def test_edit_deposit_users(api, es, users, location, deposit,
                            json_headers, user_info, status):
    """Test edit deposit by the owner."""
    deposit_id = deposit['_deposit']['id']
    with api.test_request_context():
        with api.test_client() as client:
            if user_info:
                # login
                res = client.post(url_for_security('login'), data=user_info)
            res = client.put(
                url_for('invenio_deposit_rest.depid_item',
                        pid_value=deposit_id),
                data=json.dumps({"title": "bar"}),
                headers=json_headers
            )
            assert res.status_code == status


def test_edit_deposit_by_good_oauth2_token(api, es, users, location,
                                           deposit, write_token_user_1,
                                           oauth2_headers_user_1):
    """Test edit deposit with a correct oauth2 token."""
    deposit_id = deposit['_deposit']['id']
    with api.test_request_context():
        # with oauth2
        with api.test_client() as client:
            res = client.put(
                url_for('invenio_deposit_rest.depid_item',
                        pid_value=deposit_id),
                data=json.dumps({"title": "bar"}),
                headers=oauth2_headers_user_1
            )
            assert res.status_code == 200


def test_edit_deposit_by_bad_oauth2_token(api, es, users, location,
                                          deposit, write_token_user_2,
                                          oauth2_headers_user_2):
    """Test edit deposit with a wrong oauth2 token."""
    deposit_id = deposit['_deposit']['id']
    with api.test_request_context():
        # with oauth2
        with api.test_client() as client:
            res = client.put(
                url_for('invenio_deposit_rest.depid_item',
                        pid_value=deposit_id),
                data=json.dumps({"title": "bar"}),
                headers=oauth2_headers_user_2
            )
            assert res.status_code == 403

# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_views_rest.py::test_delete_deposit_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
@pytest.mark.parametrize('user_info,status', [
    # anonymous user
    (None, 401),
    # owner
    (dict(email='info@inveniosoftware.org', password='tester'), 204),
    # user that not have permissions
    (dict(email='test@inveniosoftware.org', password='tester2'), 403),
])
def test_delete_deposit_users(api, es, users, location, deposit,
                              json_headers, user_info, status):
    """Test delete deposit by users."""
    deposit_id = deposit['_deposit']['id']
    with api.test_request_context():
        with api.test_client() as client:
            if user_info:
                # login
                res = client.post(url_for_security('login'), data=user_info)
            res = client.delete(
                url_for('invenio_deposit_rest.depid_item',
                        pid_value=deposit_id),
                data=json.dumps({"title": "bar"}),
                headers=json_headers
            )
            assert res.status_code == status

# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_views_rest.py::test_links_html_link_missing -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
def test_links_html_link_missing(api, es, location, fake_schemas,
                                 users, json_headers):
    """Test if the html key from links is missing."""
    api.config['DEPOSIT_UI_ENDPOINT'] = None

    with api.test_request_context():
        with api.test_client() as client:
            login_user_via_view(
                client,
                users[0]['email'],
                'tester',
            )
            # try create deposit as logged in user
            res = client.post(url_for('invenio_deposit_rest.depid_list'),
                              data=json.dumps({}), headers=json_headers)
            assert res.status_code == 403

            data = json.loads(res.data.decode('utf-8'))
            assert data == {'message': "You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.", 'status': 403}


def test_delete_deposit_by_good_oauth2_token(api, es, users, location,
                                             deposit, write_token_user_1,
                                             oauth2_headers_user_1):
    """Test delete deposit with a good oauth2 token."""
    deposit_id = deposit['_deposit']['id']
    with api.test_request_context():
        # with oauth2
        with api.test_client() as client:
            res = client.delete(
                url_for('invenio_deposit_rest.depid_item',
                        pid_value=deposit_id),
                data=json.dumps({"title": "bar"}),
                headers=oauth2_headers_user_1
            )
            assert res.status_code == 204


def test_delete_deposit_by_bad_oauth2_token(api, es, users, location,
                                            deposit, write_token_user_2,
                                            oauth2_headers_user_2):
    """Test delete deposit with a bad oauth2 token."""
    deposit_id = deposit['_deposit']['id']
    with api.test_request_context():
        # with oauth2
        with api.test_client() as client:
            res = client.delete(
                url_for('invenio_deposit_rest.depid_item',
                        pid_value=deposit_id),
                data=json.dumps({"title": "bar"}),
                headers=oauth2_headers_user_2
            )
            assert res.status_code == 403

# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_views_rest.py::test_deposition_file_operations -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
def test_deposition_file_operations(api, es, location, users,
                                    write_token_user_1, pdf_file, pdf_file2,
                                    pdf_file2_samename, oauth2_headers_user_1):
    """Test deposit file operations."""
    with api.test_request_context():
        with api.test_client() as client:
            # create deposit
            res = client.post(url_for('invenio_deposit_rest.depid_list'),
                              data=json.dumps({}),
                              headers=oauth2_headers_user_1)
            assert res.status_code == 403
            data = json.loads(res.data.decode('utf-8'))
            # deposit_id = data['metadata']['_deposit']['id']
            assert data == {'message': "You don't have the permission to access the requested resource. It is either read-protected or not readable by the server.", 'status': 403}

            # sleep(2)

            # # Upload a file
            # res = client.post(
            #     url_for('invenio_deposit_rest.depid_files',
            #             pid_value=deposit_id),
            #     data=pdf_file,
            #     content_type='multipart/form-data',
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 201
            # data = json.loads(res.data.decode('utf-8'))
            # assert data['filename'] == pdf_file['name']
            # assert data['id']
            # assert data['checksum']
            # assert data['filesize']
            # file_data = json.loads(res.data.decode('utf-8'))

            # # Upload another file
            # res = client.post(
            #     url_for('invenio_deposit_rest.depid_files',
            #             pid_value=deposit_id),
            #     data=pdf_file2,
            #     content_type='multipart/form-data',
            #     headers=oauth2_headers_user_1
            # )
            # file_data2 = json.loads(res.data.decode('utf-8'))
            # assert res.status_code == 201

            # # Upload another file with identical name
            # res = client.post(
            #     url_for('invenio_deposit_rest.depid_files',
            #             pid_value=deposit_id),
            #     data=pdf_file2_samename,
            #     content_type='multipart/form-data',
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 400

            # # Get file info
            # res = client.get(url_for(
            #     'invenio_deposit_rest.depid_file',
            #     pid_value=deposit_id,
            #     key=file_data['filename']),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 200
            # get_file = json.loads(res.data.decode('utf-8'))
            # assert file_data == get_file

            # # Get non-existing file
            # res = client.get(url_for(
            #     'invenio_deposit_rest.depid_file',
            #     pid_value=deposit_id,
            #     key='bad-key'),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 404

            # # Delete non-existing file
            # res = client.delete(
            #     url_for(
            #         'invenio_deposit_rest.depid_file',
            #         pid_value=deposit_id,
            #         key='bad-key',
            #     ),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 404

            # # Get list of files
            # res = client.get(
            #     url_for(
            #         'invenio_deposit_rest.depid_files',
            #         pid_value=deposit_id
            #     ),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert len(data) == 2

            # # sort ids
            # invalid_files_list = list(map(
            #     lambda x: {'filename': x['filename']},
            #     data
            # ))
            # id_files_list = list(map(lambda x: {'id': x['id']}, data))
            # id_files_list.reverse()

            # # Sort files - invalid query
            # res = client.put(
            #     url_for('invenio_deposit_rest.depid_files',
            #             pid_value=deposit_id),
            #     data=json.dumps(invalid_files_list),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 400

            # # Sort files - valid query
            # res = client.put(
            #     url_for('invenio_deposit_rest.depid_files',
            #             pid_value=deposit_id),
            #     data=json.dumps(id_files_list),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert len(data) == 2
            # assert data[0]['id'] == id_files_list[0]['id']
            # assert data[1]['id'] == id_files_list[1]['id']

            # # Delete a file
            # res = client.delete(
            #     url_for(
            #         'invenio_deposit_rest.depid_file',
            #         pid_value=deposit_id,
            #         key=file_data['filename']
            #     ),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 204

            # # Get list of files
            # res = client.get(
            #     url_for(
            #         'invenio_deposit_rest.depid_files',
            #         pid_value=deposit_id
            #     ),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert len(data) == 1

            # # Rename file
            # res = client.put(
            #     url_for('invenio_deposit_rest.depid_file',
            #             pid_value=deposit_id,
            #             key=file_data2['filename']),
            #     data=json.dumps({'filename': 'another_test.pdf'}),
            #     headers=oauth2_headers_user_1
            # )
            # data_rename = json.loads(res.data.decode('utf-8'))
            # assert res.status_code == 200
            # assert file_data2['id'] == data_rename['id']
            # assert data_rename['filename'] == 'another_test.pdf'

            # # Bad renaming
            # test_cases = [
            #     dict(name="another_test.pdf"),
            #     dict(filename="../../etc/passwd"),
            # ]
            # for test_case in test_cases:
            #     res = client.put(
            #         url_for('invenio_deposit_rest.depid_file',
            #                 pid_value=deposit_id,
            #                 key=data_rename['filename']),
            #         data=json.dumps(test_case),
            #         headers=oauth2_headers_user_1
            #     )
            #     assert res.status_code == 400

            # # Delete resource again
            # res = client.delete(
            #     url_for('invenio_deposit_rest.depid_item',
            #             pid_value=deposit_id),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 204

            # # No files any more
            # res = client.get(
            #     url_for(
            #         'invenio_deposit_rest.depid_files',
            #         pid_value=deposit_id
            #     ),
            #     headers=oauth2_headers_user_1
            # )
            # assert res.status_code == 410

# .tox/c1/bin/pytest --cov=invenio_deposit tests/test_views_rest.py::test_simple_rest_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-deposit/.tox/c1/tmp
def test_simple_rest_flow(app, test_client, api, es, location, fake_schemas, users,
                          json_headers):
    """Test simple flow using REST API."""
    api.config['RECORDS_REST_ENDPOINTS']['recid'][
        'read_permission_factory_imp'] = \
        'invenio_records_rest.utils:allow_all'
    api.config['RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY'] = \
        'invenio_records_rest.utils:allow_all'
    user_mail = users[0]['email']

    with api.test_request_context():
        with api.test_client() as client:
            # try create deposit as anonymous user (failing)
            res = client.post(url_for('invenio_deposit_rest.depid_list'),
                              data=json.dumps({}), headers=json_headers)
            assert res.status_code == 401

            # login
            client.post(url_for_security('login'), data=dict(
                email=user_mail,
                password="tester"
            ))

            # try create deposit as logged in user
            res = client.post(url_for('invenio_deposit_rest.depid_list'),
                              data=json.dumps({}), headers=json_headers)
            assert res.status_code == 403

            # data = json.loads(res.data.decode('utf-8'))
            # deposit = data['metadata']
            # links = data['links']

            # # Check if links['html'] exists
            # assert 'html' in links

            # sleep(1)

            # # Upload first file:
            # content = b'# Hello world!\nWe are here.'
            # filename = 'test.json'
            # real_filename = 'real_test.json'
            # file_to_upload = (BytesIO(content), filename)
            # with patch("invenio_deposit.views.rest.db.session.commit", side_effect=Exception('')):
            #     res = client.post(
            #         links['files'],
            #         data={'file': file_to_upload, 'name': real_filename},
            #         content_type='multipart/form-data',
            #     )
            #     assert res.status_code == 400

            # content = b'# Hello world!\nWe are here.'
            # filename = 'test.json'
            # real_filename = 'real_test.json'
            # file_to_upload = (BytesIO(content), filename)
            # res = client.post(
            #     links['files'],
            #     data={'file': file_to_upload, 'name': real_filename},
            #     content_type='multipart/form-data',
            # )
            # assert res.status_code == 201
            # data = json.loads(res.data.decode('utf-8'))
            # file_1 = data['id']

            # # Check number of files:
            # res = client.get(links['files'])
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert 1 == len(data)

            # deposit_1 = dict(**deposit)
            # deposit_1['title'] = 'Revision 1'

            # res = client.put(links['self'], data=json.dumps(deposit_1),
            #                  headers=json_headers)
            # data = json.loads(res.data.decode('utf-8'))
            # assert res.status_code == 200

            # content = b'Second file'
            # filename = 'second.json'
            # real_filename = 'real_second.json'
            # file_to_upload = (BytesIO(content), filename)
            # res = client.post(
            #     links['files'],
            #     data={'file': file_to_upload, 'name': real_filename},
            #     content_type='multipart/form-data',
            # )
            # assert res.status_code == 201
            # data = json.loads(res.data.decode('utf-8'))
            # file_2 = data['id']

            # # Ensure the order:
            # with patch("invenio_deposit.views.rest.db.session.commit", side_effect=Exception('')):
            #     res = client.put(links['files'], data=json.dumps([
            #         {'id': file_1}, {'id': file_2}
            #     ]))
            #     assert res.status_code == 400

            # res = client.put(links['files'], data=json.dumps([
            #     {'id': file_1}, {'id': file_2}
            # ]))
            # assert res.status_code == 200

            # # Check number of files:
            # res = client.get(links['files'])
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert 2 == len(data)
            # assert file_1 == data[0]['id']
            # assert file_2 == data[1]['id']

            # res = client.post(links['publish'], data=None,
            #                   headers=json_headers)
            # assert res.status_code == 200

            # # Check that the published record is created:
            # data = json.loads(res.data.decode('utf-8'))
            # deposit_published = data['metadata']
            # record_url = url_for(
            #     'invenio_records_rest.{0}_item'.format(
            #         deposit_published['_deposit']['pid']['type']
            #     ),
            #     pid_value=deposit_published['_deposit']['pid']['value'],
            #     _external=True,
            # )
            # res = client.get(record_url)
            # assert res.status_code == 200

            # # It should not be possible to delete published deposit:
            # res = client.delete(links['self'])
            # assert res.status_code == 403
            # # or a file:
            # res = client.delete(links['files'] + '/' + file_1)
            # assert res.status_code == 403

            # res = client.post(links['edit'], data=None, headers=json_headers)
            # deposit = json.loads(res.data.decode('utf-8'))
            # assert deposit['metadata']['_deposit']['status'] == 'draft'
            # assert res.status_code == 201

            # # It should not be possible to delete
            # previously published deposit:
            # res = client.delete(links['self'])
            # assert res.status_code == 403
            # # or a file:
            # res = client.delete(links['files'] + '/' + file_1)
            # assert res.status_code == 403

            # res = client.put(links['files'], data=json.dumps([
            #     {'id': file_2}, {'id': file_1}
            # ]))
            # assert res.status_code == 200

            # # Check the order of files:
            # res = client.get(links['files'])
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert 2 == len(data)
            # assert file_2 == data[0]['id']
            # assert file_1 == data[1]['id']

            # # After discarding changes the order should be as original:
            # res = client.post(links['discard'], data=None,
            #                   headers=json_headers)
            # assert res.status_code == 201

            # # Check the order of files:
            # res = client.get(links['files'])
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert 2 == len(data)
            # assert file_1 == data[0]['id']
            # assert file_2 == data[1]['id']

            # # Edit again
            # res = client.post(links['edit'], data=None, headers=json_headers)
            # assert res.status_code == 201

            # # Save new title:
            # res = client.patch(links['self'], data=json.dumps([
            #     {'op': 'replace', 'path': '/title',
            #      'value': 'Revision 2'}, ]),
            #     headers=[('Content-Type', 'application/json-patch+json'),
            #              ('Accept', 'application/json')]
            # )
            # data = json.loads(res.data.decode('utf-8'))
            # assert res.status_code == 200

            # res = client.post(links['publish'], data=None,
            #                   headers=json_headers)
            # assert res.status_code == 202

            # # Edited record should contain new title:
            # res = client.get(record_url)
            # assert res.status_code == 200
            # data = json.loads(res.data.decode('utf-8'))
            # assert 'Revision 2' == data['metadata']['title']
