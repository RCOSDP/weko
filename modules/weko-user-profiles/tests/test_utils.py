

from flask import current_app
from flask_wtf import FlaskForm
from flask_login.utils import login_user
from wtforms import SubmitField

from weko_user_profiles.forms import EmailProfileForm
from weko_user_profiles.api import current_userprofile
from weko_user_profiles.config import WEKO_USERPROFILES_POSITION_LIST
from weko_user_profiles.utils import (
    get_user_profile_info,
    handle_verification_form,
    handle_profile_form,
    get_role_by_position
)

# def get_user_profile_info(user_id):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_utils.py::test_get_user_profile_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_get_user_profile_info(users,user_profiles):
    user_id = user_profiles[0].user_id
    result = get_user_profile_info(user_id)
    test = {
        "subitem_fullname":"test taro",
        "subitem_displayname":"sysadmin user",
        "subitem_user_name":"sysadmin",
        "subitem_university/institution":"test university",
        "subitem_affiliated_division/department":"test department",
        "subitem_position":"test position",
        "subitem_phone_number":"123-4567",
        "subitem_position(others)":"test other position",
        "subitem_affiliated_institution":[
            {"subitem_affiliated_institution_name":"test institute","subitem_affiliated_institution_position":"test institute position"},
            {"subitem_affiliated_institution_name":"test institute2","subitem_affiliated_institution_position":"test institute position2"},
        ],
        'subitem_mail_address': 'sysadmin@test.org',
    }
    
    assert result == test


# def handle_verification_form(form):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_utils.py::test_handle_verification_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_handle_verification_form(app,mocker):
    mocker.patch("weko_user_profiles.utils.send_confirmation_instructions")
    class TestForm(FlaskForm):
        send_verification_email = SubmitField('Resend verification email')
    with app.test_request_context(method="POST",data={"send_verification_email":"test@test.org"}):
        form = TestForm(formdata=None,prefix="verification")
        mock_flash = mocker.patch("weko_user_profiles.utils.flash")
        handle_verification_form(form)
        mock_flash.assert_called_with("Verification email sent.",category="success")


# def handle_profile_form(form):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_utils.py::test_handle_profile_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_handle_profile_form(app,users,user_profiles,mocker):
    # WEKO_USERPROFILES_ROLE_MAPPING_ENABLED is false
    data = {
        "profile-username":"test_sysadmin",
        "profile-timezone":'Etc/GMT',
        "profile-language":"ja",
        "profile-email":'sysadmin@test.org',
        "profile-email_repeat":'sysadmin@test.org',
        "profile-fullname":"test username",
        "profile-university":"test university",
        "profile-department":"test department",
        "profile-position":"Professor",
        "profile-phoneNumber":"12-345",
        "profile-institutePosition":"",
        "profile-institutePosition2":"",
        "profile-institutePosition3":"",
        "profile-institutePosition4":"",
        "profile-institutePosition5":""
    }
    with app.test_request_context(method="POST",data = data):
        login_user(users[0]["obj"])
        userprofile = user_profiles[0]
        form = EmailProfileForm(
            formdata=None,
            username=userprofile.username,
            fullname=userprofile.fullname,
            timezone=userprofile.timezone,
            language=userprofile.language,
            email="sysadmin@test.org",
            email_repeat="sysadmin@test.org",
            university=userprofile.university,
            department=userprofile.department,
            position=userprofile.position,
            otherPosition=userprofile.otherPosition,
            phoneNumber=userprofile.phoneNumber,
            instituteName=userprofile.instituteName,
            institutePosition=userprofile.institutePosition,
            instituteName2=userprofile.instituteName2,
            institutePosition2=userprofile.institutePosition2,
            instituteName3=userprofile.instituteName3,
            institutePosition3=userprofile.institutePosition3,
            instituteName4=userprofile.instituteName4,
            institutePosition4=userprofile.institutePosition4,
            instituteName5=userprofile.instituteName5,
            institutePosition5=userprofile.institutePosition5,
            prefix='profile', )
        mock_flash = mocker.patch("weko_user_profiles.utils.flash")
        handle_profile_form(form)
        mock_flash.assert_called_with('Profile was updated.',category="success")
        assert current_userprofile.timezone == "Etc/GMT"
        assert current_userprofile.username == "test_sysadmin"
    
    # changed email
    current_app.config.update(
        WEKO_USERPROFILES_ROLE_MAPPING_ENABLED=True
    )
    data = {
        "profile-username":"test_repoadmin",
        "profile-timezone":'Etc/GMT',
        "profile-language":"ja",
        "profile-email":'new_repoadmin@test.org',
        "profile-email_repeat":'new_repoadmin@test.org',
        "profile-fullname":"test username",
        "profile-university":"test university",
        "profile-department":"test department",
        "profile-position":"Professor",
        "profile-phoneNumber":"12-345",
        "profile-institutePosition":"",
        "profile-institutePosition2":"",
        "profile-institutePosition3":"",
        "profile-institutePosition4":"",
        "profile-institutePosition5":""
    }
    with app.test_request_context(method="POST",data=data):
        login_user(users[1]["obj"])
        userprofile = user_profiles[1]
        form = EmailProfileForm(
            formdata=None,
            username=userprofile.username,
            fullname=userprofile.fullname,
            timezone=userprofile.timezone,
            language=userprofile.language,
            email="repoadmin@test.org",
            email_repeat="repoadmin@test.org",
            university=userprofile.university,
            department=userprofile.department,
            position=userprofile.position,
            otherPosition=userprofile.otherPosition,
            phoneNumber=userprofile.phoneNumber,
            instituteName=userprofile.instituteName,
            institutePosition=userprofile.institutePosition,
            instituteName2=userprofile.instituteName2,
            institutePosition2=userprofile.institutePosition2,
            instituteName3=userprofile.instituteName3,
            institutePosition3=userprofile.institutePosition3,
            instituteName4=userprofile.instituteName4,
            institutePosition4=userprofile.institutePosition4,
            instituteName5=userprofile.instituteName5,
            institutePosition5=userprofile.institutePosition5,
            prefix='profile', )
        mock_flash = mocker.patch("weko_user_profiles.utils.flash")
        mock_send = mocker.patch("weko_user_profiles.utils.send_confirmation_instructions")
        mocker.patch("weko_user_profiles.utils.get_role_by_position",return_value="Original Role")
        handle_profile_form(form)
        mock_flash.assert_called_with("Profile was updated. We have sent a verification email to new_repoadmin@test.org. Please check it.",category="success")
        mock_send.assert_called_once()


    # validate_on_submit is false
    data = {}
    with app.test_request_context(method="POST",data=data):
        login_user(users[1]["obj"])
        form = EmailProfileForm(
            formdata=None,
            username=userprofile.username,
            fullname=userprofile.fullname,
            timezone=userprofile.timezone,
            language=userprofile.language,
            email="repoadmin@test.org",
            email_repeat="repoadmin@test.org",
            university=userprofile.university,
            department=userprofile.department,
            position=userprofile.position,
            otherPosition=userprofile.otherPosition,
            phoneNumber=userprofile.phoneNumber,
            instituteName=userprofile.instituteName,
            institutePosition=userprofile.institutePosition,
            instituteName2=userprofile.instituteName2,
            institutePosition2=userprofile.institutePosition2,
            instituteName3=userprofile.instituteName3,
            institutePosition3=userprofile.institutePosition3,
            instituteName4=userprofile.instituteName4,
            institutePosition4=userprofile.institutePosition4,
            instituteName5=userprofile.instituteName5,
            institutePosition5=userprofile.institutePosition5,
            prefix='profile', )
        handle_profile_form(form)


# def get_role_by_position(position):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_utils.py::test_get_role_by_position -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_get_role_by_position(client):
    # enable_mapping is false
    result = get_role_by_position("test position")
    assert result == None
    
    current_app.config.update(
        WEKO_USERPROFILES_ROLE_MAPPING_ENABLED=True,
        WEKO_USERPROFILES_ROLE_MAPPING={
            "WEKO_USERPROFILES_POSITION_LIST_GENERAL":"WEKO_USERPROFILES_GENERAL_ROLE",
            "WEKO_USERPROFILES_POSITION_LIST_GRADUATED_STUDENT":"WEKO_USERPROFILES_GRADUATED_STUDENT_ROLE",
            "WEKO_USERPROFILES_POSITION_LIST_STUDENT":"WEKO_USERPROFILES_STUDENT_ROLE"
        }
    )
    
    # position in WEKO_USERPROFILES_POSITION_LIST_GENERAL
    result = get_role_by_position("Full-time Instructor")
    assert result == "General"
    
    # position in WEKO_USERPROFILES_POSITION_LIST_GRADUATED_STUDENT
    result = get_role_by_position("Listener")
    assert result == "Graduated Student"
    
    # position in WEKO_USERPROFILES_POSITION_LIST_STUDENT
    result = get_role_by_position("Student")
    assert result == "Student"
    
    current_app.config.update(
        WEKO_USERPROFILES_POSITION_LIST=WEKO_USERPROFILES_POSITION_LIST+[("test position","test position")]
    )
    # position not in GENERAL,GRADUATED_STUDENT,STUDENT
    result = get_role_by_position("test position")
    assert result == None
    
    current_app.config.update(
        WEKO_USERPROFILES_POSITION_LIST="not current setting"
    )
    # WEKO_USERPROFILES_POSITION_LIST is not list
    result = get_role_by_position("test position")
    assert result == None