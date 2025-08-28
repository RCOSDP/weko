from logging import exception
import pytest
import redis
from datetime import datetime
from mock import patch, MagicMock
from flask import session,current_app,Flask
from flask_login.utils import login_user
from invenio_accounts.models import Role, User,userrole
from weko_user_profiles.models import UserProfile
from weko_accounts.models import ShibbolethUser
from weko_accounts.api import (
    ShibUser,
    get_user_info_by_role_name,
    sync_shib_gakunin_map_groups,
    update_roles,
    update_browsing_role,
    remove_browsing_role,
    update_contribute_role,
    remove_contribute_role,
    bind_roles_to_indices,
    create_fqdn_from_entity_id
) 
from invenio_db import db as db_
from invenio_accounts import InvenioAccounts
from weko_index_tree.models import Index

#class ShibUser(object):
class TestShibUser:
#    def __init__(self, shib_attr=None):
    # .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_init(self):
        attr = {
            "shib_eppn":"test_eppn"
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == []

        # get is_member_of and type is list
        attr = {
            "shib_eppn":"test_eppn",
            "shib_is_member_of": ["https://example.com/gr/xxx", 
                                  "https://example.com/gr/yyy"]
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == ["https://example.com/gr/xxx", "https://example.com/gr/yyy"]
        assert shibuser.organizations == []

        # get is_member_of , type is str and not have semicolon
        attr = {
            "shib_eppn":"test_eppn",
            "shib_is_member_of": "https://example.com/gr/xxx"
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == ["https://example.com/gr/xxx"]
        assert shibuser.organizations == []

        # get is_member_of, type is str and have semicolon
        attr = {
            "shib_eppn":"test_eppn",
            "shib_is_member_of": "https://example.com/gr/xxx;https://example.com/gr/yyy"
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == ["https://example.com/gr/xxx", "https://example.com/gr/yyy"]
        assert shibuser.organizations == []

        # get is_member_of, type is str and is empty
        attr = {
            "shib_eppn": "test_eppn",
            "shib_is_member_of": ""
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == []

        # get is_member_of, type is neither list nor str
        attr = {
            "shib_eppn": "test_eppn",
            "shib_is_member_of": 123
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == []

        # get is_member_of, type is none
        attr = {
            "shib_eppn": "test_eppn",
            "shib_is_member_of": None
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == []

        # get organizations and type is list
        attr = {
            "shib_eppn":"test_eppn",
            "shib_organization": ["Abcdef University", "Test Organization"]
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == ["Abcdef University", "Test Organization"]

        # get organizations, type is str and not have semicolon
        attr = {
            "shib_eppn":"test_eppn",
            "shib_organization": "Abcdef University"
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == ["Abcdef University"]

        # get organizations, type is str and have semicolon
        attr = {
            "shib_eppn":"test_eppn",
            "shib_organization": "Abcdef University;Test Organization"
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == ["Abcdef University", "Test Organization"]

        # get organizations, type is str and is empty
        attr = {
            "shib_eppn": "test_eppn",
            "shib_organization": ""
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == []

        # get organizations, type is neither list nor str
        attr = {
            "shib_eppn": "test_eppn",
            "shib_organization": 123
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == []

        # get organizations, type is none
        attr = {
            "shib_eppn": "test_eppn",
            "shib_organization": None
        }
        shibuser = ShibUser(attr)
        assert shibuser.shib_attr == {"shib_eppn": "test_eppn"}
        assert shibuser.user == None
        assert shibuser.shib_user == None
        assert shibuser.is_member_of == []
        assert shibuser.organizations == []

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
        assert set(shibuser.user.roles) == {role_repoadmin, role_sysadmin}
        assert set(shibuser.shib_user.shib_roles) == {role_repoadmin, role_sysadmin}

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
#    def get_relation_info(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_get_relation_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_get_relation_info(self,app,db,users):

        user1 = users[0]["obj"]
        user2 = users[1]["obj"]
        attr = {
            "shib_eppn":"test_eppn"
        }
        s_user1 = ShibbolethUser(weko_uid=user1.id,weko_user=user1,**attr)
        db.session.add(s_user1)
        db.session.commit()
        # exist shib_eppn,exist shib_user.weko_user,not exist self.user
        attr = {
            "shib_eppn":"test_eppn",
            "shib_mail":"shib.user@test.org",
            "shib_user_name":"shib name1",
            "shib_role_authority_name":"shib auth"
        }
        shibuser = ShibUser(attr)
        result = shibuser.get_relation_info()
        assert result.shib_mail == "shib.user@test.org"
        assert result.shib_user_name == "shib name1"
        assert result.shib_role_authority_name == "shib auth"

        # not exist shib_eppn,not exist shib_user.weko_user
        attr = {
            "shib_eppn":"",
            "shib_user_name":"shib name2"
        }
        s_user2 = ShibbolethUser(**attr)
        db.session.add(s_user2)
        db.session.commit()
        shibuser = ShibUser(attr)
        result = shibuser.get_relation_info()
        assert result == None

        # not exist shib_eppn, exist shib_user.weko_user,exist self.user, raise Exception
        s_user2.weko_user = user2
        s_user2.weko_uid = user2.id
        db.session.merge(s_user2)
        db.session.commit()
        shibuser.user = user2
        with patch("weko_accounts.api.db.session.commit",side_effect=Exception):
            result = shibuser.get_relation_info()
            assert result == None
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
    def test_assign_user_role(self,users,mocker):

        # not exist self.user
        shibuser = ShibUser({})
        flg, ret = shibuser.assign_user_role()
        assert flg == False
        assert ret == "Can't get relation Weko User."

        # exist self.user, issubset, ret is None
        attr = {
            "shib_role_authority_name":"管理者;機関内のOrthros"
        }
        shibuser = ShibUser(attr)
        shibuser.user = users[0]["obj"]
        mock_set_role=mocker.patch("weko_accounts.api.ShibUser._set_weko_user_role",return_value=None)
        flg, ret = shibuser.assign_user_role()
        mock_set_role.assert_called_with(['System Administrator','Repository Administrator'])
        assert flg == True
        assert ret == None

        # ret is error
        error = Exception("test_error")
        mock_set_role=mocker.patch("weko_accounts.api.ShibUser._set_weko_user_role",return_value=error)
        flg, ret = shibuser.assign_user_role()
        mock_set_role.assert_called_with(['System Administrator','Repository Administrator'])
        assert flg == False
        assert ret == error

        # not issubset
        attr = {
            "shib_role_authority_name":"異常役員"
        }
        shibuser = ShibUser(attr)
        shibuser.user = users[0]["obj"]
        mock_set_role=mocker.patch("weko_accounts.api.ShibUser._set_weko_user_role",return_value=error)
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
class TestShibUserExtra:
    @pytest.fixture
    def app(self,db):
        app = Flask(__name__)
        app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = True
        app.config['WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING'] = {
            'test_entity_id': ['role1', 'role2']
        }
        app.config['WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT'] = {
            "prefix": "jc",
            "sysadm_group": "jc_roles_sysadm",
            "role_keyword": "roles",
            "role_mapping": {
                "idp_test": "idp_Administrator",
                   "role1": "Role_Administrator"
            }
        }
        app.config['WEKO_ADMIN_PERMISSION_ROLE_SYSTEM'] = 'admin_role'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'test_entity_id'
        app.config['CACHE_REDIS_DB'] = 1
        InvenioAccounts(app)
        # db_.init_app(app)
        # with app.app_context():
        #     db_.create_all()
        return app

    @pytest.fixture
    def user(self, db):
        user = User(email='test@example.com')
        db.session.add(user)
        db.session.commit()
        return user

    @pytest.fixture
    def roles(self, db):
        role1 = Role(name='Role_Administrator')
        role2 = Role(name='Role_Contributor')
        db.session.add(role1)
        db.session.add(role2)
        db.session.commit()
        return [role1, role2]

    @pytest.fixture
    def shib_user(user):
        shib_attr = {
            'WEKO_SHIB_ATTR_IS_MEMBER_OF': 'group1',
            'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'jc_roles_repoadm'
        }
        shib_user = ShibUser(shib_attr)
        shib_user.user = user
        shib_user.shib_user = MagicMock(shib_roles=[])
        return shib_user

    @pytest.fixture
    def shib_user_a(self):
        user = MagicMock()
        shib_user = MagicMock()
        shib_user_instance = ShibUser({})
        shib_user_instance.user = user
        shib_user_instance.shib_user = shib_user
        return shib_user_instance

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_check_in -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_check_in(self, app, mocker):
        shibuser = ShibUser({})
        shibuser.user = MagicMock(spec=User)
        shibuser.user.roles = MagicMock()

        with app.app_context():
            # prepare mock objects
            mock_assign_user_role = mocker.patch('weko_accounts.api.ShibUser.assign_user_role')
            mock_get_roles_to_add = mocker.patch('weko_accounts.api.ShibUser._get_roles_to_add')
            mock_find_organization_name = mocker.patch('weko_accounts.api.ShibUser._find_organization_name')
            mock_assign_roles_to_user = mocker.patch('weko_accounts.api.ShibUser._assign_roles_to_user')

            # assign_user_role returns False
            mock_assign_user_role.return_value = (False, "test_error")
            result = shibuser.check_in()
            assert result == "test_error"
            shibuser.user.roles.clear.assert_called_once()
            mock_assign_user_role.assert_called_once()
            mock_get_roles_to_add.assert_not_called()
            mock_find_organization_name.assert_not_called()
            mock_assign_roles_to_user.assert_not_called()
            shibuser.user.roles.clear.reset_mock()
            mocker.resetall()

            # assign_user_role returns True and WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS is False
            mock_assign_user_role.return_value = (True, "")
            app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = False
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()
            mock_assign_user_role.assert_called_once()
            mock_get_roles_to_add.assert_not_called()
            mock_find_organization_name.assert_not_called()
            mock_assign_roles_to_user.assert_not_called()
            shibuser.user.roles.clear.reset_mock()
            mocker.resetall()

            # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS is True and _find_organization_name returns True
            app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = True
            mock_get_roles_to_add.return_value = ['role1', 'role2']
            mock_find_organization_name.return_value = True
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()
            mock_assign_user_role.assert_called_once()
            mock_get_roles_to_add.assert_called_once()
            mock_find_organization_name.assert_called_once()
            mock_assign_roles_to_user.assert_not_called()
            shibuser.user.roles.clear.reset_mock()
            mocker.resetall()

            # _find_organization_name returns False
            mock_find_organization_name.return_value = False
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()
            mock_assign_user_role.assert_called_once()
            mock_get_roles_to_add.assert_called_once()
            mock_find_organization_name.assert_called_once()
            mock_assign_roles_to_user.assert_called_with(['role1', 'role2'])
            shibuser.user.roles.clear.reset_mock()
            mocker.resetall()

            # raise Exception in _get_roles_to_add
            mock_get_roles_to_add.side_effect = Exception("test_exception")
            result = shibuser.check_in()
            assert result == "test_exception"
            shibuser.user.roles.clear.assert_called_once()
            mock_assign_user_role.assert_called_once()
            mock_get_roles_to_add.assert_called_once()
            mock_find_organization_name.assert_not_called()
            mock_assign_roles_to_user.assert_not_called()
            shibuser.user.roles.clear.reset_mock()
            mocker.resetall()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_get_roles_to_add -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_get_roles_to_add(self, app):
        shibuser = ShibUser({
            'shib_is_member_of': ['role1'],
            'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'idp_test',
            'WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING': {
                'test_entity_id': ['default_role']
            }
        })

        with app.app_context():
            # WEKO_SHIB_ATTR_IS_MEMBER_OFがリストの場合のテスト
            roles = shibuser._get_roles_to_add()
            assert roles == ['role1']

            # WEKO_SHIB_ATTR_IS_MEMBER_OFがリストでもセミコロン区切りの文字列でもない場合のテスト
            shibuser.is_member_of = 12345  # 不正な型
            with pytest.raises(ValueError, match='isMemberOf is not a list'):
                shibuser._get_roles_to_add()
                assert roles == ['isMemberOf is not a list']

            # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがNoneの場合のテスト
            app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = False
            roles = shibuser._get_roles_to_add()
            assert roles == []

            # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがNoneの場合のテスト
            app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = None
            roles = shibuser._get_roles_to_add()
            assert roles == []

            # isMemberOfが空の場合のテスト
            app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = True
            app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'test_entity_id'
            app.config['WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING'] = {
                'test_entity_id': ['default_role']
            }
            shibuser.is_member_of = []
            roles = shibuser._get_roles_to_add()
            assert roles == ['default_role']

            #WEKO_ACCOUNTS_IDP_ENTITY_IDが設定されていない場合のテスト
            app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = None
            with pytest.raises(KeyError, match='WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in config'):
                shibuser._get_roles_to_add()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_find_organization_name -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_find_organization_name(self, shib_user_a, app, weko_roles, mocker):
        with app.app_context():
            with patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app, \
                patch('weko_accounts.api._datastore.add_role_to_user') as mock_add_role_to_user, \
                patch('weko_accounts.api.Role') as mock_role:

                mock_current_app.config = {
                    "WEKO_ACCOUNTS_GAKUNIN_ROLE": {
                        'defaultRole': 'Contributor',
                        'organizationName': ['Gakunin', 'Gakunin2']
                    },
                    "WEKO_ACCOUNTS_ORTHROS_INSIDE_ROLE": {
                        'defaultRole': 'Repository Administrator',
                        'organizationName': ['Orthros']
                    },
                    "WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE": {
                        'defaultRole': 'Community Administrator',
                        'organizationName': ['OutsideOrthros']
                    },
                    "WEKO_ACCOUNTS_EXTRA_ROLE": {
                        'defaultRole': 'None',
                        'organizationName': ['Extra']
                    }
                }

                # 学認IdPのorganizationNameに登録がある場合のテスト
                shib_user_a.organizations = ["Gakunin2"]
                mock_role.query.filter_by.return_value.one_or_none.return_value = weko_roles["contributor"]
                result = shib_user_a._find_organization_name()
                assert result == True
                assert mock_db_session.commit.call_count == 0
                assert mock_db_session.rollback.call_count == 0
                mock_add_role_to_user.assert_called_once_with(shib_user_a.user, weko_roles["contributor"])
                shib_user_a.shib_user.shib_roles.append.assert_called_once_with(weko_roles["contributor"])
                mock_db_session.commit.reset_mock()
                shib_user_a.shib_user.shib_roles.append.reset_mock()
                mock_add_role_to_user.reset_mock()

                # 機関内のOrthrosのorganizationNameに登録がある場合のテスト
                shib_user_a.organizations = ["Orthros"]
                mock_role.query.filter_by.return_value.one_or_none.return_value = weko_roles["repoadmin"]
                result = shib_user_a._find_organization_name()
                assert result == True
                assert mock_db_session.commit.call_count == 0
                assert mock_db_session.rollback.call_count == 0
                mock_add_role_to_user.assert_called_once_with(shib_user_a.user, weko_roles["repoadmin"])
                shib_user_a.shib_user.shib_roles.append.assert_called_once_with(weko_roles["repoadmin"])
                mock_db_session.commit.reset_mock()
                shib_user_a.shib_user.shib_roles.append.reset_mock()
                mock_add_role_to_user.reset_mock()

                # 機関外のOrthrosのorganizationNameに登録がある場合のテスト
                shib_user_a.organizations = ["OutsideOrthros"]
                mock_role.query.filter_by.return_value.one_or_none.return_value = weko_roles["comadmin"]
                result = shib_user_a._find_organization_name()
                assert result == True
                assert mock_db_session.commit.call_count == 0
                assert mock_db_session.rollback.call_count == 0
                mock_add_role_to_user.assert_called_once_with(shib_user_a.user, weko_roles["comadmin"])
                shib_user_a.shib_user.shib_roles.append.assert_called_once_with(weko_roles["comadmin"])
                mock_db_session.commit.reset_mock()
                shib_user_a.shib_user.shib_roles.append.reset_mock()
                mock_add_role_to_user.reset_mock()

                # その他のorganizationNameに登録がある場合のテスト
                shib_user_a.organizations = ["Extra"]
                mock_role.query.filter_by.return_value.one_or_none.return_value = None
                result = shib_user_a._find_organization_name()
                assert result == True
                assert mock_db_session.commit.call_count == 0
                assert mock_db_session.rollback.call_count == 0
                mock_add_role_to_user.assert_not_called()
                shib_user_a.shib_user.shib_roles.append.assert_not_called()
                mock_db_session.commit.reset_mock()
                shib_user_a.shib_user.shib_roles.append.reset_mock()
                mock_add_role_to_user.reset_mock()

                # organizationNameに登録がない場合のテスト
                shib_user_a.organizations = ["invalid"]
                result = shib_user_a._find_organization_name()
                assert result == False
                assert mock_db_session.commit.call_count == 1
                assert mock_db_session.rollback.call_count == 0
                mock_add_role_to_user.assert_not_called()
                shib_user_a.shib_user.shib_roles.append.assert_not_called()
                mock_db_session.commit.reset_mock()
                shib_user_a.shib_user.shib_roles.append.reset_mock()
                mock_add_role_to_user.reset_mock()

                # Exception Test
                mock_db_session.commit.side_effect = Exception("Test exception")
                with pytest.raises(Exception):
                    shib_user_a._find_organization_name()
                assert mock_db_session.commit.call_count == 1
                assert mock_db_session.rollback.call_count == 1
                assert mock_current_app.logger.error.call_count == 1

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_assign_roles_to_user -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_assign_roles_to_user(self, shib_user_a, app, mocker):
        with app.app_context():
            with patch('weko_accounts.api.Role') as mock_role, \
                patch('weko_accounts.api._datastore') as mock_datastore, \
                patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app, \
                patch('weko_accounts.api.create_fqdn_from_entity_id') as mock_create_fqdn:

                # Mock configuration
                mock_current_app.config = {
                    'WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT': {
                        'prefix': 'prefix',
                        'role_keyword': 'role_keyword',
                        'role_mapping': {'suffix': 'mapped_role'},
                        'sysadm_group': 'sysadm_group'
                    },
                    'WEKO_ADMIN_PERMISSION_ROLE_SYSTEM': 'admin_role'
                }

                # Mock Role queries
                mock_role.query.filter_by.return_value.one_or_none.side_effect = [None, None, None, None, None]
                mock_role.query.filter_by.return_value.one.side_effect = [None]

                mock_create_fqdn.return_value = 'A'

                # Test data
                map_group_names = [
                    'https://example.com/gr/prefix_A_role_keyword_suffix',
                    'https://example.com/gr/sysadm_group',
                    'https://example.com/gr/unmapped_role',
                    'https://example.com/gr/prefix_A_role_keyword_nonexistent',
                    'https://example.com/sp/prefix_A_role_keyword_suffix2',
                ]

                # Call the method
                shib_user_a._assign_roles_to_user(map_group_names)

                # Assertions
                assert mock_role.query.filter_by.call_count == 6
                assert mock_datastore.add_role_to_user.call_count == 0
                assert mock_db_session.commit.call_count == 1

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_assign_roles_to_user_with_roles -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_assign_roles_to_user_with_roles(self,shib_user_a, app):
        with app.app_context():
            with patch('weko_accounts.api.Role') as mock_role, \
                patch('weko_accounts.api._datastore') as mock_datastore, \
                patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app, \
                patch('weko_accounts.api.create_fqdn_from_entity_id') as mock_create_fqdn:

                # Mock configuration
                mock_current_app.config = {
                    'WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT': {
                        'prefix': 'prefix',
                        'role_keyword': 'role_keyword',
                        'role_mapping': {'suffix': 'mapped_role'},
                        'sysadm_group': 'sysadm_group'
                    },
                    'WEKO_ADMIN_PERMISSION_ROLE_SYSTEM': 'admin_role'
                }

                # Mock Role queries
                mock_role_instance = MagicMock()
                mock_role.query.filter_by.return_value.one_or_none.side_effect = [mock_role_instance, mock_role_instance, mock_role_instance,mock_role_instance]
                mock_role.query.filter_by.return_value.one.side_effect = [mock_role_instance]

                mock_create_fqdn.return_value = 'A'

                # Test data
                map_group_names = [
                    'https://example.com/gr/prefix_A_role_keyword_suffix',
                    'https://example.com/gr/sysadm_group',
                    'https://example.com/gr/unmapped_role',
                    'https://example.com/gr/prefix_A_role_keyword_suffix/admin',
                ]

                # Call the method
                shib_user_a._assign_roles_to_user(map_group_names)

                # Assertions
                assert mock_role.query.filter_by.call_count == 5
                assert mock_datastore.add_role_to_user.call_count == 5
                assert mock_db_session.commit.call_count == 1

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_assign_roles_to_user_exception -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_assign_roles_to_user_exception(self, shib_user_a, app, mocker):
        with app.app_context():
            with patch('weko_accounts.api.Role') as mock_role, \
                patch('weko_accounts.api._datastore') as mock_datastore, \
                patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app, \
                patch('weko_accounts.api.create_fqdn_from_entity_id') as mock_create_fqdn:

                # Mock configuration
                mock_current_app.config = {
                    'WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT': {
                        'prefix': 'prefix',
                        'role_keyword': 'role_keyword',
                        'role_mapping': {'suffix': 'mapped_role'},
                        'sysadm_group': 'sysadm_group'
                    },
                    'WEKO_ADMIN_PERMISSION_ROLE_SYSTEM': 'admin_role'
                }

                # Mock Role queries
                mock_role.query.filter_by.return_value.one_or_none.side_effect = [None, None, None, None]
                mock_role.query.filter_by.return_value.one.side_effect = [None]

                mock_create_fqdn.return_value = 'A'

                # Mock db.session.commit to raise an exception
                mock_db_session.commit.side_effect = Exception("Test exception")

                # Test data
                map_group_names = ['prefix_A_role_keyword_suffix', 'sysadm_group', 'unmapped_role']

                # Call the method and assert that an exception is raised
                with pytest.raises(Exception, match="Test exception"):
                    shib_user_a._assign_roles_to_user(map_group_names)

                # Assertions
                assert mock_role.query.filter_by.call_count == 5
                assert mock_datastore.add_role_to_user.call_count == 0
                assert mock_db_session.commit.call_count == 1
                assert mock_db_session.rollback.call_count == 1

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_get_organization_from_api -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
    def test_get_organization_from_api(self, app):
        """
        PeopleAPIからorganization_nameを取得するメソッドテスト
        """
        test_response = {
            "entry": [
                {
                    "organizations": [
                        {
                            "type": "organization",
                            "value": {
                                "name": "Orthros"
                            }
                        }
                    ]
                }
            ]
        }
        group_id = "test_group_id"
        shibuser = ShibUser({})
        with app.app_context():
            with patch('requests.get') as mock_get, \
                patch('weko_accounts.api.current_app') as mock_current_app:
                    mock_current_app.config = {
                        'WEKO_ACCOUNTS_GAKUNIN_MAP_BASE_URL': 'https://example.com'
                    }
                    # モックが返すレスポンスを設定
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json = lambda: test_response

                    # ShibUserクラスのメソッドを呼び出し、結果を確認
                    result = shibuser.get_organization_from_api(group_id)
                    assert result == "Orthros"  # 期待値を比較
                    mock_get.assert_called_once_with(f'https://example.com/api/people/@me/{group_id}',
                                                     headers={'Content-Type': 'application/json'}
                                                     )

                    # organization don't have type
                    test_response = {
                        'entry': [
                            {
                                'organizations': [
                                    {
                                        'value': {
                                            'name': 'Orthros'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                    mock_get.return_value.json = lambda: test_response
                    with pytest.raises(ValueError) as exc_info:
                        shibuser.get_organization_from_api(group_id)
                    assert str(exc_info.value) == f'Organization not found in response: {test_response}'

                    # organizations is empty
                    test_response = {
                        'entry': [
                            {
                                'organizations': []
                            }
                        ]
                    }
                    mock_get.return_value.json = lambda: test_response
                    with pytest.raises(ValueError) as exc_info:
                        shibuser.get_organization_from_api(group_id)
                    assert str(exc_info.value) == f'Organization not found in response: {test_response}'

                    # entry is empty
                    test_response = {
                        'entry': []
                    }
                    mock_get.return_value.json = lambda: test_response
                    with pytest.raises(ValueError) as exc_info:
                        shibuser.get_organization_from_api(group_id)
                    assert str(exc_info.value) == f'Organization not found in response: {test_response}'

                    # status_code is not 200
                    mock_get.return_value.status_code = 404
                    with pytest.raises(Exception) as exc_info:
                        shibuser.get_organization_from_api(group_id)
                    assert str(exc_info.value) == 'API returned error: 404'


#    @classmethod
#    def shib_user_logout(cls):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_shib_user_logout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_shib_user_logout(request_context,users,mocker):
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
    assert result == [users[1]["obj"]]

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_success -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_success(app, client, group_info_redis_connect):
    redis = group_info_redis_connect.redis
    with app.test_request_context('/sync', method='POST'):
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'https://example.com'
        with patch('weko_accounts.api.Role') as mock_role, \
             patch('weko_accounts.api.update_roles') as mock_update_roles:

            # Redisから取得するグループリストとデータベースのロールリストが異なる場合
            redis.delete('example_com_gakunin_groups')
            redis.rpush('example_com_gakunin_groups', 'role1', 'role3')
            mock_role1 = MagicMock()
            mock_role1.name = 'role1'
            mock_role2 = MagicMock()
            mock_role2.name = 'role2'
            mock_role.query.all.return_value = [mock_role1, mock_role2]

            sync_shib_gakunin_map_groups()

            # update_rolesが呼び出されることを確認
            mock_update_roles.assert_called_once_with(
                {'role1', 'role3'}, [mock_role1, mock_role2])

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_no_update_needed -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_no_update_needed(app, client, group_info_redis_connect):
    redis = group_info_redis_connect.redis
    with app.test_request_context('/sync', method='POST'):
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'https://example.com'
        with patch('weko_accounts.api.Role') as mock_role, \
             patch('weko_accounts.api.update_roles') as mock_update_roles:

            # Redisから取得するグループリストとデータベースのロールリストが同じ場合
            redis.delete('example_com_gakunin_groups')
            redis.rpush('example_com_gakunin_groups', 'role1', 'role2')
            mock_role1 = MagicMock()
            mock_role1.name = 'role1'
            mock_role2 = MagicMock()
            mock_role2.name = 'role2'
            mock_role.query.all.return_value = [mock_role1, mock_role2]

            sync_shib_gakunin_map_groups()

            # update_rolesが呼び出されないことを確認
            mock_update_roles.assert_not_called()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_key_error -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_key_error(app, client):
    with app.test_request_context('/sync', method='POST'):
        with patch('weko_accounts.api.current_app.logger') as mock_logger:
            with pytest.raises(KeyError):
                sync_shib_gakunin_map_groups()
            mock_logger.error.assert_called_once()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_redis_connection_error -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_redis_connection_error(app, client):
    with app.test_request_context('/sync', method='POST'):
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'https://example.com'
        with patch('weko_accounts.api.RedisConnection') as mock_redis_conn, \
             patch('weko_accounts.api.current_app.logger') as mock_logger:

            mock_redis_conn().connection.side_effect = redis.ConnectionError

            with pytest.raises(redis.ConnectionError):
                sync_shib_gakunin_map_groups()
            mock_logger.error.assert_called_once()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_unexpected_error -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_unexpected_error(app, client):
    with app.test_request_context('/sync', method='POST'):
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'https://example.com'
        with patch('weko_accounts.api.RedisConnection') as mock_redis_conn, \
             patch('weko_accounts.api.current_app.logger') as mock_logger:

            mock_redis_conn().connection.side_effect = Exception

            with pytest.raises(Exception):
                sync_shib_gakunin_map_groups()
            mock_logger.error.assert_called_once()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_roles -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_update_roles(app, db, mocker):
    with app.app_context():
        mock_bind = mocker.patch('weko_accounts.api.bind_roles_to_indices')
        # テストデータの準備
        map_group_list = ['group1', 'group2', 'group3','']
        existing_role_names = {'group1', 'jc_group4'}

        # 既存のロールを追加
        existing_roles = []
        for role_name in existing_role_names:
            role = Role(name=role_name, description="description")
            db.session.add(role)
            existing_roles.append(role)
        db.session.commit()

        # update_rolesの呼び出し
        update_roles(map_group_list, existing_roles)

        # 結果の検証
        roles = Role.query.all()
        role_names = [role.name for role in roles]
        assert 'group1' in role_names
        assert 'group2' in role_names  # 新しいロールが追加されていることを確認
        assert 'group3' in role_names  # 新しいロールが追加されていることを確認
        assert 'jc_group4' not in role_names  # 既存のロールが削除されていることを確認
        assert '' not in role_names  # 空のロールが追加されていないことを確認

        new_roles = [r for r in roles if r.name in ['group2', 'group3']]
        remove_role_ids = [r.id for r in existing_roles if r.name == 'jc_group4']
        mock_bind.assert_called_once_with([], new_roles, remove_role_ids)

        with patch('weko_accounts.api.db.session.commit', side_effect=Exception("Test exception")),\
            patch('weko_accounts.api.current_app.logger') as mock_logger:
            with pytest.raises(Exception):
                map_group_list = ['group5']
                existing_roles = [existing_roles[0]]
                update_roles(map_group_list, existing_roles)
            mock_logger.error.assert_called_once_with('Error adding new roles: Test exception')

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_bind_roles_to_indices_with_all_permissions -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_bind_roles_to_indices_with_all_permissions(app, indices):
    with app.app_context():
        # setting config
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = True
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = True

        # create test data
        new_role1 = Role(id=3, name='group3', description='description')
        new_role2 = Role(id=4, name='group4', description='description')

        bind_roles_to_indices([], [new_role1, new_role2], [2, 5])

        result_indices = sorted(Index.query.all(), key=lambda x: x.id)
        assert result_indices[0].browsing_role == '1,3,4'
        assert result_indices[0].contribute_role == '1,3,4'
        assert result_indices[1].browsing_role == '1,3,4'
        assert result_indices[1].contribute_role == '3,4'
        assert result_indices[2].browsing_role == '3,4'
        assert result_indices[2].contribute_role == '1,3,4'
        assert result_indices[3].browsing_role == '3,4'
        assert result_indices[3].contribute_role == '3,4'

        with patch('weko_accounts.api.db.session.commit', side_effect=Exception("Test exception")),\
            patch('weko_accounts.api.current_app.logger') as mock_logger:
            with pytest.raises(Exception):
                bind_roles_to_indices([], [new_role1, new_role2], [2, 5])
            mock_logger.error.assert_called_once_with('Error binding roles to indices: Test exception')

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_bind_roles_to_indices_with_browsing_permissions -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_bind_roles_to_indices_with_browsing_permissions(app, indices):
    with app.app_context():
        # setting config
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = True
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = False

        # create test data
        new_role1 = Role(id=3, name='group3', description='description')
        new_role2 = Role(id=4, name='group4', description='description')

        bind_roles_to_indices([], [new_role1, new_role2], [2, 5])

        result_indices = sorted(Index.query.all(), key=lambda x: x.id)
        assert result_indices[0].browsing_role == '1,3,4'
        assert result_indices[0].contribute_role == '1,3'
        assert result_indices[1].browsing_role == '1,3,4'
        assert result_indices[1].contribute_role == ''
        assert result_indices[2].browsing_role == '3,4'
        assert result_indices[2].contribute_role == '1,3'
        assert result_indices[3].browsing_role == '3,4'
        assert result_indices[3].contribute_role == ''

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_bind_roles_to_indices_with_contribute_permissions -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_bind_roles_to_indices_with_contribute_permissions(app, indices):
    with app.app_context():
        # setting config
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = False
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = True

        # create test data
        new_role1 = Role(id=3, name='group3', description='description')
        new_role2 = Role(id=4, name='group4', description='description')

        bind_roles_to_indices([], [new_role1, new_role2], [2, 5])

        result_indices = sorted(Index.query.all(), key=lambda x: x.id)
        assert result_indices[0].browsing_role == '1,3'
        assert result_indices[0].contribute_role == '1,3,4'
        assert result_indices[1].browsing_role == '1,3'
        assert result_indices[1].contribute_role == '3,4'
        assert result_indices[2].browsing_role == ''
        assert result_indices[2].contribute_role == '1,3,4'
        assert result_indices[3].browsing_role == ''
        assert result_indices[3].contribute_role == '3,4'

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_bind_roles_to_indices_with_no_permissions -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_bind_roles_to_indices_with_no_permissions(app, indices):
    with app.app_context():
        # setting config
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = False
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = False

        # create test data
        new_role1 = Role(id=3, name='group3', description='description')
        new_role2 = Role(id=4, name='group4', description='description')

        bind_roles_to_indices([], [new_role1, new_role2], [2, 5])

        result_indices = sorted(Index.query.all(), key=lambda x: x.id)
        assert result_indices[0].browsing_role == '1,3'
        assert result_indices[0].contribute_role == '1,3'
        assert result_indices[1].browsing_role == '1,3'
        assert result_indices[1].contribute_role == ''
        assert result_indices[2].browsing_role == ''
        assert result_indices[2].contribute_role == '1,3'
        assert result_indices[3].browsing_role == ''
        assert result_indices[3].contribute_role == ''

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_bind_roles_to_indices_with_select_index -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_bind_roles_to_indices_with_select_index(app, indices):
    with app.app_context():
        # setting config
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = True
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = True

        # create test data
        new_role1 = Role(id=3, name='group3', description='description')
        new_role2 = Role(id=4, name='group4', description='description')

        bind_roles_to_indices([indices[1]], [new_role1, new_role2], [2, 5])

        result_indices = sorted(Index.query.all(), key=lambda x: x.id)
        assert result_indices[0].browsing_role == '1,2,3'
        assert result_indices[0].contribute_role == '1,2,3'
        assert result_indices[1].browsing_role == '1,3,4'
        assert result_indices[1].contribute_role == '3,4'
        assert result_indices[2].browsing_role == ''
        assert result_indices[2].contribute_role == '1,2,3'
        assert result_indices[3].browsing_role == ''
        assert result_indices[3].contribute_role == ''

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_and_remove_browsing_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_update_and_remove_browsing_role(app, db):
    with app.app_context():
        # テスト用のIndexインスタンスを作成
        index = Index(
            id=1,
            index_name='Test Index',
            index_name_english='Test Index English'
        )
        db.session.add(index)
        db.session.commit()

        # 初期状態では browsing_role は None
        assert index.browsing_role is None

        # browsing_role が None の場合に remove_browsing_role を呼び出す
        remove_browsing_role(index, 1)
        db.session.commit()
        assert index.browsing_role is None  # 変更がないことを確認

        # ロールID 1 を追加
        update_browsing_role(index, 1)
        db.session.commit()
        assert index.browsing_role == '1'

        # 存在しないロールID 3 を削除しようとする
        remove_browsing_role(index, 3)
        db.session.commit()
        assert index.browsing_role == '1'  # 変更がないことを確認

        # ロールID 2 を追加
        update_browsing_role(index, 2)
        db.session.commit()
        assert set(index.browsing_role.split(',')) == {'1', '2'}

        # 既存のロールID 1 を再度追加しても重複しない
        update_browsing_role(index, 1)
        db.session.commit()
        assert set(index.browsing_role.split(',')) == {'1', '2'}

        # ロールID 1 を削除
        remove_browsing_role(index, 1)
        db.session.commit()
        assert index.browsing_role == '2'

        # ロールID 2 を削除
        remove_browsing_role(index, 2)
        db.session.commit()
        assert index.browsing_role == ''

        # クリーンアップ
        db.session.delete(index)
        db.session.commit()
#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_and_remove_contribute_role -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_update_and_remove_contribute_role(app, db):
    with app.app_context():
        # テスト用のIndexインスタンスを作成
        index = Index(
            id=1,
            index_name='Test Index',
            index_name_english='Test Index English'
        )
        db.session.add(index)
        db.session.commit()

        # 初期状態では browsing_role は None
        assert index.contribute_role is None

        # browsing_role が None の場合に remove_browsing_role を呼び出す
        remove_contribute_role(index, 1)
        db.session.commit()
        assert index.contribute_role is None  # 変更がないことを確認

        # ロールID 1 を追加
        update_contribute_role(index, 1)
        db.session.commit()
        assert index.contribute_role == '1'

        # 存在しないロールID 3 を削除しようとする
        remove_contribute_role(index, 3)
        db.session.commit()
        assert index.contribute_role == '1'  # 変更がないことを確認

        # ロールID 2 を追加
        update_contribute_role(index, 2)
        db.session.commit()
        assert set(index.contribute_role.split(',')) == {'1', '2'}  # 順序を考慮しない

        # 既存のロールID 1 を再度追加しても重複しない
        update_contribute_role(index, 1)
        db.session.commit()
        assert set(index.contribute_role.split(',')) == {'1', '2'}  # 順序を考慮しない

        # ロールID 1 を削除
        remove_contribute_role(index, 1)
        db.session.commit()
        assert index.contribute_role == '2'

        # ロールID 2 を削除
        remove_contribute_role(index, 2)
        db.session.commit()
        assert index.contribute_role == ''

        # クリーンアップ
        db.session.delete(index)
        db.session.commit()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_create_fqdn_from_entity_id -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-accounts/.tox/c1/tmp
def test_create_fqdn_from_entity_id(app):
    with app.app_context():
        # Test when WEKO_ACCOUNTS_IDP_ENTITY_ID is set
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'https://example-org.com/shibboleth'
        fqdn = create_fqdn_from_entity_id()
        assert fqdn == 'example_org_com'

        # Test when WEKO_ACCOUNTS_IDP_ENTITY_ID is not set
        app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = None
        with pytest.raises(KeyError, match='WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in config'):
            create_fqdn_from_entity_id()
