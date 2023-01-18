# .tox/c1/bin/pytest --cov=weko_deposit tests/test_serializer.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
# def file_uploaded_owner(created_user_id=0, updated_user_id=0):
from weko_deposit.serializer import file_uploaded_owner
from mock import patch
import pytest
from  werkzeug.exceptions import NotFound

def test_file_uploaded_owner(app,db,users):
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        with pytest.raises(NotFound):
            assert file_uploaded_owner()==""
        assert file_uploaded_owner(users[1]['id'],users[1]['id'])=={'created_user': {'user_id': users[1]['id'], 'username': '', 'displayname': '', 'email': users[1]['email']}, 'updated_user': {'user_id': users[1]['id'], 'username': '', 'displayname': '', 'email': users[1]['email']}}
        with pytest.raises(NotFound):
            assert file_uploaded_owner(created_user_id=users[1]['id'])==""
        with pytest.raises(NotFound):
            assert file_uploaded_owner(updated_user_id=users[1]['id'])==""

def test_file_uploaded_owner_with_userprofile(app,db,users,db_userprofile):
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert file_uploaded_owner(users[1]['id'],users[1]['id'])=={'created_user': {'user_id': users[1]['id'], 'username': db_userprofile[users[1]['email']]._username, 'displayname': db_userprofile[users[1]['email']]._displayname, 'email': users[1]['email']}, 'updated_user': {'user_id': users[1]['id'], 'username': db_userprofile[users[1]['email']]._username, 'displayname': db_userprofile[users[1]['email']]._displayname, 'email': users[1]['email']}}
        
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert file_uploaded_owner(users[1]['id'],users[0]['id'])=={'created_user': {'user_id': users[1]['id'], 'username': db_userprofile[users[1]['email']]._username, 'displayname': db_userprofile[users[1]['email']]._displayname, 'email': users[1]['email']}, 'updated_user': {'user_id': users[0]['id'], 'username': '', 'displayname': '', 'email': users[0]['email']}}

    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert file_uploaded_owner(users[0]['id'],users[1]['id'])=={'created_user': {'user_id': users[0]['id'], 'username': '', 'displayname': '', 'email': users[0]['email']}, 'updated_user': {'user_id': users[1]['id'], 'username': db_userprofile[users[1]['email']]._username, 'displayname': db_userprofile[users[1]['email']]._displayname, 'email': users[1]['email']}}
        
   

