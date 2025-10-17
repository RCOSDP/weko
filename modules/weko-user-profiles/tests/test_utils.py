

from flask import current_app,Flask
from flask_wtf import FlaskForm
from flask_login.utils import login_user
from wtforms import SubmitField

from weko_user_profiles.forms import EmailProfileForm, ProfileForm
from weko_user_profiles.api import current_userprofile
from weko_user_profiles.config import WEKO_USERPROFILES_POSITION_LIST
from weko_user_profiles.utils import (
    get_user_profile_info,
    handle_verification_form,
    handle_profile_form,
    get_role_by_position
)
import pytest
from unittest.mock import patch, MagicMock
from weko_user_profiles.models import UserProfile
from invenio_accounts.models import User
from flask_sqlalchemy import SQLAlchemy

# def get_user_profile_info(user_id):
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_utils.py::test_get_user_profile_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp

@pytest.fixture()
def setup_data(db):
    # Create a user
    user = User(
        email="sysadmin@test.org",
        active=True
    )
    db.session.add(user)
    db.session.commit()

    # Create a user profile
    profile = UserProfile(
        user_id=user.id,
        _username="sysadmin",
        _displayname="sysadmin user",
        fullname="test taro",
        timezone="Etc/GMT",
        language="ja",
        university="test university",
        department="test department",
        position="test position",
        item1="test other position",
        item2="123-4567",
        item3="test institute",
        item4="test institute position",
        item5="test institute2",
        item6="test institute position2",
        item7="test institute3",
        item8="test institute position3",
        item9="test institute4",
        item10="test institute position4",
        item11="test institute5",
        item12="test institute position5",
        item13="item 13",
        item14="item 14",
        item15="item 15",
        item16="item 16"
    )
    db.session.add(profile)
    db.session.commit()

    return {'user': user, 'profile': profile}

def test_get_user_profile_info(setup_data):
    user_id = setup_data['profile'].user_id

    # 正常系
    profile_conf = {
        'fullname': {'visible': True},
        'displayname': {'visible': True},
        'username': {'visible': True},
        'university': {'visible': True},
        'department': {'visible': True},
        'position': {'visible': True},
        'item1': {'visible': True},
        'item2': {'visible': True},
        'item3': {'visible': True},
        'item4': {'visible': True},
        'item5': {'visible': True},
        'item6': {'visible': True},
        'item7': {'visible': True},
        'item8': {'visible': True},
        'item9': {'visible': True},
        'item10': {'visible': True},
        'item11': {'visible': True},
        'item12': {'visible': True},
        'item13': {'visible': True},
        'item14': {'visible': True},
        'item15': {'visible': True},
        'item16': {'visible': True}
    }

    with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
        result = get_user_profile_info(user_id)
        expected = {
            "subitem_fullname": "test taro",
            "subitem_displayname": "sysadmin user",
            "subitem_user_name": "sysadmin",
            "subitem_university/institution": "test university",
            "subitem_affiliated_division/department": "test department",
            "subitem_position": "test position",
            "subitem_phone_number": "123-4567",
            "subitem_position(others)": "test other position",
            "subitem_affiliated_institution": [
                {"subitem_affiliated_institution_name": "test institute", "subitem_affiliated_institution_position": "test institute position"},
                {"subitem_affiliated_institution_name": "test institute2", "subitem_affiliated_institution_position": "test institute position2"},
                {"subitem_affiliated_institution_name": "test institute3", "subitem_affiliated_institution_position": "test institute position3"},
                {"subitem_affiliated_institution_name": "test institute4", "subitem_affiliated_institution_position": "test institute position4"},
                {"subitem_affiliated_institution_name": "test institute5", "subitem_affiliated_institution_position": "test institute position5"}
            ],
            'subitem_mail_address': 'sysadmin@test.org',
        }
        assert result == expected

    profile_conf2 = {
        'fullname': {'visible': False},
        'displayname': {'visible': False},
        'username': {'visible': False},
        'university': {'visible': False},
        'department': {'visible': False},
        'position': {'visible': False},
        'item1': {'visible': False},
        'item2': {'visible': False},
        'item3': {'visible': False},
        'item4': {'visible': False},
        'item5': {'visible': False},
        'item6': {'visible': False},
        'item7': {'visible': False},
        'item8': {'visible': False},
        'item9': {'visible': False},
        'item10': {'visible': False},
        'item11': {'visible': False},
        'item12': {'visible': False},
        'item13': {'visible': False},
        'item14': {'visible': False},
        'item15': {'visible': False},
        'item16': {'visible': False}
    }

    with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf2):
        result = get_user_profile_info(user_id)
        expected = {
            "subitem_fullname": "",
            "subitem_displayname": "",
            "subitem_user_name": "",
            "subitem_university/institution": "",
            "subitem_affiliated_division/department": "",
            "subitem_position": "",
            "subitem_phone_number": "",
            "subitem_position(others)": "",
            "subitem_affiliated_institution": [],
            'subitem_mail_address': 'sysadmin@test.org',
        }
        assert result == expected

    # ユーザープロファイルが存在しない場合のテスト
    with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf), \
         patch('weko_user_profiles.models.UserProfile.get_by_userid', return_value=None):
        result = get_user_profile_info(user_id)
        expected = {
            'subitem_user_name': '',
            'subitem_mail_address': 'sysadmin@test.org',
            'subitem_displayname': '',
            'subitem_university/institution': '',
            'subitem_affiliated_division/department': '',
            'subitem_position': '',
            'subitem_phone_number': '',
            'subitem_position(others)': '',
            'subitem_affiliated_institution': []
        }
        assert result == expected

    # institute_dict_dataが空の場合のテスト
    with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf), \
    patch('weko_user_profiles.models.UserProfile.get_by_userid', return_value=setup_data['profile']), \
    patch('weko_user_profiles.models.UserProfile.get_institute_data', return_value=[]):
        result = get_user_profile_info(user_id)
        expected = {
            'subitem_user_name': 'sysadmin',
            'subitem_mail_address': 'sysadmin@test.org',
            'subitem_displayname': 'sysadmin user',
            'subitem_university/institution': 'test university',
            'subitem_affiliated_division/department': 'test department',
            'subitem_position': 'test position',
            'subitem_phone_number': '123-4567',
            'subitem_position(others)': 'test other position',
            'subitem_affiliated_institution': [],
            'subitem_fullname': 'test taro'
        }
        assert result == expected

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
# .tox/c1/bin/pytest --cov=weko_user_profiles tests/test_utils.py::test_handle_profile_form -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-user-profiles/.tox/c1/tmp
def test_handle_profile_form(app, users, user_profiles, mocker):
    # WEKO_USERPROFILES_ROLE_MAPPING_ENABLED is false
    data = {
        "profile-username": "test_sysadmin",
        "profile-timezone": 'Etc/GMT',
        "profile-language": "ja",
        "profile-email": 'sysadmin@test.org',
        "profile-email_repeat": 'sysadmin@test.org',
        "profile-fullname": "test username",
        "profile-university": "test university",
        "profile-department": "test department",
        "profile-position": "Professor",
        "profile-phoneNumber": "12-345",
        "profile-institutePosition": "",
        "profile-institutePosition2": "",
        "profile-institutePosition3": "",
        "profile-institutePosition4": "",
        "profile-institutePosition5": ""
    }

    profile_conf = {
        "item1": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "役職（その他）", "current_type": "text"},
        "item2": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "電話番号", "current_type": "identifier"},
        "item3": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "所属学会名", "current_type": "text"},
        "item4": {"type": ["text", "identifier", "select"], "select": ["a|b|c"], "visible": False, "label_name": "所属学会役職", "current_type": "select"},
        "item5": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "所属学会名", "current_type": "text"},
        "item6": {"type": ["text", "identifier", "select"], "select": ["a|b|c"], "visible": False, "label_name": "所属学会役職", "current_type": "select"},
        "item7": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "所属学会名", "current_type": "text"},
        "item8": {"type": ["text", "identifier", "select"], "select": ["a|b|c"], "visible": False, "label_name": "所属学会役職", "current_type": "select"},
        "item9": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "所属学会名", "current_type": "text"},
        "item10": {"type": ["text", "identifier", "select"], "select": ["a|b|c"], "visible": False, "label_name": "所属学会役職", "current_type": "select"},
        "item11": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "所属学会名", "current_type": "text"},
        "item12": {"type": ["text", "identifier", "select"], "select": ["a|b|c"], "visible": False, "label_name": "所属学会役職", "current_type": "select"},
        "fullname": {"type": ["text", "identifier", "select"], "select": [""], "visible": True, "label_name": "氏名", "current_type": "text"},
        "position": {"type": ["text", "identifier", "select"], "select": ["a|b|c"], "visible": False, "label_name": "役職", "current_type": "text"},
        "department": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "所属部局・部署", "current_type": "text"},
        "university": {"type": ["text", "identifier", "select"], "select": [""], "visible": False, "label_name": "大学・機関名", "current_type": "text"}
    }

    with app.test_request_context(method="POST", data=data):
        with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
            login_user(users[0]["obj"])
            userprofile = user_profiles[0]
            form = EmailProfileForm(
                formdata=None,
                username=userprofile._username,
                fullname=userprofile.fullname,
                timezone=userprofile.timezone,
                language=userprofile.language,
                email="sysadmin@test.org",
                email_repeat="sysadmin@test.org",
                university=userprofile.university,
                department=userprofile.department,
                position=userprofile.position,
                item1=userprofile.item1,
                item2=userprofile.item2,
                item3=userprofile.item3,
                item4=userprofile.item4,
                item5=userprofile.item5,
                item6=userprofile.item6,
                item7=userprofile.item7,
                item8=userprofile.item8,
                item9=userprofile.item9,
                item10=userprofile.item10,
                item11=userprofile.item11,
                item12=userprofile.item12,
                prefix='profile',
            )
            mock_flash = mocker.patch("weko_user_profiles.utils.flash")
            handle_profile_form(form)
            mock_flash.assert_called_with('Profile was updated.', category="success")
            assert userprofile.timezone == "Etc/GMT"
            assert userprofile._username == "sysadmin"

    # validate_on_submit is false
    data = {
        "profile-username": "",
        "profile-timezone": '',
        "profile-language": "",
        "profile-email": '',
        "profile-email_repeat": '',
        "profile-fullname": "",
        "profile-university": "",
        "profile-department": "",
        "profile-position": "",
        "profile-phoneNumber": "",
        "profile-institutePosition": "",
        "profile-institutePosition2": "",
        "profile-institutePosition3": "",
        "profile-institutePosition4": "",
        "profile-institutePosition5": ""
    }
    with app.test_request_context(method="POST", data=data):
        with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
            login_user(users[1]["obj"])
            form = ProfileForm(
                formdata=None,
                username=userprofile._username,
                fullname=userprofile.fullname,
                timezone=userprofile.timezone,
                language=userprofile.language,
                email="repoadmin@test.org",
                email_repeat="repoadmin@test.org",
                university=userprofile.university,
                department=userprofile.department,
                position=userprofile.position,
                item1=userprofile.item1,
                item2=userprofile.item2,
                item3=userprofile.item3,
                item4=userprofile.item4,
                item5=userprofile.item5,
                item6=userprofile.item6,
                item7=userprofile.item7,
                item8=userprofile.item8,
                item9=userprofile.item9,
                item10=userprofile.item10,
                item11=userprofile.item11,
                item12=userprofile.item12,
                prefix='profile',
            )
            mock_flash = mocker.patch("weko_user_profiles.utils.flash")
            handle_profile_form(form)
            mock_flash.assert_not_called()
    # changed email
    current_app.config.update(
        WEKO_USERPROFILES_ROLE_MAPPING_ENABLED=True,
        USERPROFILES_EMAIL_ENABLED=True
    )
    data = {
        "profile-username": "test_repoadmin",
        "profile-timezone": 'Etc/GMT',
        "profile-language": "ja",
        "profile-email": 'new_repoadmin@test.org',
        "profile-email_repeat": 'new_repoadmin@test.org',
        "profile-fullname": "test username",
        "profile-university": "test university",
        "profile-department": "test department",
        "profile-position": "Professor",
        "profile-phoneNumber": "12-345",
        "profile-item4": "",
        "profile-item6": "",
        "profile-item8": "",
        "profile-item10": "",
        "profile-item12": ""
    }

    with app.test_request_context(method="POST", data=data):
        with patch('weko_admin.models.AdminSettings.get', return_value=profile_conf):
            login_user(users[1]["obj"])
            userprofile = user_profiles[1]
            form = EmailProfileForm(
                formdata=None,
                username=userprofile._username,
                fullname=userprofile.fullname,
                timezone=userprofile.timezone,
                language=userprofile.language,
                email="repoadmin@test.org",
                email_repeat="repoadmin@test.org",
                university=userprofile.university,
                department=userprofile.department,
                position=userprofile.position,
                item1=userprofile.item1,
                item2=userprofile.item2,
                item3=userprofile.item3,
                item4=userprofile.item4,
                item5=userprofile.item5,
                item6=userprofile.item6,
                item7=userprofile.item7,
                item8=userprofile.item8,
                item9=userprofile.item9,
                item10=userprofile.item10,
                item11=userprofile.item11,
                item12=userprofile.item12,
                prefix='profile',
            )
            mock_flash = mocker.patch("weko_user_profiles.utils.flash")
            mocker.patch("weko_user_profiles.utils.get_role_by_position", return_value="Original Role")
            handle_profile_form(form)
            mock_flash.assert_called_with(
                'Profile was updated. We have sent a verification email to new_repoadmin@test.org. Please check it.',
                category="success"
            )
    data = {
        "profile-username": "test_repoadmin",
        "profile-timezone": 'Etc/GMT',
        "profile-language": "ja",
        "profile-email": 'new_repoadmin@test.org',
        "profile-email_repeat": 'new_repoadmin@test.org',
        "profile-fullname": "test username",
        "profile-university": "test university",
        "profile-department": "test department",
        "profile-position": "Professor",
        "profile-phoneNumber": "12-345",
        "profile-item4": "",
        "profile-item6": "",
        "profile-item8": "",
        "profile-item10": "",
        "profile-item12": ""
    }


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