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


from weko_user_profiles.forms import _update_with_csrf_disabled, \
    confirm_register_form_factory, register_form_factory


def test_register_form_factory_no_csrf(app):
    """Test CSRF token is not in reg. form and not in profile inner form."""
    security = app.extensions['security']
    rf = _get_form(app, security.register_form, register_form_factory)

    _assert_no_csrf_token(rf)


def test_register_form_factory_csrf(app_with_csrf):
    """Test CSRF token is in reg. form but not in profile inner form."""
    security = app_with_csrf.extensions['security']
    rf = _get_form(app_with_csrf, security.register_form,
                   register_form_factory)

    _assert_csrf_token(rf)


def test_force_disable_csrf_register_form(app_with_csrf):
    """Test force disable CSRF for reg. form"""
    security = app_with_csrf.extensions['security']
    rf = _get_form(app_with_csrf, security.register_form,
                   register_form_factory, force_disable_csrf=True)
    _assert_no_csrf_token(rf)


def test_confirm_register_form_factory_no_csrf(app):
    """Test CSRF token is not in confirm form and not in profil
e inner form."""
    security = app.extensions['security']
    rf = _get_form(app, security.confirm_register_form,
                   confirm_register_form_factory)

    _assert_no_csrf_token(rf)


def test_confirm_register_form_factory_csrf(app_with_csrf):
    """Test CSRF token is in confirm form but not in profile inner form."""
    security = app_with_csrf.extensions['security']
    rf = _get_form(app_with_csrf, security.confirm_register_form,
                   confirm_register_form_factory)

    _assert_csrf_token(rf)


def test_force_disable_csrf_confirm_form(app_with_csrf):
    """Test force disable CSRF for confirm. form"""
    security = app_with_csrf.extensions['security']
    rf = _get_form(app_with_csrf, security.confirm_register_form,
                   confirm_register_form_factory, force_disable_csrf=True)

    _assert_no_csrf_token(rf)


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
