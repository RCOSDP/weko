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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""weko-user-profile utils."""
from flask import current_app, flash, request
from flask_babelex import lazy_gettext as _
from flask_login import current_user
from flask_security.confirmable import send_confirmation_instructions
from invenio_accounts.models import Role
from invenio_db import db

from .api import current_userprofile
from .models import UserProfile
from weko_admin.models import AdminSettings


def get_user_profile_info(user_id):
    """Get user profile information.
    Args:
        user_id (int): User ID
    Returns:
        dict: User profile information
    """
    result = {
        'subitem_user_name': '',
        'subitem_mail_address': '',
        'subitem_displayname': '',
        'subitem_university/institution': '',
        'subitem_affiliated_division/department': '',
        'subitem_position': '',
        'subitem_phone_number': '',
        'subitem_position(others)': '',
        'subitem_affiliated_institution': [],
    }
    user_info = UserProfile.get_by_userid(int(user_id))

    # get setting from admin settings
    profile_setting = AdminSettings.get('profiles_items_settings', dict_to_object=False)
    if not profile_setting:
        profile_setting = current_app.config.get("WEKO_USERPROFILES_DEFAULT_FIELDS_SETTINGS", {})

    # get user profile visible setting
    if user_info is not None:
        result['subitem_fullname'] = user_info.fullname if profile_setting.get('fullname', {}).get('visible', True) else ''
        result['subitem_displayname'] = user_info._displayname if profile_setting.get('displayname', {}).get('visible', True) else ''
        result['subitem_user_name'] = user_info.get_username if profile_setting.get('username', {}).get('visible', True) else ''
        result['subitem_university/institution'] = user_info.university if profile_setting.get('university', {}).get('visible', True) else ''
        result['subitem_affiliated_division/department'] = user_info.department if profile_setting.get('department', {}).get('visible', True) else ''
        result['subitem_position'] = user_info.position if profile_setting.get('position', {}).get('visible', True) else ''
        result['subitem_position(others)'] = user_info.item1 if profile_setting.get('item1', {}).get('visible', True) else ''
        result['subitem_phone_number'] = user_info.item2 if profile_setting.get('item2', {}).get('visible', True) else ''
        subitem_affiliated_institution = []
        institute_dict_data = user_info.get_institute_data()
        for institution_info in institute_dict_data:
            if institution_info and institution_info.get('subitem_affiliated_institution_name') != '':
                subitem_affiliated_institution.append(institution_info)
        result['subitem_affiliated_institution'] = subitem_affiliated_institution
    from invenio_accounts.models import User
    user = User()
    data = user.query.filter_by(id=user_id).one_or_none()
    if data is not None:
        result['subitem_mail_address'] = data.email
        return result


def handle_verification_form(form):
    """Handle email sending verification form."""
    form.process(formdata=request.form)

    if form.validate_on_submit():
        send_confirmation_instructions(current_user)
        # NOTE: Flash message.
        flash(_("Verification email sent."), category="success")


def handle_profile_form(form):
    """Handle profile update form."""
    form.process(formdata=request.form)

    if form.validate_on_submit():
        email_changed = False
        with db.session.begin_nested():
            # Update profile.
            for key in form.__dict__:
                if getattr(form, key) and hasattr(current_userprofile, key):
                    form_data = getattr(form, key).data
                    setattr(current_userprofile, key, form_data)
            # Mapping role
            current_config = current_app.config
            if (current_config['WEKO_USERPROFILES_ROLE_MAPPING_ENABLED']
                    and current_userprofile.position):
                role_name = get_role_by_position(current_userprofile.position)
                roles1 = db.session.query(Role).filter_by(
                    name=role_name).all()
                admin_role = current_config.get(
                    "WEKO_USERPROFILES_ADMINISTRATOR_ROLE")
                userprofile_roles = current_config.get(
                    "WEKO_USERPROFILES_ROLES")
                roles2 = [
                    role for role in current_user.roles
                    if role not in userprofile_roles or role == admin_role
                ]
                roles = roles1 + roles2
                if roles:
                    current_user.roles = roles
            db.session.add(current_userprofile)

            # Update email
            if current_app.config['USERPROFILES_EMAIL_ENABLED'] and \
                    form.email.data != current_user.email:
                current_user.email = form.email.data
                current_user.confirmed_at = None
                db.session.add(current_user)
                email_changed = True

        if email_changed:
            send_confirmation_instructions(current_user)
            # NOTE: Flash message after successful update of profile.
            flash(_('Profile was updated. We have sent a verification '
                    'email to %(email)s. Please check it.',
                    email=current_user.email),
                  category='success')
        else:
            # NOTE: Flash message after successful update of profile.
            flash(_('Profile was updated.'), category='success')


def get_role_by_position(position):
    """Get role by position.

    :param position:
    :return:
    """
    current_config = current_app.config
    role_setting = current_config.get('WEKO_USERPROFILES_ROLE_MAPPING')
    enable_mapping = current_config.get(
        'WEKO_USERPROFILES_ROLE_MAPPING_ENABLED')
    if isinstance(role_setting, dict) and enable_mapping:
        position_list = current_config.get("WEKO_USERPROFILES_POSITION_LIST")
        if not isinstance(position_list, list):
            return
        for item in position_list:
            if position == item[0]:
                if item in \
                    current_config.get(
                        "WEKO_USERPROFILES_POSITION_LIST_GENERAL"):
                    key = role_setting.get(
                        'WEKO_USERPROFILES_POSITION_LIST_GENERAL')
                    return current_config.get(key)
                elif item in \
                    current_config.get(
                        "WEKO_USERPROFILES_POSITION_LIST_GRADUATED_STUDENT"):
                    key = role_setting.get(
                        'WEKO_USERPROFILES_POSITION_LIST_GRADUATED_STUDENT')
                    return current_config.get(key)
                elif item in \
                    current_config.get(
                        "WEKO_USERPROFILES_POSITION_LIST_STUDENT"):
                    key = role_setting.get(
                        'WEKO_USERPROFILES_POSITION_LIST_STUDENT')
                    return current_config.get(key)
