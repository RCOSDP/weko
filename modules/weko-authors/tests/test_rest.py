import copy
import json
from mock import patch

from sqlalchemy.exc import SQLAlchemyError


def url(root, kwargs={}):
    args = [f'{key}={value}' for key, value in kwargs.items()]
    url = f'{root}?{"&".join(args)}' if kwargs else root
    return url


class TestAuthorsREST:
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::TestAuthorsREST::test_get_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_v1(app, client, auth_headers, mocker):
        path = '/v1/authors'
        invalid_version_path = '/v0/authors'

        headers_not_login = auth_headers[0]     # not login
        headers_sysadmin = auth_headers[1]      # OAuth token : sysadmin
        headers_student = auth_headers[2]       # OAuth token : student

        data = {
            'hits': {
                'hits': [
                    {'_source': {'authorIdInfo': [{'authorId': 'test_1'}]}, 'sort': ['1']},
                    {'_source': {'authorIdInfo': [{'authorId': 'test_2'}]}, 'sort': ['2']}
                ],
                'total': 5
            }
        }
        expected = {
            'total_results': 5,
            'count_results': 2,
            'cursor': '2',
            'authors': [
                {'authorIdInfo': [{'authorId': 'test_1'}]},
                {'authorIdInfo': [{'authorId': 'test_2'}]},
            ],
        }
        mock_get_authors = mocker.patch('weko_authors.utils.get_authors', return_value=data)

        # No param
        param = {}
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 200
        assert json.loads(res.get_data()) == expected
        assert res.headers['Cache-Control'] == 'no-store'
        assert res.headers['Pragma'] == 'no-cache'
        assert res.headers['Expires'] == '0'

        mock_get_authors.assert_called_with('', 25, '', '', '', '')

        # Specify parameters #1
        param = {'search_key': 'param1', 'limit': '10', 'page': '2', 'cursor': 'param4', 'sort_key': 'name'}
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 200
        assert json.loads(res.get_data()) == expected
        mock_get_authors.assert_called_with('param1', 10, 2, 'param4', 'authorNameInfo.fullName', 'asc')

        # Specify parameters #2
        param = {'search_key': 'param1', 'limit': '10', 'page': '2', 'cursor': 'param4', 'sort_key': '-name'}
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 200
        assert json.loads(res.get_data()) == expected
        mock_get_authors.assert_called_with('param1', 10, 2, 'param4', 'authorNameInfo.fullName', 'desc')

        # Normal user
        param = {}
        res = client.get(url(path, param), headers=headers_student)
        assert res.status_code == 200
        assert json.loads(res.get_data()) == expected

        data = {
            'hits': {
                'hits': [],
                'total': 0
            }
        }
        expected = {
            'total_results': 0,
            'count_results': 0,
            'cursor': '',
            'authors': [],
        }
        mock_get_authors = mocker.patch('weko_authors.utils.get_authors', return_value=data)

        # No item searched
        param = {}
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 200
        assert json.loads(res.get_data()) == expected

        # Not login : 401
        param = {}
        res = client.get(url(path, param), headers=headers_not_login)
        assert res.status_code == 401

        # Invalid version : 400
        param = {}
        res = client.get(url(invalid_version_path, param), headers=headers_sysadmin)
        assert res.status_code == 400

        # limit is not a number
        param = {'limit': 'test_string'}
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 400

        # page is not a number
        param = {'page': 'test_string'}
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 400

        # Invalid sort key
        param = {'sort_key': 'test_string'}
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 400

        # Error occurred in get_authors : 500
        with patch('weko_authors.utils.get_authors', side_effect=SQLAlchemyError('test_error')):
            param = {}
            res = client.get(url(path, param), headers=headers_sysadmin)
            assert res.status_code == 500


class TestAuthorREST:
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_rest.py::TestAuthorREST::test_get_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_v1(app, client, authors, auth_headers, mocker):
        path = '/v1/authors/1'
        invalid_version_path = '/v0/authors/1'
        invalid_author_path = '/v1/authors/100'

        headers_not_login = auth_headers[0]     # not login
        headers_sysadmin = auth_headers[1]      # OAuth token : sysadmin
        headers_student = auth_headers[2]       # OAuth token : student

        data = {
            'hits': {
                'hits': [
                    {'_source': {'authorIdInfo': [{'authorId': 'test_1'}]}, 'sort': ['1']},
                ],
                'total': 1
            }
        }
        expected = {'authorIdInfo': [{'authorId': 'test_1'}]}

        mocker.patch('weko_authors.utils.get_author_by_pk_id', return_value=data)

        # Normal
        res = client.get(url(path), headers=headers_sysadmin)
        assert res.status_code == 200
        assert json.loads(res.get_data()) == expected

        etag = res.headers['Etag']
        last_modified = res.headers['Last-Modified']

        # Normal user
        res = client.get(url(path), headers=headers_student)
        assert res.status_code == 200
        assert json.loads(res.get_data()) == expected

        # Check Etag
        headers = copy.deepcopy(headers_sysadmin)
        headers.append(('If-None-Match', etag))
        res = client.get(url(path), headers=headers)
        assert res.status_code == 304

        # Check Last-Modified
        headers = copy.deepcopy(headers_sysadmin)
        headers.append(('If-Modified-Since', last_modified))
        res = client.get(url(path), headers=headers)
        assert res.status_code == 304

        # Not login : 401
        res = client.get(url(path), headers=headers_not_login)
        assert res.status_code == 401

        # Invalid version
        res = client.get(url(invalid_version_path), headers=headers_sysadmin)
        assert res.status_code == 400

        # Author not found
        res = client.get(url(invalid_author_path), headers=headers_sysadmin)
        assert res.status_code == 404

        with patch('weko_authors.utils.get_author_by_pk_id', side_effect=SQLAlchemyError('test_error')):
            res = client.get(url(path), headers=headers_sysadmin)
            assert res.status_code == 500
