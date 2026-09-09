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
        enable_custom = current_app.config.get('WEKO_USERPROFILES_CUSTOMIZE_ENABLED', False)
        result['subitem_fullname'] = user_info.fullname \
            if not enable_custom or profile_setting.get('fullname', {}).get('visible', True) else ''
        result['subitem_displayname'] = user_info._displayname \
            if not enable_custom or profile_setting.get('displayname', {}).get('visible', True) else ''
        result['subitem_user_name'] = user_info.get_username \
            if not enable_custom or profile_setting.get('username', {}).get('visible', True) else ''
        result['subitem_university/institution'] = user_info.university \
            if not enable_custom or profile_setting.get('university', {}).get('visible', True) else ''
        result['subitem_affiliated_division/department'] = user_info.department \
            if not enable_custom or profile_setting.get('department', {}).get('visible', True) else ''
        # weko#XXXXX: WEKO_USERPROFILES_POSITION_LIST* stores the value in
        # English; only the display label is localized via gettext, and
        # that translation depends on the *current request's* resolved
        # locale (session / I18N_USER_LANG_ATTR / Accept-Language), which
        # is not reliably Japanese even for users whose own profile
        # language is "ja" (I18N_USER_LANG_ATTR here is bound to a
        # "prefered_language" attribute, not userprofile.language).
        # Item types with a Japanese-only enum for subitem_position
        # (e.g. JGSS-style USER_INFORMATION property) reject the raw
        # English value -- or an untranslated one -- on required-field
        # validation / silently fail to pre-select in the form widget.
        # Use a fixed, locale-independent mapping to the same Japanese
        # labels already shipped in this module's own .po catalog
        # (weko_user_profiles/translations/ja/LC_MESSAGES/messages.po),
        # so the auto-filled value always matches the item type's enum
        # regardless of the request's resolved locale.
        _POSITION_EN_TO_JA = {
            'Professor': '教授',
            'Assistant Professor': '准教授',
            'Full-time Instructor': '専任講師',
            'Assistant Teacher': '助教',
            'Full-time Researcher': '常勤研究員',
            'Others (Input Detail)': 'その他（具体的に入力）',
            'JSPS Research Fellowship for Young Scientists (PD, SPD etc.)':
                '日本学術振興会特別研究員(PD, SPD等)',
            'JSPS Research Fellowship for Young Scientists (DC1, DC2)':
                '日本学術振興会特別研究員(DC1, DC2)',
            'Doctoral Course (Doctoral Program)': '博士課程(博士後期課程)',
            'Master Course (Master Program)': '修士課程(博士前期課程)',
            'Fellow Researcher': '研究生',
            'Listener': '聴講生',
            'Student': '学部生',
        }
        if not enable_custom or profile_setting.get('position', {}).get('visible', True):
            result['subitem_position'] = \
                _POSITION_EN_TO_JA.get(user_info.position, user_info.position) \
                if user_info.position else ''
        else:
            result['subitem_position'] = ''
        result['subitem_position(others)'] = user_info.item1 \
            if not enable_custom or profile_setting.get('item1', {}).get('visible', True) else ''
        result['subitem_phone_number'] = user_info.item2 \
            if not enable_custom or profile_setting.get('item2', {}).get('visible', True) else ''
        subitem_affiliated_institution = []
        institute_dict_data = user_info.get_institute_data(enable_custom)
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
