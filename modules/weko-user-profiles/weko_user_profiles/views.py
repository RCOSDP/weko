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

"""VIews for weko-user-profiles."""

import json

from flask import Blueprint, current_app, flash, render_template, request
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from flask_security.confirmable import send_confirmation_instructions
from invenio_accounts.models import Role
from invenio_db import db

from .api import current_userprofile
from .forms import EmailProfileForm, ProfileForm, VerificationForm, \
    confirm_register_form_factory, register_form_factory
from .models import UserProfile

blueprint = Blueprint(
    'weko_user_profiles',
    __name__,
    template_folder='templates',
)

blueprint_api_init = Blueprint(
    'weko_user_profiles_api_init',
    __name__,
    template_folder='templates',
)

blueprint_ui_init = Blueprint(
    'weko_user_profiles_ui_init',
    __name__,
)


def init_common(app):
    """Post initialization."""
    if app.config['USERPROFILES_EXTEND_SECURITY_FORMS']:
        security_ext = app.extensions['security']
        security_ext.confirm_register_form = confirm_register_form_factory(
            security_ext.confirm_register_form)
        security_ext.register_form = register_form_factory(
            security_ext.register_form)


@blueprint_ui_init.record_once
def init_ui(state):
    """Post initialization for UI application."""
    app = state.app
    init_common(app)

    # Register blueprint for templates
    app.register_blueprint(
        blueprint, url_prefix=app.config['USERPROFILES_PROFILE_URL'])


@blueprint_api_init.record_once
def init_api(state):
    """Post initialization for API application."""
    init_common(state.app)


@blueprint.app_template_filter()
def userprofile(value):
    """Retrieve user profile for a given user id."""
    return UserProfile.get_by_userid(int(value))


@blueprint.route('/', methods=['GET', 'POST'])
@login_required
@register_menu(
    blueprint, 'settings.profile',
    # NOTE: Menu item text (icon replaced by a user icon).
    _('%(icon)s Profile', icon='<i class="fa fa-user fa-fw"></i>'),
    order=0)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.profile', _('Profile')
)
def profile():
    """View for editing a profile."""
    # Create forms
    verification_form = VerificationForm(formdata=None, prefix="verification")
    profile_form = profile_form_factory()

    # Process forms
    form = request.form.get('submit', None)
    if form == 'profile':
        handle_profile_form(profile_form)
    elif form == 'verification':
        handle_verification_form(verification_form)

    return render_template(
        current_app.config['USERPROFILES_PROFILE_TEMPLATE'],
        profile_form=profile_form,
        verification_form=verification_form,)


def profile_form_factory():
    """Create a profile form."""
    if current_app.config['USERPROFILES_EMAIL_ENABLED']:
        form = EmailProfileForm(
            formdata=None,
            username=current_userprofile.username,
            timezone=current_userprofile.timezone,
            language=current_userprofile.language,
            email=current_user.email,
            email_repeat=current_user.email,
            university=current_userprofile.university,
            department=current_userprofile.department,
            position=current_userprofile.position,
            otherPosition=current_userprofile.otherPosition,
            phoneNumber=current_userprofile.phoneNumber,
            instituteName=current_userprofile.instituteName,
            institutePosition=current_userprofile.institutePosition,
            instituteName2=current_userprofile.instituteName2,
            institutePosition2=current_userprofile.institutePosition2,
            instituteName3=current_userprofile.instituteName3,
            institutePosition3=current_userprofile.institutePosition3,
            instituteName4=current_userprofile.instituteName4,
            institutePosition4=current_userprofile.institutePosition4,
            instituteName5=current_userprofile.instituteName5,
            institutePosition5=current_userprofile.institutePosition5,
            prefix='profile', )
        return form
    else:
        form = ProfileForm(
            formdata=None,
            obj=current_userprofile,
            prefix='profile', )
        return form


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
        db.session.commit()

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
