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

"""Forms for user profiles."""

import re

from flask import current_app, Flask
from flask_babelex import lazy_gettext as _
from flask_login import current_user
from flask_security.forms import email_required, email_validator, \
    unique_user_email
from flask_wtf import FlaskForm
from sqlalchemy.orm.exc import NoResultFound
from wtforms import FormField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, StopValidation, \
    ValidationError

from .api import current_userprofile
from .config import USERPROFILES_LANGUAGE_LIST, USERPROFILES_TIMEZONE_LIST, \
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_OTHERS_INPUT_DETAIL, WEKO_USERPROFILES_POSITION_LIST
from .models import UserProfile
from .validators import USERNAME_RULES, validate_username
from weko_admin.models import AdminSettings
from collections import OrderedDict

def strip_filter(text):
    """Filter for trimming whitespace.

    :param text: The text to strip.
    :returns: The stripped text.
    """
    return text.strip() if text else text


def current_user_email(form, field):
    """Field validator to stop validation if email wasn't changed."""
    if current_user.email == field.data:
        raise StopValidation()


def check_length_100_characters(form, field):
    """Check length 100.

    :param form:
    :param field:
    """
    if len(field.data) > 100:
        raise ValidationError(_("Text field must be less than 100 characters."))


def check_phone_number(form, field):
    """Validate phone number.

    @param form:
    @param field:
    """
    if len(field.data) > 15:
        raise ValidationError('Phone number must be less than 15 characters.')
    field = field.data.split("-")
    if not all([x.isdigit() for x in field]):
        raise ValidationError(_('Phone Number format is incorrect.'))

def check_other_position(form, field):
    """Check other position.

    @param form:
    @param field:
    """
    #設定されたリストに存在するOthersではなく、文字列としての【その他】もしくは【Others】を判別するバリデーション
    if not form.position.data in ["その他", "Others"]:
        if len(strip_filter(field.data)) > 0:
            raise ValidationError(_("Position is being inputted "
                                    "(Only input when selecting 'Others')"))
    else:
        if len(strip_filter(field.data)) == 0:
            raise ValidationError(_('Position not provided.'))
        

#識別子を判別するためのバリデーション
def validate_digits(form, field):
    """Validate digits.

    @param form:
    @param field:
    """

    error_message = _('Only digits are allowed.')
    if not re.fullmatch(r'[0-9]*', field.data):
        raise ValidationError(error_message)

app = Flask(__name__)

class ProfileForm(FlaskForm):
    """Form for editing user profile."""

    username = StringField(
        # NOTE: Form field label
        _('Username'),
        # NOTE: Form field help text
        description=_('Required. %(username_rules)s',
                      username_rules=USERNAME_RULES),
        validators=[DataRequired(message=_('Username not provided.'))],
        filters=[strip_filter], )

    timezone = SelectField(
        # NOTE: Form label
        _('Timezone'),
        filters=[strip_filter],
        choices=USERPROFILES_TIMEZONE_LIST,
    )

    language = SelectField(
        # NOTE: Form label
        _('Language'),
        filters=[strip_filter],
        choices=USERPROFILES_LANGUAGE_LIST,
    )

    email = StringField(
        # NOTE: Form field label
        _('Email address'),
        filters=[lambda x: x.lower() if x is not None else x, ],
        validators=[
            email_required,
            current_user_email,
            email_validator,
            unique_user_email,
        ],
    )

    email_repeat = StringField(
        # NOTE: Form field label
        _('Re-enter email address'),
        # NOTE: Form field help text
        description=_('Please re-enter your email address.'),
        filters=[lambda x: x.lower() if x else x, ],
        validators=[
            email_required,
            # NOTE: Form validation error.
            EqualTo('email', message=_('Email addresses do not match.'))
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # アプリケーションコンテキスト内でデータベースクエリを実行
        profile_conf = AdminSettings.get('profiles_items_settings', dict_to_object=False)

        if profile_conf is None:
            raise ValueError("Could not retrieve profile configuration settings.")
        
        # プロフィール設定の表示設定を取得
        self.field_visibility = {}

        # 順序を指定して OrderedDict に変換
        ordered_profile_conf = OrderedDict()

        # 固定されたキーを最初に追加
        fix_keys = ["fullname", "university", "department", "position"]
        missing_keys = []

        for key in fix_keys:
            if key in profile_conf:
                ordered_profile_conf[key] = profile_conf.get(key)
            else:
                missing_keys.append(key)
        if missing_keys:
            raise KeyError("Could not find the following keys in profile configuration settings: {}".format(missing_keys))

        # 固定キー以外を追加
        ordered_profile_conf.update(profile_conf)

        # それぞれのフィールドに取得したアイテムデータを設定
        required_keys = ['current_type', 'label_name', 'visible', 'select']
        for key, value in ordered_profile_conf.items():
            missing_fieldkeys = [k for k in required_keys if k not in value]
            if missing_fieldkeys:
                raise KeyError(f"Missing required key(s) {missing_fieldkeys} in field: {key}")

            self.field_visibility[key] = value['visible']

            if value['current_type'] == 'select':
                if not isinstance(value['select'], list):
                    raise ValueError(f"Invalid 'select' value in field: {key}")
                field = SelectField(
                    _(value['label_name']),
                    filters=[strip_filter],
                    choices=[(choice, choice) for choice in value['select'][0].split('|')]
                )
                setattr(ProfileForm, key, field)
            elif value['current_type'] == 'identifier':
                validators = [validate_digits]
                field = StringField(
                    _(value['label_name']),
                    validators=validators,
                    filters=[strip_filter]
                )
                setattr(ProfileForm, key, field)
            elif value['current_type'] == 'text':
                validators = [check_length_100_characters]
                field = StringField(
                    _(value['label_name']),
                    validators=validators,
                    filters=[strip_filter]
                )
                setattr(ProfileForm, key, field)
            else:
                raise ValueError(f"Invalid 'current_type' value in field: {key}")

    def validate_username(form, field):
        """Wrap username validator for WTForms."""
        try:
            user_profile = UserProfile.get_by_username(field.data)
            if current_userprofile.is_anonymous or \
                    (current_userprofile.user_id != user_profile.user_id
                     and field.data != current_userprofile.username):
                # NOTE: Form validation error.
                raise ValidationError(_('Username already exists.'))
        except NoResultFound:
            return

class EmailProfileForm(ProfileForm):
    """Form to allow editing of email address."""

    def __init__(self, *args, **kwargs):
        """Initial Profile Form.

        @param args:
        @param kwargs:
        """
        super().__init__(*args, **kwargs)
        form_column = current_app.config['WEKO_USERPROFILES_FORM_COLUMN']
        disable_column_lst = list()
        if isinstance(form_column, list):
            for key in kwargs:
                if key not in form_column:
                    disable_column_lst.append(key)

            for key in disable_column_lst:
                if hasattr(self, key):
                    delattr(self, key)


class VerificationForm(FlaskForm):
    """Form to render a button to request email confirmation."""

    # NOTE: Form button label
    send_verification_email = SubmitField(_('Resend verification email'))


def register_form_factory(Form):
    """Factory for creating an extended user registration form."""
    class CsrfDisabledProfileForm(ProfileForm):
        """Subclass of ProfileForm to disable CSRF token in the inner form.

        This class will always be a inner form field of the parent class
        `Form`. The parent will add/remove the CSRF token in the form.
        """

        def __init__(self, *args, **kwargs):
            """Initialize the object by hardcoding CSRF token to false."""
            kwargs = _update_with_csrf_disabled(kwargs)
            super(CsrfDisabledProfileForm, self).__init__(*args, **kwargs)

    class RegisterForm(Form):
        """RegisterForm extended with UserProfile details."""

        profile = FormField(CsrfDisabledProfileForm, separator='.')

    return RegisterForm


def confirm_register_form_factory(Form):
    """Factory for creating a confirm register form."""
    class CsrfDisabledProfileForm(ProfileForm):
        """Subclass of ProfileForm to disable CSRF token in the inner form.

        This class will always be a inner form field of the parent class
        `Form`. The parent will add/remove the CSRF token in the form.
        """

        def __init__(self, *args, **kwargs):
            """Initialize the object by hardcoding CSRF token to false."""
            kwargs = _update_with_csrf_disabled(kwargs)
            super(CsrfDisabledProfileForm, self).__init__(*args, **kwargs)

    class ConfirmRegisterForm(Form):
        """RegisterForm extended with UserProfile details."""

        profile = FormField(CsrfDisabledProfileForm, separator='.')

    return ConfirmRegisterForm


def _update_with_csrf_disabled(d=None):
    """Update the input dict with CSRF disabled depending on WTF-Form version.

    From Flask-WTF 0.14.0, `csrf_enabled` param has been deprecated in favor of
    `meta={csrf: True/False}`.
    """
    if d is None:
        d = {}

    import flask_wtf
    from pkg_resources import parse_version
    supports_meta = parse_version(flask_wtf.__version__) >= parse_version(
        "0.14.0")
    if supports_meta:
        d.setdefault('meta', {})
        d['meta'].update({'csrf': False})
    else:
        d['csrf_enabled'] = False
    return d
