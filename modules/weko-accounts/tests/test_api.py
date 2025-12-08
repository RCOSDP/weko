from logging import exception
import pytest
from datetime import datetime
from mock import patch
from flask import session,current_app
from flask_login.utils import login_user
from invenio_accounts.models import Role, User
from weko_user_profiles.models import UserProfile
from sqlalchemy.exc import SQLAlchemyError
from weko_accounts.models import ShibbolethUser
from weko_accounts.api import ShibUser,get_user_info_by_role_name

#class ShibUser(object):
class TestShibUser:
#    def __init__(self, shib_attr=None):
    def test_init(self,db,users):
        user = users[0]["obj"]
        attr = {
            "shib_eppn":"test_eppn"
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == attr
        assert shibuser.user == None
        assert shibuser.shib_user == None
        
        
#    def _set_weko_user_role(self, roles):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_set_weko_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_set_weko_user_role(self,app,db,users):
        
        role_sysadmin = Role.query.filter_by(name='System Administrator').first()
        role_repoadmin = Role.query.filter_by(name='Repository Administrator').first()
        role_original = Role.query.filter_by(name='Original Role').first()
        
        user = users[6]["obj"]
        attr = {
            "shib_eppn":"test_eppn"
        }
        s_user = ShibbolethUser(weko_uid=user.id,weko_user=user,**attr)
        db.session.add(s_user)
        s_user.shib_roles.append(role_original)
        db.session.commit()
        
        shibuser = ShibUser(attr)
        shibuser.shib_user = s_user
        shibuser.user=user
        
        roles = ['System Administrator','Repository Administrator']
        result = shibuser._set_weko_user_role(roles)
        assert shibuser.user.roles == [role_repoadmin,role_sysadmin]
        assert shibuser.shib_user.shib_roles == [role_sysadmin]
        
        # raise Exception
        error = Exception("test_error")
        with patch("weko_accounts.api.db.session.begin_nested",side_effect=error):
            result = shibuser._set_weko_user_role(roles)
            assert result == error
#    def _get_site_license(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_get_site_license -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_get_site_license(self):
        attr = {
            "shib_eppn":"test_eppn",
            "shib_ip_range_flag":True
        }
        shibuser = ShibUser(attr)
        result = shibuser._get_site_license()
        assert result == True
#    def _create_unknown_roles(self, role_names):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test__create_unknown_roles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test__create_unknown_roles(self, app, users, mocker):
        attr = {
            "shib_eppn":"test_eppn",
        }
        shibuser = ShibUser(attr)

        before_roles = Role.query.all()
        role_names = ['System Administrator']

        # not allow create group
        app.config.update(WEKO_ACCOUNTS_SHIB_ALLOW_CREATE_GROUP_ROLE=False)
        shibuser._create_unknown_roles(role_names)
        assert before_roles == Role.query.all()

        # unknown_roles is not exists
        app.config.update(WEKO_ACCOUNTS_SHIB_ALLOW_CREATE_GROUP_ROLE=True)
        shibuser._create_unknown_roles(role_names)
        assert before_roles == Role.query.all()
        
        # Occurred exception
        role_names = ['System Administrator', 'new_role_1', 'new_role_2', '']
        with patch("weko_accounts.api.db.session.commit",side_effect=Exception):
            shibuser._create_unknown_roles(role_names)
            assert before_roles == Role.query.all()
        
        # Success
        shibuser._create_unknown_roles(role_names)
        assert Role.query.filter_by(name='new_role_1').count() == 1
        assert Role.query.filter_by(name='new_role_2').count() == 1
        assert Role.query.filter_by(name='').count() == 0

#    def get_relation_info(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_get_relation_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_get_relation_info(self,app,db,users):

        user1 = users[0]["obj"]
        user2 = users[1]["obj"]

        attr = {
            "shib_eppn": "test_eppn",
            "shib_mail": None,
            "shib_user_name": None,
            "shib_role_authority_name": None,
            "shib_page_name": None,
            "shib_active_flag": None,
            "shib_ip_range_flag": None,
            "shib_organization": None
        }
        s_user1 = ShibbolethUser(weko_uid=user1.id,weko_user=user1,**attr)
        db.session.add(s_user1)
        db.session.commit()

        # exist shib_eppn,exist shib_user.weko_user,not exist self.user
        # attribute does not exist
        shibuser = ShibUser(attr)
        result = shibuser.get_relation_info()
        assert result.shib_mail == None
        assert result.shib_user_name == None
        assert result.shib_role_authority_name == None
        assert result.shib_page_name == None
        assert result.shib_active_flag == None
        assert result.shib_ip_range_flag == None
        assert result.shib_organization == None

        # attribute exists
        attr = {
            "shib_eppn":"test_eppn",
            "shib_mail":"shib.user@test.org",
            "shib_user_name":"shib name1",
            "shib_role_authority_name":"shib auth",
            "shib_page_name":"shib page",
            "shib_active_flag":"TRUE",
            "shib_ip_range_flag":"TRUE",
            "shib_organization":"shib org"
        }
        shibuser = ShibUser(attr)
        result = shibuser.get_relation_info()
        assert result.shib_mail == "shib.user@test.org"
        assert result.shib_user_name == "shib name1"
        assert result.shib_role_authority_name == "shib auth"
        assert result.shib_page_name == "shib page"
        assert result.shib_active_flag == "TRUE"
        assert result.shib_ip_range_flag == "TRUE"
        assert result.shib_organization == "shib org"

        # not exist shib_eppn,not exist shib_user.weko_user
        attr = {
            "shib_eppn":"",
            "shib_user_name":"shib name2",
            "shib_mail":None,
            "shib_role_authority_name":None,
            "shib_page_name":None,
            "shib_active_flag":None,
            "shib_ip_range_flag":None,
            "shib_organization":None
        }
        s_user2 = ShibbolethUser(**attr)
        db.session.add(s_user2)
        db.session.commit()
        shibuser = ShibUser(attr)
        result = shibuser.get_relation_info()
        assert result == None
        
        # not exist shib_eppn, exist shib_user.weko_user,exist self.user, raise SQLAlchemyError
        s_user2.weko_user = user2
        s_user2.weko_uid = user2.id
        db.session.merge(s_user2)
        db.session.commit()
        shibuser.user = user2
        with patch("weko_accounts.api.db.session.commit",side_effect=SQLAlchemyError):
            with pytest.raises(SQLAlchemyError):
                shibuser.get_relation_info()
#    def check_weko_user(self, account, pwd):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_check_weko_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_check_weko_user(self,app,users):
        user = users[0]["obj"]
        password = user.password_plaintext
        
        # exist wkeo_user, correct password
        shibuser = ShibUser({})
        result = shibuser.check_weko_user(user.email,password)
        assert result == True
        
        # not exist weko_user
        result = shibuser.check_weko_user("not.exist.user@test.org",password)
        assert result == False
        
        # exist weko_user, not correct password
        result = shibuser.check_weko_user(user.email,"wrong passwd")
        assert result == False
#    def bind_relation_info(self, account):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_bind_relation_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_bind_relation_info(self,app,users):
        user = users[0]["email"]
        attr = {
            "shib_eppn":"",
            "shib_mail":"new.sysadmin_mail@test.org",
            "shib_user_name":"shib name"
        }
        # not exist shib_eppn
        shibuser = ShibUser(attr)
        result = shibuser.bind_relation_info(user)
        assert users[0]["obj"].email == "new.sysadmin_mail@test.org"
        assert shibuser.shib_attr["shib_eppn"] == "shib name"
        assert result == ShibbolethUser.query.filter_by(shib_eppn="shib name").one_or_none()
        
        # exist shib_eppn, raise Exception
        user = users[1]["email"]
        attr = {
            "shib_eppn":"test_eppn",
            "shib_mail":"new.repoadmin_mail@test.org"
        }
        shibuser = ShibUser(attr)
        with patch("weko_accounts.api.ShibbolethUser.create",side_effect=Exception):
            result = shibuser.bind_relation_info(user)
            assert result == None
#    def new_relation_info(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_new_relation_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_new_relation_info(self,users,mocker):
        datetime_mock = mocker.patch("weko_accounts.api.datetime")
        today = datetime(2022,10,6,1,2,3,4)
        datetime_mock.utcnow.return_value=today
        mocker.patch("weko_accounts.api.ShibUser.new_shib_profile")
        
        # exist user
        user = users[0]["obj"]
        attr = {
            "shib_mail":user.email,
            "shib_eppn":"test_eppn1"
        }
        shibuser = ShibUser(attr)
        result = shibuser.new_relation_info()
        assert result.shib_eppn == "test_eppn1"
        assert result.weko_uid == user.id
        
        # not exist user
        attr = {
            "shib_mail":"newuser@test.org",
            "shib_eppn":"test_eppn2"
        }
        shibuser = ShibUser(attr)
        result = shibuser.new_relation_info()
        assert result.shib_eppn == "test_eppn2"
        assert User.query.filter_by(email='newuser@test.org').one_or_none() is not None
#    def new_shib_profile(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_new_shib_profile -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_new_shib_profile(self,db,users):
        attr = {
            "shib_eppn":"test_eppn"
        }
        user = users[0]["obj"]
        s_user = ShibbolethUser(weko_uid=user.id,weko_user=user,**attr)
        db.session.add(s_user)
        db.session.commit()
        shibuser = ShibUser(attr)
        shibuser.shib_user = s_user
        shibuser.user=user
        
        result = shibuser.new_shib_profile()
        profile = UserProfile.query.filter_by(user_id=user.id).one_or_none()
        assert result==profile
        
#    def shib_user_login(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_shib_user_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_shib_user_login(self,request_context,users,mocker):
        mock_sender = mocker.patch("weko_accounts.api.user_logged_in.send")
        user = users[0]["obj"]
        shibuser = ShibUser({})
        shibuser.user=user
        shibuser.shib_user_login()
        mock_sender.assert_called_with(current_app._get_current_object(),user=user)
        assert session["user_id"] == user.id
        assert session["user_src"] == "Shib"
#    def assign_user_role(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_assign_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_assign_user_role(self,app, users,mocker):
        
        # not exist self.user
        shibuser = ShibUser({})
        flg, ret = shibuser.assign_user_role()
        assert flg == False
        assert ret == "Can't get relation Weko User."
        
        # exist self.user, issubset, ret is None
        attr = {
            "shib_role_authority_name":"管理者;図書館員"
        }
        shibuser = ShibUser(attr)
        shibuser.user = users[0]["obj"]
        mock_set_role=mocker.patch("weko_accounts.api.ShibUser._set_weko_user_role",return_value=None)
        app.config.update(WEKO_ACCOUNTS_SHIB_ROLE_ALL_USERS=['非会員','非会員2'])
        flg, ret = shibuser.assign_user_role()
        mock_set_role.assert_called_with(['System Administrator','Repository Administrator','非会員','非会員2'])
        assert flg == True
        assert ret == None

        # exist self.user, issubset, ret is None
        attr = {
            "shib_role_authority_name":"管理者;図書館員",
            "shib_page_name":"IPSJ:学会員;AL:会員;SLDM:会員",
        }
        shibuser = ShibUser(attr)
        shibuser.user = users[0]["obj"]
        mock_set_role=mocker.patch("weko_accounts.api.ShibUser._set_weko_user_role",return_value=None)
        app.config.update(WEKO_ACCOUNTS_SHIB_ROLE_ALL_USERS='非会員')
        flg, ret = shibuser.assign_user_role()
        mock_set_role.assert_called_with(['System Administrator','Repository Administrator','IPSJ:学会員','AL:会員','SLDM:会員','非会員'])
        assert flg == True
        assert ret == None

        # ret is error
        error = Exception("test_error")
        mock_set_role=mocker.patch("weko_accounts.api.ShibUser._set_weko_user_role",return_value=error)
        app.config.update(WEKO_ACCOUNTS_SHIB_ROLE_ALL_USERS='')
        flg, ret = shibuser.assign_user_role()
        mock_set_role.assert_called_with(['System Administrator','Repository Administrator','IPSJ:学会員','AL:会員','SLDM:会員',''])
        assert flg == False
        assert ret == error
        
        # not issubset
        attr = {
            "shib_role_authority_name":"異常役員"
        }
        shibuser = ShibUser(attr)
        shibuser.user = users[0]["obj"]
        mock_set_role=mocker.patch("weko_accounts.api.ShibUser._set_weko_user_role",return_value=error)
        app.config.update(WEKO_ACCOUNTS_SHIB_ROLE_ALL_USERS=None)
        flg, ret = shibuser.assign_user_role()
        mock_set_role.assert_not_called()
        assert flg == True
        assert ret == ""
#    def valid_site_license(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_valid_site_license -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_valid_site_license(self):
        # self._get_site_license is true
        attr = {
            "shib_eppn":"test_eppn",
            "shib_ip_range_flag":True
        }
        shibuser = ShibUser(attr)
        flg,msg = shibuser.valid_site_license()
        assert flg == True
        assert msg == ""
        # self._get_site_license is false
        attr = {
            "shib_eppn":"test_eppn",
        }
        shibuser = ShibUser(attr)
        flg,msg = shibuser.valid_site_license()
        assert flg == False
        assert msg == 'Failed to login.'
#    def check_in(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_check_in -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_check_in(self,mocker):
        shibuser = ShibUser({})
        # check_role is True
        with patch("weko_accounts.api.ShibUser.assign_user_role",return_value=(True,"")):
            result = shibuser.check_in()
            assert result == None
        # check_role is False
        with patch("weko_accounts.api.ShibUser.assign_user_role",return_value=(False,"test_error")):
            result = shibuser.check_in()
            assert result == "test_error"

#    @classmethod
#    def shib_user_logout(cls):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_shib_user_logout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_shib_user_logout(self,request_context,users,mocker):
        user = users[0]["obj"]
        login_user(user)
        mock_send = mocker.patch("weko_accounts.api.user_logged_out.send")
        shibuser = ShibUser({})
        shibuser.shib_user_logout()
        mock_send.assert_called_with(current_app._get_current_object(),user=user)
#def get_user_info_by_role_name(role_name):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_get_user_info_by_role_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_get_user_info_by_role_name(users):
    result = get_user_info_by_role_name('Repository Administrator')
    assert result == [users[1]["obj"],users[6]["obj"]]