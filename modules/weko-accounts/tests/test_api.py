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
from weko_accounts.api import ShibUser,get_user_info_by_role_name,sync_shib_gakunin_map_groups,update_roles
from invenio_db import db as db_
from invenio_accounts import InvenioAccounts
from weko_accounts.api import ShibUser,get_user_info_by_role_name,sync_shib_gakunin_map_groups,update_roles,update_browsing_role,remove_browsing_role,update_contribute_role,remove_contribute_role
from weko_index_tree.models import Index

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
        assert set(shibuser.user.roles) == {role_repoadmin, role_sysadmin}
        assert set(shibuser.shib_user.shib_roles) == {role_repoadmin, role_sysadmin}

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
        shib_user_instance = ShibUser()
        shib_user_instance.user = user
        shib_user_instance.shib_user = shib_user
        return shib_user_instance
#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_check_in -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_check_in(self, app, mocker):
        shibuser = ShibUser({})
        shibuser.user = MagicMock(spec=User)
        shibuser.user.roles = MagicMock()

        with app.app_context():
            # テストでは_find_organization_nameは常にFalseを返すようにモック化
            mocker.patch.object(shibuser, '_find_organization_name', return_value=False)

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
            assert result == None
            shibuser.user.roles.clear.assert_called_once()

            # _assign_roles_to_userが成功する場合のテスト
            shibuser.user.roles.clear.reset_mock()
            mocker.patch.object(shibuser, '_assign_roles_to_user', return_value=None)
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()

            # _get_roles_to_addが空のセットを返す場合のテスト
            shibuser.user.roles.clear.reset_mock()
            mocker.patch.object(shibuser, '_get_roles_to_add', return_value=set())
            mocker.patch.object(shibuser, '_get_roles_to_add', side_effect=Exception("test_exception"))
            result = shibuser.check_in()
            assert result == "test_exception"
            shibuser.user.roles.clear.assert_called_once()

            # reset_mockを呼び出してclearの呼び出し回数をリセット
            shibuser.user.roles.clear.reset_mock()

            # _assign_roles_to_userがエラーを返す場合のテスト
            mocker.patch.object(shibuser, '_get_roles_to_add', return_value=set(['role1']))
            mocker.patch.object(shibuser, '_assign_roles_to_user', side_effect=Exception("test_exception"))
            result = shibuser.check_in()
            assert result == 'test_exception'
            shibuser.user.roles.clear.assert_called_once()

            # reset_mockを呼び出してclearの呼び出し回数をリセット
            shibuser.user.roles.clear.reset_mock()

            # WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPSがFalseの場合のテスト
            app.config['WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS'] = False
            result = shibuser.check_in()
            assert result is None
            shibuser.user.roles.clear.assert_called_once()

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_get_roles_to_add -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_roles_to_add(self, app, mocker):
        shibuser = ShibUser({
            'isMemberOf': ['role1'],
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
            shibuser.shib_attr['isMemberOf'] = 12345  # 不正な型
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
            shibuser.shib_attr['isMemberOf'] = []
            roles = shibuser._get_roles_to_add()
            assert roles == ['default_role']

            #WEKO_ACCOUNTS_IDP_ENTITY_IDが設定されていない場合のテスト
            app.config['WEKO_ACCOUNTS_IDP_ENTITY_ID'] = None
            with pytest.raises(KeyError, match='WEKO_ACCOUNTS_IDP_ENTITY_ID is missing in config'):
                shibuser._get_roles_to_add()

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_find_organization_name -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_find_organization_name(self, shib_user_a, app, mocker):
        with app.app_context():
            with patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app:

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

                group_ids = ['test_group_id']

                # 学認IdPのorganizationNameに登録がある場合のテスト
                mocker.patch("weko_accounts.api.ShibUser.get_organization_from_api", return_value="Gakunin2")
                result = shib_user_a._find_organization_name(group_ids)
                assert result == True

                # 機関内のOrthrosのorganizationNameに登録がある場合のテスト
                mocker.patch("weko_accounts.api.ShibUser.get_organization_from_api", return_value="Orthros")
                result = shib_user_a._find_organization_name(group_ids)
                assert result == True

                # 機関外のOrthrosのorganizationNameに登録がある場合のテスト
                mocker.patch("weko_accounts.api.ShibUser.get_organization_from_api", return_value="OutsideOrthros")
                result = shib_user_a._find_organization_name(group_ids)
                assert result == True

                # その他のorganizationNameに登録がある場合のテスト
                mocker.patch("weko_accounts.api.ShibUser.get_organization_from_api", return_value="Extra")
                result = shib_user_a._find_organization_name(group_ids)
                assert result == True

                # organizationNameに登録がない場合のテスト
                mocker.patch("weko_accounts.api.ShibUser.get_organization_from_api", return_value="invalid")
                result = shib_user_a._find_organization_name(group_ids)
                assert result == False

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_assign_roles_to_user -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_assign_roles_to_user(self, shib_user_a, app, mocker):
        with app.app_context():
            with patch('weko_accounts.api.Role') as mock_role, \
                patch('weko_accounts.api._datastore') as mock_datastore, \
                patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app:

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

                # Test data
                map_group_names = ['prefix_A_role_keyword_suffix', 'sysadm_group', 'unmapped_role', 'prefix_A_role_keyword_nonexistent']

                # Call the method
                shib_user_a._assign_roles_to_user(map_group_names)

                # Assertions
                assert mock_role.query.filter_by.call_count == 6
                assert mock_datastore.add_role_to_user.call_count == 0
                assert mock_db_session.commit.call_count == 1
#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_assign_roles_to_user_with_roles -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_assign_roles_to_user_with_roles(self,shib_user_a, app):
        with app.app_context():
            with patch('weko_accounts.api.Role') as mock_role, \
                patch('weko_accounts.api._datastore') as mock_datastore, \
                patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app:

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

                # Test data
                map_group_names = ['prefix_A_role_keyword_suffix', 'sysadm_group', 'unmapped_role']

                # Call the method
                shib_user_a._assign_roles_to_user(map_group_names)

                # Assertions
                assert mock_role.query.filter_by.call_count == 5
                assert mock_datastore.add_role_to_user.call_count == 5
                assert mock_db_session.commit.call_count == 1

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_assign_roles_to_user_exception -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_assign_roles_to_user_exception(self, shib_user_a, app, mocker):
        with app.app_context():
            with patch('weko_accounts.api.Role') as mock_role, \
                patch('weko_accounts.api._datastore') as mock_datastore, \
                patch('weko_accounts.api.db.session') as mock_db_session, \
                patch('weko_accounts.api.current_app') as mock_current_app:

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

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::TestShibUserExtra::test_get_ouganization_from_api -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_get_ouganization_from_api(self, app):
        """
        PeopleAPIからorganization_nameを取得するメソッドテスト
        """
        test_response = {
            "entry": [
                {
                    "organizations": [
                        {"type": "organization", "value": {
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
                    # モックが返すレスポンスを設定
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json = lambda: test_response

                    # ShibUserクラスのメソッドを呼び出し、結果を確認
                    result = shibuser.get_organization_from_api(group_id)
                    assert result == "Orthros"  # 期待値を比較


#    @classmethod
#    def shib_user_logout(cls):
# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_shib_user_logout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_shib_user_logout(request_context,users,mocker):
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
    assert result == [users[1]["obj"]]

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_success -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_success(app, client):
    with app.test_request_context('/sync', method='POST', data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'https://example.com'}):
        with patch('weko_accounts.api.RedisConnection') as mock_redis_conn, \
             patch('weko_accounts.api.Role') as mock_role, \
             patch('weko_accounts.api.update_roles') as mock_update_roles:

            # Redisから取得するグループリストとデータベースのロールリストが異なる場合
            mock_redis_conn().connection().lrange.return_value = ['role1', 'role3']
            mock_role1 = MagicMock()
            mock_role1.name = 'role1'
            mock_role2 = MagicMock()
            mock_role2.name = 'role2'
            mock_role.query.all.return_value = [mock_role1, mock_role2]

            sync_shib_gakunin_map_groups()

            # update_rolesが呼び出されることを確認
            mock_update_roles.assert_called_once()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_no_update_needed -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_no_update_needed(app, client):
    with app.test_request_context('/sync', method='POST', data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'https://example.com'}):
        with patch('weko_accounts.api.RedisConnection') as mock_redis_conn, \
             patch('weko_accounts.api.Role') as mock_role, \
             patch('weko_accounts.api.update_roles') as mock_update_roles:

            # Redisから取得するグループリストとデータベースのロールリストが同じ場合
            mock_redis_conn().connection().lrange.return_value = ['role1', 'role2']
            mock_role1 = MagicMock()
            mock_role1.name = 'role1'
            mock_role2 = MagicMock()
            mock_role2.name = 'role2'
            mock_role.query.all.return_value = [mock_role1, mock_role2]

            sync_shib_gakunin_map_groups()

            # update_rolesが呼び出されないことを確認
            mock_update_roles.assert_not_called()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_key_error -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_key_error(app, client):
    with app.test_request_context('/sync', method='POST', data={}):
        with patch('weko_accounts.api.current_app') as mock_current_app:
            with pytest.raises(KeyError):
                sync_shib_gakunin_map_groups()
            mock_current_app.logger.error.assert_called_once()

# .tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_redis_connection_error -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_redis_connection_error(app, client):
    with app.test_request_context('/sync', method='POST', data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'https://example.com'}):
        with patch('weko_accounts.api.RedisConnection') as mock_redis_conn, \
             patch('weko_accounts.api.current_app') as mock_current_app:

            mock_redis_conn().connection.side_effect = redis.ConnectionError

            with pytest.raises(redis.ConnectionError):
                sync_shib_gakunin_map_groups()
            mock_current_app.logger.error.assert_called_once()

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_sync_shib_gakunin_map_groups_unexpected_error -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_sync_shib_gakunin_map_groups_unexpected_error(app, client):
    with app.test_request_context('/sync', method='POST', data={'WEKO_ACCOUNTS_IDP_ENTITY_ID': 'https://example.com'}):
        with patch('weko_accounts.api.RedisConnection') as mock_redis_conn, \
             patch('weko_accounts.api.current_app') as mock_current_app:

            mock_redis_conn().connection.side_effect = Exception

            with pytest.raises(Exception):
                sync_shib_gakunin_map_groups()
            mock_current_app.logger.error.assert_called_once()

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_roles_add_new_roles -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_roles_add_new_roles(app, db, mocker):
    with app.app_context():
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

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_roles_with_permissions -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_roles_with_permissions(app, db, mocker):
    with app.app_context():
        # テストデータの準備
        map_group_list = ['group1', 'group2', 'group3', '']
        existing_role_names = {'group1', 'jc_group4'}

        # 既存のロールを追加
        existing_roles = []
        for role_name in existing_role_names:
            role = Role(name=role_name, description="description")
            db.session.add(role)
            existing_roles.append(role)
        db.session.commit()

        # Indexインスタンスを追加
        index1 = Index(id=1, parent=0, position=1, index_name='group1', index_name_english='Group 1 English')
        index2 = Index(id=2, parent=0, position=2, index_name='group2', index_name_english='Group 2 English')
        index3 = Index(id=3, parent=0, position=3, index_name='group3', index_name_english='Group 3 English')
        db.session.add(index1)
        db.session.add(index2)
        db.session.add(index3)
        db.session.commit()

        # 設定をモック
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = True
        app.config['WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = True

        # update_rolesの呼び出し
        update_roles(map_group_list, existing_roles,[index1])

        assert index1.browsing_role is not None


def test_update_roles_with_permissions_false(app, db, mocker):
    with app.app_context():
        # テストデータの準備
        map_group_list = ['group1', 'group2', 'group3', '']
        existing_role_names = {'group1', 'group4'}

        # 既存のロールを追加
        existing_roles = []
        for role_name in existing_role_names:
            role = Role(name=role_name, description="description")
            db.session.add(role)
            existing_roles.append(role)
        db.session.commit()

        # Indexインスタンスを追加
        index1 = Index(id=1, parent=0, position=1, index_name='group1', index_name_english='Group 1 English')
        index2 = Index(id=2, parent=0, position=2, index_name='group2', index_name_english='Group 2 English')
        index3 = Index(id=3, parent=0, position=3, index_name='group3', index_name_english='Group 3 English')
        db.session.add(index1)
        db.session.add(index2)
        db.session.add(index3)
        db.session.commit()

        # 設定をモック
        app.config['WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = False
        app.config['WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = False

        # APIモジュールのメソッドをモック
        mock_update_browsing_role = mocker.patch('weko_accounts.api.update_browsing_role')
        mock_remove_browsing_role = mocker.patch('weko_accounts.api.remove_browsing_role')
        mock_update_contribute_role = mocker.patch('weko_accounts.api.update_contribute_role')
        mock_remove_contribute_role = mocker.patch('weko_accounts.api.remove_contribute_role')

        # update_rolesの呼び出し
        update_roles(map_group_list, existing_roles)

        # APIモジュールのメソッドが呼び出されたことを確認
        assert mock_update_browsing_role.call_count == 0
        assert mock_remove_browsing_role.call_count == 0
        assert mock_update_contribute_role.call_count == 0
        assert mock_remove_contribute_role.call_count == 0

#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_roles_with_permissions_index_none -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_update_roles_with_permissions_index_none(app, db, mocker):
    with app.app_context():
        # テストデータの準備
        map_group_list = ['group1', 'group2', 'group3', '']
        existing_role_names = {'group1', 'group4'}

        # 既存のロールを追加
        existing_roles = []
        for role_name in existing_role_names:
            role = Role(name=role_name, description="description")
            db.session.add(role)
            existing_roles.append(role)
        db.session.commit()

        # Indexインスタンスを設定しない

        # 設定をモック
        app.config['WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION'] = True
        app.config['WEKO_INNDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION'] = True

        # APIモジュールのメソッドをモック
        mock_update_browsing_role = mocker.patch('weko_accounts.api.update_browsing_role')
        mock_remove_browsing_role = mocker.patch('weko_accounts.api.remove_browsing_role')
        mock_update_contribute_role = mocker.patch('weko_accounts.api.update_contribute_role')
        mock_remove_contribute_role = mocker.patch('weko_accounts.api.remove_contribute_role')

        # update_rolesの呼び出し
        update_roles(map_group_list, existing_roles)

        # APIモジュールのメソッドが呼び出されたことを確認
        assert mock_update_browsing_role.call_count == 0
        assert mock_remove_browsing_role.call_count == 0
        assert mock_update_contribute_role.call_count == 0
        assert mock_remove_contribute_role.call_count == 0
#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_and_remove_browsing_role -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
#.tox/c1/bin/pytest --cov=weko_accounts tests/test_api.py::test_update_and_remove_contribute_role -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
