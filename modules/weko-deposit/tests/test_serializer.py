# .tox/c1/bin/pytest --cov=weko_deposit tests/test_serializer.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
# def file_uploaded_owner(created_user_id=0, updated_user_id=0):
from unittest import mock
from weko_deposit.serializer import file_uploaded_owner
from unittest.mock import patch
import pytest
from  werkzeug.exceptions import NotFound

def test_file_uploaded_owner(app,db,users):
    with patch('weko_deposit.serializer.weko_logger') as mock_logger:
        assert file_uploaded_owner(users[1]['id'], users[1]['id']) == {
            'created_user': {
                'user_id': 0,
                'username': '',
                'displayname': '',
                'email': ''
            },
            'updated_user': {
                'user_id': 0,
                'username': '',
                'displayname': '',
                'email': ''
            }
        }
        mock_logger.assert_called_once_with(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with patch('weko_deposit.serializer.weko_logger') as mock_logger:

            # no created_user_id
            with pytest.raises(NotFound):
                file_uploaded_owner()
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER',branch="current_user.is_authenticated is True")
            mock_logger.asset_any_call(key='WEKO_COMMON_RETURN_VALUE', value=None)
            mock_logger.reset_mock()

            # found created_user and updated_user
            assert file_uploaded_owner(users[1]['id'],users[1]['id'])=={
                'created_user': {
                    'user_id': users[1]['id'],
                    'username': '',
                    'displayname': '',
                    'email': users[1]['email']
                    },
                'updated_user': {
                    'user_id': users[1]['id'],
                    'username': '',
                    'displayname': '',
                    'email': users[1]['email']
                    }}
            assert mock_logger.call_count == 2
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER',branch="current_user.is_authenticated is True")
            mock_logger.assert_any_call(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)
            mock_logger.reset_mock()

            # Could not find a user corresponding to the specified user ID.
            with pytest.raises(NotFound):
                file_uploaded_owner(created_user_id=users[1]['id'])
            assert mock_logger.call_count == 1
            mock_logger.assert_any_call(key='WEKO_COMMON_IF_ENTER',branch="current_user.is_authenticated is True")
            mock_logger.reset_mock()

            # could not find updated_user
            with pytest.raises(NotFound):
                file_uploaded_owner(updated_user_id=users[1]['id'])
            mock_logger.assert_called_once_with(key='WEKO_COMMON_IF_ENTER',branch="current_user.is_authenticated is True")
            mock_logger.reset_mock()

    #mock_current_user.is_authenticated = False
    with patch('weko_deposit.serializer.weko_logger') as mock_logger:
        assert file_uploaded_owner(users[1]['id'], users[1]['id']) == {
            'created_user': {
                'user_id': 0,
                'username': '',
                'displayname': '',
                'email': ''
            },
            'updated_user': {
                'user_id': 0,
                'username': '',
                'displayname': '',
                'email': ''
            }
        }
    mock_logger.assert_called_once_with(key='WEKO_COMMON_RETURN_VALUE', value=mock.ANY)


def test_file_uploaded_owner_with_userprofile(app,db,users,db_userprofile):

    # user upload file
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with patch('weko_deposit.serializer.weko_logger') as mock_logger:
            assert file_uploaded_owner(users[1]['id'],users[1]['id'])=={
                'created_user': {
                    'user_id': users[1]['id'],
                    'username': db_userprofile[users[1]['email']]._username,
                    'displayname': db_userprofile[users[1]['email']]._displayname,
                    'email': users[1]['email']
                    },
                'updated_user': {
                    'user_id': users[1]['id'],
                    'username': db_userprofile[users[1]['email']]._username,
                    'displayname': db_userprofile[users[1]['email']]._displayname,
                    'email': users[1]['email']}}

    # created_user uploads updated_user files
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert file_uploaded_owner(users[1]['id'],users[0]['id'])=={
            'created_user': {
                'user_id': users[1]['id'],
                'username': db_userprofile[users[1]['email']]._username,
                'displayname': db_userprofile[users[1]['email']]._displayname,
                'email': users[1]['email']
                },
            'updated_user': {
                'user_id': users[0]['id'],
                'username': '',
                'displayname': '',
                'email': users[0]['email']
                }}

    # created_user uploads updated_user files
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert file_uploaded_owner(users[0]['id'],users[1]['id'])=={
            'created_user': {
                'user_id': users[0]['id'],
                'username': '',
                'displayname': '',
                'email': users[0]['email']
                },
            'updated_user': {
                'user_id': users[1]['id'],
                'username': db_userprofile[users[1]['email']]._username,
                'displayname': db_userprofile[users[1]['email']]._displayname,
                'email': users[1]['email']
                }}


