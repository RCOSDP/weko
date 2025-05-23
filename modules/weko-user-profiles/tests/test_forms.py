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

from wtforms import StringField
from wtforms.validators import StopValidation,ValidationError

from flask import Blueprint, current_app
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
    EmailProfileForm
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
def test_check_other_position():
    class MockForm:
        def __init__(self,data):
            self.position = self.MockPosition(data)
        class MockPosition:
            def __init__(self,data):
                self.data = data
    
    # form.position.data is not "Others (Input Detail)"
    form = MockForm("test form")
    ## field.data > 0
    field = MockData("test data")
    with pytest.raises(ValidationError) as e:
        check_other_position(form,field)
        assert str(e) == "Position is being inputted (Only input when selecting 'Others')"
        
    ## field.data <= 0
    field = MockData("")
    check_other_position(form,field)
    
    # form.position.data is "Others (Input Detail)"
    form = MockForm("Others (Input Detail)")
    ## field.data == 0
    field = MockData("")
    with pytest.raises(ValidationError) as e:
        check_other_position(form,field)
        assert str(e) == 'Position not provided.'
    
    ## field.data != 0
    field = MockData("test data")
    check_other_position(form,field)


#class ProfileForm(FlaskForm):
class TestProfileForm:
#    def validate_username(form, field):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::TestProfileForm::test_validate_username -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
    def test_validate_username(self,app,client,register_form,users,db):
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
            "phoneNumber":"12-345",
            "institutePosition":"",
            "institutePosition2":"",
            "institutePosition3":"",
            "institutePosition4":"",
            "institutePosition5":""
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
        res = client.post("/test_form/profile_form",data=data)
        assert res.data == bytes("OK","utf-8")
        logout(app,client)
        
        
        # current_userid!= userprofile.user_id,field.data!=current_userid
        user = users[1]["obj"]
        login(app,client,obj=user)
        
        res = client.post("/test_form/profile_form",data=data)
        assert res.data == bytes('Username already exists.',"utf-8")
        
        # raise NoResultFound
        data["username"]="other user"
        res = client.post("/test_form/profile_form",data=data)
        assert res.data == bytes("invalid","utf-8")


#class EmailProfileForm(ProfileForm):
#    def __init__(self, *args, **kwargs):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_forms.py::test_EmailProfileForm -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_EmailProfileForm(app):

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
            position = "test position",
            otherPosition="test other position",
            phoneNumber="123-4567",
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
    class TestForm(FlaskForm):
        text = StringField("Text")
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
    result = confirm_register_form_factory(TestForm)()
    
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
