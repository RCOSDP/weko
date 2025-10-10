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

from flask import current_app
from flask_babelex import lazy_gettext as _
from flask_login import current_user
from flask_security.forms import email_required, email_validator, \
    unique_user_email
from flask_wtf import FlaskForm
from sqlalchemy.orm.exc import NoResultFound
from wtforms.widgets import PasswordInput
from wtforms import FormField, HiddenField, SelectField, StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, EqualTo, StopValidation, \
    ValidationError

from .api import current_userprofile
from .config import USERPROFILES_LANGUAGE_LIST, USERPROFILES_TIMEZONE_LIST, WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, WEKO_USERPROFILES_POSITION_LIST
from .models import UserProfile
from .validators import USERNAME_RULES
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
    if field.data == "":
        return
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
    if form.position.data != current_app.config.get("WEKO_USERPROFILES_OTHERS_INPUT_DETAIL") \
        and not form.position.data in ["その他", "Others"]:
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
    if field.data == "None":
        return
    error_message = _('Only digits are allowed.')
    if not re.fullmatch(r'[0-9]*', field.data):
        raise ValidationError(error_message)


def custom_profile_form_factory(profile_cls):
    """Create a custom profile form class based on configuration settings.
    Args:
        profile_cls (class): Base profile form class to extend.
    Returns:
        class: A dynamically created ProfileForm class.
    """
    if not issubclass(profile_cls, ProfileForm):
        profile_cls = ProfileForm

    # Get profile configuration settings
    profile_setting = AdminSettings.get('profiles_items_settings', dict_to_object=False)

    # Create the ProfileForm class dynamically
    if profile_setting is None:
        if current_app.config.get("WEKO_USERPROFILES_DEFAULT_FIELDS_SETTINGS", {}):
            profile_setting = current_app.config.get("WEKO_USERPROFILES_DEFAULT_FIELDS_SETTINGS")
        else:
            raise ValueError("Could not retrieve profile configuration settings.")

    # Sort profile_setting by 'order' key
    sorted_profile_setting = OrderedDict(sorted(profile_setting.items(), key=lambda x: x[1].get("order", 0)))
    # Iterate over the sorted configuration and add fields to the form class
    for key, value in sorted_profile_setting.items():
        # Check if the field should be visible
        if value['visible']:
            field_format = value['format']
            # Create the field based on the current_type
            if field_format == 'select':
                # Check if format is select
                if not isinstance(value['options'], list):
                    raise ValueError(f"Invalid 'options' value in field: {key}")
                field = SelectField(
                    _(value['label_name']),
                    filters=[strip_filter],
                    choices=[('','')] + [(choice, _(choice)) for choice in value['options']]
                )
            elif field_format == 'identifier':
                # Check if the field is a identifier
                validators = [validate_digits]
                field = StringField(
                    _(value['label_name']),
                    validators=validators,
                    filters=[strip_filter]
                )
            elif field_format == 'text':
                # Check if the field is a text field
                validators = [check_length_100_characters]
                field = StringField(
                    _(value['label_name']),
                    validators=validators,
                    filters=[strip_filter]
                )
            elif field_format == 'phonenumber':
                # Check if the field is a phone number
                validators = [check_phone_number]
                field = StringField(
                    _(value['label_name']),
                    validators=validators,
                    filters=[strip_filter]
                )
            elif field_format == 'position(other)':
                # Check if the field is other position field
                validators = [check_other_position]
                field = StringField(
                    _(value['label_name']),
                    validators=validators,
                    filters=[strip_filter]
                )
            else:
                raise ValueError(f"Invalid 'format' value in field: {key}")
        else:
            field = HiddenField(_(value['label_name']))

        # Add the field to the ProfileForm class dynamically
        setattr(profile_cls, key, field)

    # Return the dynamically created ProfileForm class
    return profile_cls


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

    access_key = PasswordField(
        # NOTE: Form field label
        _('access key'),
        # NOTE: Form field help text
        description=_('Please enter if you use your own S3 Bucket.'),
        validators=[check_length_100_characters],
        filters=[strip_filter],
        widget=PasswordInput(hide_value=False),
    )

    secret_key = PasswordField(
        # NOTE: Form field label
        _('secret key'),
        # NOTE: Form field help text
        description=_('Please enter if you use your own S3 Bucket.'),
        validators=[check_length_100_characters],
        filters=[strip_filter],
        widget=PasswordInput(hide_value=False),
    )

    s3_endpoint_url = StringField(
        # NOTE: Form field label
        _('endpoint url'),
        # NOTE: Form field help text
        description=_('Please enter if you use your own S3 Bucket.'),
        validators=[check_length_100_characters],
        filters=[strip_filter],
    )

    s3_region_name = StringField(
        # NOTE: Form field label
        _('region name'),
        description=_('Please enter if you specify your own S3 Bucket region.'),
        # NOTE: Form field help text
        validators=[check_length_100_characters],
        filters=[strip_filter],
    )


    fullname = StringField(
        # NOTE: Form label
        _('Fullname'),
        validators=[
            DataRequired(message=_('Full name not provided.')),
            check_length_100_characters
        ],
        filters=[strip_filter])

    # University / Institution
    university = StringField(
        _('University/Institution'),
        validators=[
            DataRequired(message=_('University/Institution not provided.')),
            check_length_100_characters
        ],
        filters=[strip_filter]
    )

    # Affiliation department / Department
    department = StringField(
        _('Affiliated Division/Department'),
        validators=[
            DataRequired(
                message=_('Affiliated Division/Department not provided.')),
            check_length_100_characters
        ],
        filters=[strip_filter]
    )

    # Position
    position = SelectField(
        _('Position'),
        filters=[strip_filter],
        validators=[
            DataRequired(message=_('Position not provided.')),
        ],
        choices=WEKO_USERPROFILES_POSITION_LIST
    )

    # Other Position
    item1 = StringField(
        _('Position (Others)'),
        validators=[
            check_other_position
        ],
        render_kw={"placeholder": _("Input when selecting Others")}
    )

    # Phone number
    item2 = StringField(
        _('Phone number'),
        validators=[
            DataRequired(message=_('Phone number not provided.')),
            check_phone_number
        ]
    )

    # Affiliation institute 1
    # Affiliation institute name (n)
    item3 = StringField(
        _('Affiliated Institution Name'),
        validators=[
            check_length_100_characters
        ],
        filters=[strip_filter]
    )

    # Affiliation institute position (n)
    item4 = SelectField(
        _('Affiliated Institution Position'),
        filters=[strip_filter],
        choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    )

    # Affiliation institute 2
    # Affiliation institute name (n)
    item5 = StringField(
        _('Affiliated Institution Name'),
        validators=[
            check_length_100_characters
        ],
        filters=[strip_filter]
    )

    # Affiliation institute position (n)
    item6 = SelectField(
        _('Affiliated Institution Position'),
        filters=[strip_filter],
        choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    )

    # Affiliation institute 3
    # Affiliation institute name (n)
    item7 = StringField(
        _('Affiliated Institution Name'),
        validators=[
            check_length_100_characters
        ],
        filters=[strip_filter]
    )

    # Affiliation institute position (n)
    item8 = SelectField(
        _('Affiliated Institution Position'),
        filters=[strip_filter],
        choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    )

    # Affiliation institute 4
    # Affiliation institute name (n)
    item9 = StringField(
        _('Affiliated Institution Name'),
        validators=[
            check_length_100_characters
        ],
        filters=[strip_filter]
    )

    # Affiliation institute position (n)
    item10 = SelectField(
        _('Affiliated Institution Position'),
        filters=[strip_filter],
        choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    )

    # Affiliation institute 5
    # Affiliation institute name (n)
    item11 = StringField(
        _('Affiliated Institution Name'),
        validators=[
            check_length_100_characters
        ],
        filters=[strip_filter]
    )

    # Affiliation institute position (n)
    item12 = SelectField(
        _('Affiliated Institution Position'),
        filters=[strip_filter],
        choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    )


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
