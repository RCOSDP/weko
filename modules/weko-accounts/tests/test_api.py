from logging import exception
import pytest
from datetime import datetime
from mock import patch, MagicMock
from flask import session,current_app,Flask
from flask_login.utils import login_user
from invenio_accounts.models import Role, User,userrole
from weko_user_profiles.models import UserProfile
from weko_accounts.models import ShibbolethUser
from weko_accounts.api import ShibUser,get_user_info_by_role_name
from invenio_db import db as db_
from invenio_accounts import InvenioAccounts

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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_set_weko_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_get_site_license -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_site_license(self):
        attr = {
            "shib_eppn":"test_eppn",
            "shib_ip_range_flag":True
        }
        shibuser = ShibUser(attr)
        result = shibuser._get_site_license()
        assert result == True
#    def get_relation_info(self):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_get_relation_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_check_weko_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_bind_relation_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_new_relation_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_new_shib_profile -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_shib_user_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_assign_user_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_assign_user_role(self,users,mocker):
        
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
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_valid_site_license -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
class TestShibUser:
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
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        InvenioAccounts(app)
        db_.init_app(app)
        with app.app_context():
            db_.create_all()
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
    def shib_user(self,user):
        shib_attr = {
            'WEKO_SHIB_ATTR_IS_MEMBER_OF': 'group1',
            'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'jc_roles_repoadm'
        }
        shib_user = ShibUser(shib_attr)
        shib_user.user = user
        shib_user.shib_user = MagicMock(shib_roles=[])
        return shib_user
#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_check_in -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_check_in(self, app, mocker):
        shibuser = ShibUser({})
        shibuser.user = MagicMock(spec=User)
        shibuser.user.roles = MagicMock()

        with app.app_context():
            # assign_user_roleがFalseを返す場合のテスト
            mocker.patch.object(shibuser, 'assign_user_role', return_value=(False, "test_error"))
            result = shibuser.check_in()
            assert result == "test_error"
            shibuser.user.roles.clear.assert_called_once()

            # assign_user_roleがTrueを返す場合のテスト
            shibuser.user.roles.clear.reset_mock()
            mocker.patch.object(shibuser, 'assign_user_role', return_value=(True, ""))
            mocker.patch.object(shibuser, '_get_roles_to_add', return_value=set())
            mocker.patch.object(shibuser, '_assign_roles_to_user', return_value=None)
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()

            # reset_mockを呼び出してclearの呼び出し回数をリセット
            shibuser.user.roles.clear.reset_mock()

            # _get_roles_to_addがNoneを返す場合のテスト
            mocker.patch.object(shibuser, '_get_roles_to_add', return_value=None)
            result = shibuser.check_in()
            assert result == "Error getting roles to add"
            shibuser.user.roles.clear.assert_called_once()

            # _get_roles_to_addが空のセットを返す場合のテスト
            shibuser.user.roles.clear.reset_mock()
            mocker.patch.object(shibuser, '_get_roles_to_add', return_value=set())
            mocker.patch.object(shibuser, '_assign_roles_to_user', return_value=None)
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()

            # reset_mockを呼び出してclearの呼び出し回数をリセット
            shibuser.user.roles.clear.reset_mock()

            # _assign_roles_to_userがエラーを返す場合のテスト
            mocker.patch.object(shibuser, '_get_roles_to_add', return_value=set(['role1']))
            mocker.patch.object(shibuser, '_assign_roles_to_user', return_value="test_error")
            result = shibuser.check_in()
            assert result == "test_error"
            shibuser.user.roles.clear.assert_called_once()

            # _assign_roles_to_userが成功する場合のテスト
            shibuser.user.roles.clear.reset_mock()
            mocker.patch.object(shibuser, '_assign_roles_to_user', return_value=None)
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_get_roles_to_add -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_roles_to_add(self, app, mocker):
        shibuser = ShibUser({
            'WEKO_SHIB_ATTR_IS_MEMBER_OF': ['group1'],
            'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'idp_test',
            'WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING': {
            'test_entity_id': ['role1', 'role2']
        }
        })

        with app.app_context():
            # WEKO_SHIB_ATTR_IS_MEMBER_OFがリストの場合のテスト
            roles = shibuser._get_roles_to_add()
            assert roles == ['group1']

            # WEKO_SHIB_ATTR_IS_MEMBER_OFがセミコロン区切りの文字列の場合のテスト
            shibuser.shib_attr['WEKO_SHIB_ATTR_IS_MEMBER_OF'] = 'group1;group2'
            roles = shibuser._get_roles_to_add()
            assert roles == ['group1', 'group2']

            # WEKO_SHIB_ATTR_IS_MEMBER_OFがリストでもセミコロン区切りの文字列でもない場合のテスト
            shibuser.shib_attr['WEKO_SHIB_ATTR_IS_MEMBER_OF'] = 12345  # 不正な型
            roles = shibuser._get_roles_to_add()
            assert roles == []

            # WEKO_ACCOUNTS_IDP_ENTITY_IDが存在する場合、対応するロールを取得
            shibuser.shib_attr.pop('WEKO_SHIB_ATTR_IS_MEMBER_OF')
            shibuser.shib_attr['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'test_entity_id'  # role_mappingに対応
            roles = shibuser._get_roles_to_add()
            assert roles == ['role1', 'role2']

            # WEKO_ACCOUNTS_IDP_ENTITY_IDが存在するが設定した辞書に値が存在しない場合
            shibuser.shib_attr['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = 'repoadm_test'  # role_mappingに対応
            roles = shibuser._get_roles_to_add()
            assert roles == []

            # WEKO_ACCOUNTS_IDP_ENTITY_IDが存在しない場合のテスト
            shibuser.shib_attr.pop('WEKO_ACCOUNTS_IDP_ENTITY_ID')
            roles = shibuser._get_roles_to_add()
            assert roles == []

            # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがFalseの場合のテスト
            app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = False
            roles = shibuser._get_roles_to_add()
            assert roles == []

            #Exceptionが発生する場合のテスト
            shibuser.shib_attr = {}
            mock_logger = mocker.patch('flask.current_app.logger.error')
            roles = shibuser._get_roles_to_add()
            assert roles == []

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_assign_roles_to_user -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_assign_roles_to_user(self, app, shib_user, roles, mocker):
        with app.app_context():
            # モックの設定
            mock_role_query = mocker.patch('weko_accounts.api.Role.query.filter_by')
            mock_role_query.return_value.first.return_value = Role(name='Role_Administrator')
            mock_add_role = mocker.patch('weko_accounts.api._datastore.add_role_to_user')

            # 正常なケース
            roles_add = ['jc_role1']
            error = shib_user._assign_roles_to_user(roles_add)
            assert len(shib_user.shib_user.shib_roles) == 1
            assert shib_user.shib_user.shib_roles[0].name == 'Role_Administrator'

            # プレフィックスが一致しないケース
            roles_add = ['non_jc_role1']
            error = shib_user._assign_roles_to_user(roles_add)
            assert len(shib_user.shib_user.shib_roles) == 1  # 追加されないので変わらない

            # ロールが既にユーザーに割り当てられているケース
            shib_user.user.roles.append(roles[0])  # Role_Administrator を追加
            roles_add = ['jc_role1']
            error = shib_user._assign_roles_to_user(roles_add)
            assert len(shib_user.shib_user.shib_roles) == 1  # 追加されないので変わらない

            # 例外が発生する場合のテスト
            mock_role_query.side_effect = Exception("test_error")
            error = shib_user._assign_roles_to_user(roles_add)
            assert error == "This transaction is closed"

#    @classmethod
#    def shib_user_logout(cls):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUser::test_shib_user_logout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_shib_user_logout(self,request_context,users,mocker):
        user = users[0]["obj"]
        login_user(user)
        mock_send = mocker.patch("weko_accounts.api.user_logged_out.send")
        shibuser = ShibUser({})
        shibuser.shib_user_logout()
        mock_send.assert_called_with(current_app._get_current_object(),user=user)
#def get_user_info_by_role_name(role_name):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_get_user_info_by_role_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_user_info_by_role_name(users):
    result = get_user_info_by_role_name('Repository Administrator')
    assert result == [users[1]["obj"],users[6]["obj"]]