# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Tests for user profile forms."""

import pytest
from mock import patch

from wtforms import StringField, SelectField
from wtforms.validators import StopValidation,ValidationError

from flask import Blueprint, current_app,Flask
from flask_login.utils import login_user, logout_user
from flask_wtf import FlaskForm


from weko_user_profiles.models import UserProfile
from weko_user_profiles.forms import (
    VerificationForm,
    strip_filter,
    _update_with_csrf_disabled, 
    confirm_register_form_factory, 
    register_form_factory,
    current_user_email,
    check_phone_number,
    check_length_100_characters,
    check_other_position,
    ProfileForm,
    EmailProfileForm,
    validate_digits
)

from tests.helpers import login,logout

# def test_register_form_factory_no_csrf(app):
#     """Test CSRF token is not in reg. form and not in profile inner form."""
#     security = app.extensions['security']
#     rf = _get_form(app, security.register_form, register_form_factory)

# def test_register_form_factory_no_csrf(app):
#     """Test CSRF token is not in reg. form and not in profile inner form."""
#     security = app.extensions['security']
#     rf = _get_form(app, security.register_form, register_form_factory)

#     _assert_no_csrf_token(rf)


# def test_register_form_factory_csrf(app_with_csrf):
#     """Test CSRF token is in reg. form but not in profile inner form."""
#     security = app_with_csrf.extensions['security']
#     rf = _get_form(app_with_csrf, security.register_form,
#                    register_form_factory)

#     _assert_csrf_token(rf)


# def test_force_disable_csrf_register_form(app_with_csrf):
#     """Test force disable CSRF for reg. form."""
#     security = app_with_csrf.extensions['security']
#     rf = _get_form(app_with_csrf, security.register_form,
#                    register_form_factory, force_disable_csrf=True)
#     _assert_no_csrf_token(rf)


# def test_confirm_register_form_factory_no_csrf(app):
#     """Test CSRF token is not in confirm form and not in \
#     profile inner form."""
#     security = app.extensions['security']
#     rf = _get_form(app, security.confirm_register_form,
#                    confirm_register_form_factory)

#     _assert_no_csrf_token(rf)


# def test_confirm_register_form_factory_csrf(app_with_csrf):
#     """Test CSRF token is in confirm form but not in profile inner form."""
#     security = app_with_csrf.extensions['security']
#     rf = _get_form(app_with_csrf, security.confirm_register_form,
#                    confirm_register_form_factory)

#     _assert_csrf_token(rf)


# def test_force_disable_csrf_confirm_form(app_with_csrf):
#     """Test force disable CSRF for confirm form."""
#     security = app_with_csrf.extensions['security']
#     rf = _get_form(app_with_csrf, security.confirm_register_form,
#                    confirm_register_form_factory, force_disable_csrf=True)

#     _assert_no_csrf_token(rf)


def _assert_csrf_token(form):
    """Assert that the field `csrf_token` exists in the form."""
    assert 'profile' in form
    assert 'csrf_token' not in form.profile
    assert 'csrf_token' in form
    assert form.csrf_token


def _assert_no_csrf_token(form):
    """Assert that the field `csrf_token` does not exist in the form."""
    assert 'profile' in form
    assert 'csrf_token' not in form.profile
    # Flask-WTF==0.13.1 adds always `csrf_token` field, but with None value
    # Flask-WTF>0.14.2 do not `csrf_token` field
    assert 'csrf_token' not in form or form.csrf_token.data is None


def _get_form(app, parent_form, factory_method, force_disable_csrf=False):
    """Create and fill a form."""
    class AForm(parent_form):
        pass

    with app.test_request_context():
        extra = _update_with_csrf_disabled() if force_disable_csrf else {}

        RF = factory_method(AForm)
        rf = RF(**extra)

        rf.profile.username.data = "my username"
        rf.profile.full_name.data = "My full name"

        rf.validate()

        return rf


form_test_blueprint = Blueprint(
    "form_test",
    __name__)


@form_test_blueprint.route("/profile_form",methods=["POST"])
def profile_form():
    form = ProfileForm(csrf_enabled=False)

    if form.validate_on_submit():
        return "OK"
    
    if len(form.username.errors) > 0:
        return str(form.username.errors[0])
    else:
        return "invalid"


@form_test_blueprint.route("/verification_form",methods=["POST"])
def verification_form():
    form = VerificationForm()
    if form.validate_on_submit():
        return "OK"
    return form.send_verification_email.errors


@pytest.fixture()
def register_form(app):
    app.register_blueprint(form_test_blueprint,url_prefix="/test_form")




class MockData:
    def __init__(self,data):
        self.data = data
        self.errors = []


# def strip_filter(text):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_strip_filter -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_strip_filter():
    result = strip_filter(" test ")
    assert result == "test"
    
    result = strip_filter("")
    assert result == ""


#def current_user_email(form, field):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_current_user_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_current_user_email(req_context,users):

    login_user(users[0]["obj"])
    field = MockData("sysadmin@test.org")
    with pytest.raises(StopValidation):
        current_user_email({},field)
    
    logout_user()
    login_user(users[1]["obj"])
    current_user_email({},field)


#def check_phone_number(form, field):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_check_phone_number -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_check_phone_number():
    # data > 15
    field = MockData("1111111111111111")
    with pytest.raises(ValidationError) as e:
        check_phone_number({},field)
        assert str(e.value) == 'Phone number must be less than 15 characters.'
    
    # data is not currect format
    field = MockData("this-is-not-correct-data")
    with pytest.raises(ValidationError) as e:
        check_phone_number({},field)
        assert str(e.value) == 'Phone Number format is incorrect.'
    
    # correct
    field = MockData("12-345")
    check_phone_number({},field)

#.tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_validate_digits -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
#識別子のバリデーション
def test_validate_digits():

    #異常系(数字以外)
    field = MockData("test data")
    with pytest.raises(ValidationError) as e:
        validate_digits({},field)
        assert str(e.value) == 'Only digits are allowed.'

    #異常系(全角数字)
    field = MockData("０１２３４５６７８９")
    with pytest.raises(ValidationError) as e:
        validate_digits({},field)
        assert str(e.value) == 'Only digits are allowed.'

    #正常系
    field = MockData("0123456789")
    validate_digits({},field)

    field = MockData("")
    validate_digits({},field)

    # 正常系(None文字列)
    field = MockData("None")
    validate_digits({}, field)

#def check_length_100_characters(form, field):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_check_length_100_characters -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_check_length_100_characters():
    # data > 100
    field = MockData("a"*150)
    with pytest.raises(ValidationError) as e:
        check_length_100_characters({},field)
        assert str(e) == "Text field must be less than 100 characters."
    # data <= 100
    field = MockData("a"*50)
    check_length_100_characters({},field)


#def check_other_position(form, field):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_check_other_position -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
# モッククラスの定義
class MockForm:
    def __init__(self, data):
        self.position = self.MockPosition(data)

    class MockPosition:
        def __init__(self, data):
            self.data = data

class MockField:
    def __init__(self, data):
        self.data = data

# モック関数の定義
def strip_filter(data):
    return data.strip()

# テスト関数
@pytest.mark.parametrize("position, field_data, expected_exception, expected_message", [
    ("test form", "test data", ValidationError, "Position is being inputted (Only input when selecting 'Others')"),
    ("test form", "", None, None),
    ("Others", "", ValidationError, 'Position not provided.'),
    ("Others", "test data", None, None),
    ("その他", "", ValidationError, 'Position not provided.'),
    ("その他", "test data", None, None),
])
#check_other_positionのテスト
def test_check_other_position(position, field_data, expected_exception, expected_message):
    form = MockForm(position)
    field = MockField(field_data)

    if expected_exception:
        with pytest.raises(expected_exception) as e:
            check_other_position(form, field)
        assert str(e.value) == expected_message
    else:
        check_other_position(form, field)  # 例外は発生しない


class TestProfileForm:
    # .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::TestProfileForm::test_get_profile_conf -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp

    def test_get_profile_conf(self, app):
        # プロファイル設定が取得できることを確認するテスト
        profile_conf = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'text', 'label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            #正常系
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
                form = ProfileForm()
                assert form is not None

            #異常系
            with patch('weko_admin.models.AdminSettings.get', return_value=None):
                with pytest.raises(ValueError, match="Could not retrieve profile configuration settings."):
                    ProfileForm()

    # .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::TestProfileForm::test_missing_fixed_itemkeys -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp

    def test_missing_fixed_itemkeys(self, app):
        # 固定されたキーが存在する場合のテスト
        profile_conf = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'text', 'label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
                form = ProfileForm()
                assert form is not None


        #異常系
        profile_conf2 = {
            'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'text', 'label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf2):
                with pytest.raises(KeyError, match="Could not find the following keys in profile configuration settings: \['fullname'\]"):
                    ProfileForm()

        #universityが欠損
        profile_conf3 = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'text', 'label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf3):
                with pytest.raises(KeyError, match="Could not find the following keys in profile configuration settings: \['university'\]"):
                    ProfileForm()
        
        #departmentが欠損
        profile_conf4 = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
            'position': {'current_type': 'text', 'label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf4):
                with pytest.raises(KeyError, match="Could not find the following keys in profile configuration settings: \['department'\]"):
                    ProfileForm()
        
        #positionが欠損
        profile_conf5 = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf5):
                with pytest.raises(KeyError, match="Could not find the following keys in profile configuration settings: \['position'\]"):
                    ProfileForm()

        #キーが取得できなかった、想定外のキーを取得した場合
        profile_conf = {
            'some_other_key': {'current_type': 'text', 'label_name': 'Some Other Key', 'visible': True, 'select': ['']}
        }
 
        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
                with pytest.raises(KeyError, match="Could not find the following keys in profile configuration settings: \['fullname', 'university', 'department', 'position'\]"):
                    ProfileForm()


    # .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::TestProfileForm::test_missing_current_type_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp

    def test_missing_current_type_key(self, app):
        # current_typeキーが欠損している場合のテスト
        profile_conf = {
            'fullname': {'label_name': 'Full Name', 'visible': True, 'select': ['']},
             'university': {'current_type': 'text','label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text','label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'select','label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
                with pytest.raises(KeyError, match=r"Missing required key\(s\) \['current_type'\] in field: fullname"):
                    ProfileForm()

            #label_nameが欠損
            profile_conf2 = {
                'fullname': {'current_type': 'text','label_name': 'Full Name', 'visible': True, 'select': ['']},
                'university': {'current_type': 'text','visible': True, 'select': ['']},
                'department': {'current_type': 'text','label_name': 'Department', 'visible': True, 'select': ['']},
                'position': {'current_type': 'select','label_name': 'Position', 'visible': True, 'select': ['']}
            }

            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf2):
                with pytest.raises(KeyError, match=r"Missing required key\(s\) \['label_name'\] in field: university"):
                    ProfileForm()

        #visibleが欠損
            profile_conf3 = {
                'fullname': {'current_type': 'text','label_name': 'Full Name', 'visible': True, 'select': ['']},
                'university': {'current_type': 'text','label_name': 'University', 'visible': True, 'select': ['']},
                'department': {'current_type': 'text','label_name': 'Department','select': ['']},
                'position': {'current_type': 'select','label_name': 'Position', 'visible': True, 'select': ['']}
            }

            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf3):
                with pytest.raises(KeyError, match=r"Missing required key\(s\) \['visible'\] in field: department"):
                    ProfileForm()
        
            #selectが欠損
            profile_conf4 = {
                'fullname': {'current_type': 'text','label_name': 'Full Name', 'visible': True, 'select': ['']},
                'university': {'current_type': 'text','label_name': 'University', 'visible': True, 'select': ['']},
                'department': {'current_type': 'text','label_name': 'Department', 'visible': True, 'select': ['']},
                'position': {'current_type': 'select','label_name': 'Position', 'visible': True,}
            }
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf4):
                with pytest.raises(KeyError, match=r"Missing required key\(s\) \['select'\] in field: position"):
                    ProfileForm()
        
            #正常系
            profile_conf5 = {
                'fullname': {'current_type': 'text','label_name': 'Full Name', 'visible': True, 'select': ['']},
                'university': {'current_type': 'text','label_name': 'University', 'visible': True, 'select': ['']},
                'department': {'current_type': 'text','label_name': 'Department', 'visible': True, 'select': ['']},
                'position': {'current_type': 'select','label_name': 'Position', 'visible': True, 'select': ['']}
            }
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf5):
                form = ProfileForm()
                assert form is not None

    # .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::TestProfileForm::test_fields_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp

    def test_fields_settings(self, app):
        from werkzeug.datastructures import MultiDict
    # 不正な 'select' 値が入っている場合のテスト
        profile_form = {
            'fullname': {'current_type': 'select', 'label_name': 'Full Name', 'visible': True, 'select': ['item1|item2|item3']},
            'university': {'current_type': 'identifier', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'select', 'label_name': 'Position', 'visible': True, 'select': ''}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_form):
                with pytest.raises(ValueError, match=r"Invalid 'select' value in field: position"):
                    ProfileForm()

        # 不正な 'current_type' 値が入っている場合のテスト
        profile_form = {
            'fullname': {'current_type': 'select', 'label_name': 'Full Name', 'visible': True, 'select': ['item1|item2|item3']},
            'university': {'current_type': 'identifier', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'test', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'select', 'label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_form):
                with pytest.raises(ValueError, match=r"Invalid 'current_type' value in field: department"):
                    ProfileForm()

        # 正常な 'identifier' タイプのフィールド生成のテスト
        profile_form = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'university': {'current_type': 'identifier', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'select', 'label_name': 'Position', 'visible': True, 'select': ['item1|item2|item3']}
        }

        with app.test_client():
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_form):
                form = ProfileForm()
                
                # フォームデータの設定
                form_data = MultiDict({
                    'university': '123456789',         # universityフィールドに値を設定
                })

                # フォームデータを処理
                form.process(form_data)

                # フィールドの生成を確認
                assert form is not None
                assert isinstance(form.university, StringField)  # 'identifier' の場合
                assert form.university.data == '123456789'
                print(f"University: {form.university.data}")

        # 'text' タイプのフィールド生成のテスト
        profile_form1 = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'university': {'current_type': 'identifier', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'text', 'label_name': 'Position', 'visible': True, 'select': ['']}
        }

        with app.test_client():
            # AdminSettings.getをモックして、profile_formを返すようにする
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_form1):
                print(f"formtext1:", profile_form)

                # ProfileFormのインスタンスを作成
                form = ProfileForm()

                # フォームデータの設定
                form_data = MultiDict({
                    'fullname': 'John Doe',
                })

                # フォームデータを処理
                form.process(form_data)

                # フィールドの生成とデータの確認
                assert form is not None
                assert isinstance(form.fullname, StringField)
                # フィールドに設定された値を確認
                assert form.fullname.data == 'John Doe'
                # 値を出力して確認する
                print(f"Fullname: {form.fullname.data}")


        # 正常なプロフィール設定でselectフィールドが正しく生成されるかテスト
        profile_form2 = {
            'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
            'university': {'current_type': 'identifier', 'label_name': 'University', 'visible': True, 'select': ['']},
            'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
            'position': {'current_type': 'select', 'label_name': 'Position', 'visible': True, 'select': ['item1|item2|item3']}
        }

        with app.test_client():
            # AdminSettings.getをモックして、profile_formを返すようにする
            with patch('weko_admin.models.AdminSettings.get', return_value=profile_form2):
                print(f"formtext2:", profile_form2)
                # ProfileFormのインスタンスを作成
                form1 = ProfileForm()

                # フォームデータの設定
                form_data = MultiDict({
                    'position': 'item1',
                })

                # フォームデータを処理
                form1.process(form_data)

                # フィールドの生成とデータの確認
                assert form1 is not None
                assert isinstance(form1.position, SelectField)
                # フィールドに設定された値を確認
                assert form1.position.data == 'item1'
                # 値を出力して確認する
                print(f"Position: {form1.position.data}")


#    def validate_username(form, field):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::TestProfileForm::test_validate_username -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
    def test_validate_username(self,app,client,register_form,users,db):
        from weko_user_profiles.config import USERPROFILES_LANGUAGE_LIST, USERPROFILES_TIMEZONE_LIST
        from weko_user_profiles.validators import USERNAME_RULES

        app.config.update(
            USERNAME_RULES=USERNAME_RULES,
            USERPROFILES_LANGUAGE_LIST=USERPROFILES_LANGUAGE_LIST,
            USERPROFILES_TIMEZONE_LIST=USERPROFILES_TIMEZONE_LIST
        )
        user = users[0]["obj"]
        login(app,client,obj=user)
        data = {
            "timezone":'Etc/GMT',
            "language":"ja",
            "email":'sysadmin@test.org',
            "email_repeat":'sysadmin@test.org',
            "fullname":"test username",
            "university":"test university",
            "department":"test department",
            "position":"Professor",
            "phoneNumber":"12345",
            "institutePosition":"",
            "institutePosition2":"",
            "institutePosition3":"",
            "institutePosition4":"",
            "institutePosition5":""
        }

        profile_conf1 = {
                'fullname': {'current_type': 'text','label_name': 'Full Name', 'visible': True, 'select': ['']},
                'university': {'current_type': 'text','label_name': 'University', 'visible': True, 'select': ['']},
                'department': {'current_type': 'text','label_name': 'Department', 'visible': True, 'select': ['']},
                'position': {'current_type': 'select','label_name': 'Position', 'visible': True, 'select': ['item|item2|item3|Professor']}
        }
        #login_user(users[0]["obj"])
        user_profile1 = UserProfile(
            user_id=users[0]["id"],
            _username="sysadmin user",
            _displayname="sysadmin user",
        )
        db.session.add(user_profile1)
        user_profile2 = UserProfile(
            user_id=users[1]["id"],
            _username="repoadmin user",
            _displayname="repoadmin user",
        )
        db.session.add(user_profile2)
        db.session.commit()
        data["username"]="sysadmin user"
        with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf1.copy()):
            print(f"current_user:return_value",profile_conf1)
            res = client.post("/test_form/profile_form",data=data)
            assert res.data == bytes("OK","utf-8")
            logout(app,client)

            # current_userid!= userprofile.user_id,field.data!=current_userid

        with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf1.copy()):
            user = users[1]["obj"]
            login(app,client,obj=user)
            res = client.post("/test_form/profile_form",data=data)
            print(f"res.data",res.data)
            assert res.data == bytes('Username already exists.',"utf-8")

            # raise NoResultFound
        with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf1.copy()):
            data["username"]="other user"
            res = client.post("/test_form/profile_form",data=data)
            assert res.data == bytes("invalid","utf-8")

#class EmailProfileForm(ProfileForm):
#    def __init__(self, *args, **kwargs):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_EmailProfileForm -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_EmailProfileForm(app):
    
    profile_conf = {
        'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
        'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
        'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
        'position': {'current_type': 'select', 'label_name': 'Position', 'visible': True, 'select': ['item|item2|item3']}
    }

    # リスト以外の値を設定
    with app.app_context():
        with patch('weko_user_profiles.forms.current_app') as mock_current_app:
            mock_current_app.config = {'WEKO_USERPROFILES_FORM_COLUMN': 'not_a_list'}

            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
                form = EmailProfileForm(
                    formdata=None,
                    username="test",
                    fullname="test user",
                    timezone="Etc/GMT-9",
                    language="ja",
                    email="test@test.org",
                    email_repeat="test@test.org",
                    university="test university",
                    department="test department",
                    position="test position",
                    otherPosition="test other position",
                    phoneNumber="1234567",
                    instituteName="test institute",
                    institutePosition="test institute position",
                    instituteName2="test institute2",
                    institutePosition2="test institute position2",
                    instituteName3="",
                    institutePosition3="",
                    instituteName4="",
                    institutePosition4="",
                    instituteName5="",
                    institutePosition5=""
                )
                assert "username" in form.data
                assert "phoneNumber" not in form.data

        # リストの値を設定
        with patch('weko_user_profiles.forms.current_app') as mock_current_app:
            mock_current_app.config = {'WEKO_USERPROFILES_FORM_COLUMN': ['username', 'fullname', 'email']}

            with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
                form = EmailProfileForm(
                    formdata=None,
                    username="test",
                    fullname="test user",
                    timezone="Etc/GMT-9",
                    language="ja",
                    email="test@test.org",
                    email_repeat="test@test.org",
                    university="test university",
                    department="test department",
                    position="test position",
                    otherPosition="test other position",
                    phoneNumber="1234567",
                    instituteName="test institute",
                    institutePosition="test institute position",
                    instituteName2="test institute2",
                    institutePosition2="test institute position2",
                    instituteName3="",
                    institutePosition3="",
                    instituteName4="",
                    institutePosition4="",
                    instituteName5="",
                    institutePosition5=""
                )
                assert "username" in form.data
                assert "phoneNumber" not in form.data


#class VerificationForm(FlaskForm):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_verificationForm -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_verificationForm(client,register_form):
    url = "/test_form/verification_form"
    data = {"send_verification_email":""}
    res = client.post(url,data=data)
    assert res.data == bytes("OK","utf-8")


#def register_form_factory(Form):
#    class CsrfDisabledProfileForm(ProfileForm):
#        def __init__(self, *args, **kwargs):
#    class ConfirmRegisterForm(Form):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_register_form_factory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_register_form_factory(req_context):
    profile_conf = {
        'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
        'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
        'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
        'position': {'current_type': 'select', 'label_name': 'Position', 'visible': True, 'select': ['item|item2|item3']}
    }

    class TestForm(FlaskForm):
        text = StringField("Text")

    with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
        result = register_form_factory(TestForm)()

        assert 'profile' in result
        assert "text" in result
        assert 'csrf_token' not in result.profile
        assert 'csrf_token' not in result or result.csrf_token.data is None

        current_app.config.update(
            WTF_CSRF_ENABLED=True
        )
        result = register_form_factory(TestForm)()

        assert 'profile' in result
        assert "text" in result
        assert 'csrf_token' not in result.profile
        assert 'csrf_token' in result
        assert result.csrf_token

# def confirm_register_form_factory(Form)
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_confirm_register_form_factory -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_confirm_register_form_factory(req_context):
    class TestForm(FlaskForm):
        text = StringField("Text")
    profile_conf = {
        'fullname': {'current_type': 'text', 'label_name': 'Full Name', 'visible': True, 'select': ['']},
        'university': {'current_type': 'text', 'label_name': 'University', 'visible': True, 'select': ['']},
        'department': {'current_type': 'text', 'label_name': 'Department', 'visible': True, 'select': ['']},
        'position': {'current_type': 'select', 'label_name': 'Position', 'visible': True, 'select': ['item|item2|item3']}
    }
    with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
        result = confirm_register_form_factory(TestForm)()

        assert 'profile' in result
        assert "text" in result
        assert 'csrf_token' not in result.profile
        assert 'csrf_token' not in result or result.csrf_token.data is None

        current_app.config.update(
            WTF_CSRF_ENABLED=True
        )
        result = confirm_register_form_factory(TestForm)()

        assert 'profile' in result
        assert "text" in result
        assert 'csrf_token' not in result.profile
        assert 'csrf_token' in result
        assert result.csrf_token


#def _update_with_csrf_disabled(d=None):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_update_with_csrf_disabled -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_update_with_csrf_disabled():
    d = None
    result = _update_with_csrf_disabled(d)
    assert result == {"meta":{"csrf":False}}
    d = {"test_key":"test_value"}
    with patch("pkg_resources.parse_version",side_effect=[10,100]):
        result = _update_with_csrf_disabled(d)
        assert result == {"test_key":"test_value","csrf_enabled":False}
