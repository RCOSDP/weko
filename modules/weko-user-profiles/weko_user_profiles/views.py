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

"""Views for weko-user-profiles."""

import traceback
import requests

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import current_user, login_required
from flask_menu import register_menu
from invenio_db import db

from .api import current_userprofile
from .forms import EmailProfileForm, ProfileForm, VerificationForm, \
    confirm_register_form_factory, custom_profile_form_factory, register_form_factory
from .models import UserProfile
from .utils import get_user_profile_info, handle_profile_form, \
    handle_verification_form

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


@blueprint_api_init.route('/get_profile_info/', methods=['GET'])
def get_profile_info():
    """Get user profile.

    @return:
    """
    result = {
        'positions': '',
        'results': '',
        'error': '',
    }

    try:
        user_id = current_user.id
        if user_id is not None:
            result['results'] = get_user_profile_info(user_id)
            result['positions'] = current_app.config[
                'WEKO_USERPROFILES_POSITION_LIST']
    except Exception as e:
        result['error'] = str(e)
    return jsonify(result)


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
    try:
        if form == 'profile':
            handle_profile_form(profile_form)
            db.session.commit()
        elif form == 'verification':
            handle_verification_form(verification_form)
    except Exception as e:
        traceback.print_exc()
        db.session.rollback()
        current_app.logger.error(e)

    if current_app.config["WEKO_NOTIFICATIONS"]:
        try:
            from weko_notifications.utils import create_userprofile, inbox_url
            create_userprofile(current_userprofile)
            requests.post(
                inbox_url(endpoint="/userprofile"),
                json=create_userprofile(current_userprofile)
            )
        except Exception as ex:
            current_app.logger.error(
                f"Error sending user profile to inbox. user_id={current_user.id}"
            )
            traceback.print_exc()

    return render_template(
        current_app.config['USERPROFILES_PROFILE_TEMPLATE'],
        profile_form=profile_form,
        verification_form=verification_form,)


def profile_form_factory():
    """Create a profile form."""
    if current_app.config['USERPROFILES_EMAIL_ENABLED']:
        if current_app.config.get("WEKO_USERPROFILES_CUSTOMIZE_ENABLED", False):
            form_cls = custom_profile_form_factory(EmailProfileForm)
        else:
            form_cls = EmailProfileForm
        form = form_cls(
            formdata=None,
            username=current_userprofile.username,
            fullname=current_userprofile.fullname,
            timezone=current_userprofile.timezone,
            language=current_userprofile.language,
            email=current_user.email,
            email_repeat=current_user.email,
            access_key=current_userprofile.access_key,
            secret_key=current_userprofile.secret_key,
            s3_endpoint_url=current_userprofile.s3_endpoint_url,
            s3_region_name=current_userprofile.s3_region_name,
            university=current_userprofile.university,
            department=current_userprofile.department,
            position=current_userprofile.position,
            item1=current_userprofile.item1,
            item2=current_userprofile.item2,
            item3=current_userprofile.item3,
            item4=current_userprofile.item4,
            item5=current_userprofile.item5,
            item6=current_userprofile.item6,
            item7=current_userprofile.item7,
            item8=current_userprofile.item8,
            item9=current_userprofile.item9,
            item10=current_userprofile.item10,
            item11=current_userprofile.item11,
            item12=current_userprofile.item12,
            item13=current_userprofile.item13,
            item14=current_userprofile.item14,
            item15=current_userprofile.item15,
            item16=current_userprofile.item16,
            prefix='profile', )
        return form
    else:
        if current_app.config.get("WEKO_USERPROFILES_CUSTOMIZE_ENABLED", False):
            form_cls = custom_profile_form_factory(ProfileForm)
        else:
            form_cls = ProfileForm
        form = form_cls(
            formdata=None,
            obj=current_userprofile,
            prefix='profile', )
    return form

@blueprint.teardown_request
@blueprint_ui_init.teardown_request
@blueprint_api_init.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_user_profiles dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
