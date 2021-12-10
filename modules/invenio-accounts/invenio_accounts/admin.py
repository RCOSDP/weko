# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for invenio-accounts."""

from flask import current_app, flash
from flask_admin.actions import action
from flask_admin.babel import lazy_gettext
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.form.fields import DateTimeField
from flask_admin.model.fields import AjaxSelectMultipleField
from flask_babelex import gettext as _
from flask_security.recoverable import send_reset_password_instructions
from flask_security.utils import hash_password
from invenio_db import db
from passlib import pwd
from werkzeug.local import LocalProxy
from wtforms.fields import BooleanField
from wtforms.validators import DataRequired

from .cli import commit
from .models import Role, SessionActivity, User
from .sessions import delete_session

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class UserView(ModelView):
    """Flask-Admin view to manage users."""

    can_view_details = True
    can_delete = False

    list_all = (
        'id', 'email', 'active', 'confirmed_at', 'last_login_at',
        'current_login_at', 'last_login_ip', 'current_login_ip', 'login_count'
    )

    column_list = \
        column_searchable_list = \
        column_sortable_list = \
        column_details_list = \
        list_all

    form_columns = ('email', 'password', 'active', 'roles', 'notification')

    form_args = dict(
        email=dict(label='Email', validators=[DataRequired()]),
        password=dict(default=lambda: pwd.genword(length=12))
    )

    form_extra_fields = {
        'notification': BooleanField(
            'Send User Notification',
            description='Send the new user an email about their account.')
    }

    column_filters = ('id', 'email', 'active', 'confirmed_at', 'last_login_at',
                      'current_login_at', 'login_count')

    column_default_sort = ('last_login_at', True)

    form_overrides = {
        'last_login_at': DateTimeField
    }

    column_labels = {
        'current_login_ip': _('Current Login IP'),
        'last_login_ip': _('Last Login IP')
    }

    def on_model_change(self, form, User, is_created):
        """Hash password when saving."""
        if form.password.data is not None:
            pwd_ctx = current_app.extensions['security'].pwd_context
            if pwd_ctx.identify(form.password.data) is None:
                User.password = hash_password(form.password.data)

    def after_model_change(self, form, User, is_created):
        """Send password instructions if desired."""
        if is_created and form.notification.data is True:
            send_reset_password_instructions(User)

    @action('inactivate', _('Inactivate'),
            _('Are you sure you want to inactivate selected users?'))
    @commit
    def action_inactivate(self, ids):
        """Inactivate users."""
        try:
            count = 0
            for user_id in ids:
                user = _datastore.get_user(user_id)
                if user is None:
                    raise ValueError(_("Cannot find user."))
                if _datastore.deactivate_user(user):
                    count += 1
            if count > 0:
                flash(_('User(s) were successfully inactivated.'), 'success')
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise

            current_app.logger.exception(str(exc))  # pragma: no cover
            flash(_('Failed to inactivate users.'),
                  'error')  # pragma: no cover

    @action('activate', _('Activate'),
            _('Are you sure you want to activate selected users?'))
    @commit
    def action_activate(self, ids):
        """Inactivate users."""
        try:
            count = 0
            for user_id in ids:
                user = _datastore.get_user(user_id)
                if user is None:
                    raise ValueError(_("Cannot find user."))
                if _datastore.activate_user(user):
                    count += 1
            if count > 0:
                flash(_('User(s) were successfully inactivated.'), 'success')
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise

            current_app.logger.exception(str(exc))  # pragma: no cover
            flash(_('Failed to activate users.'), 'error')  # pragma: no cover


class RoleView(ModelView):
    """Admin view for roles."""

    can_view_details = True

    list_all = ('id', 'name', 'description')

    column_list = \
        column_searchable_list = \
        column_filters = \
        column_details_list = \
        columns_sortable_list = \
        list_all

    form_columns = ('name', 'description', 'users')

    user_loader = QueryAjaxModelLoader(
        'user',
        LocalProxy(lambda: _datastore.db.session),
        User,
        fields=['email'],
        page_size=10
    )

    form_extra_fields = {
        'users': AjaxSelectMultipleField(user_loader)
    }

    form_ajax_refs = {
        'user': user_loader
    }


class SessionActivityView(ModelView):
    """Admin view for user sessions."""

    can_view_details = False
    can_create = False
    can_edit = False

    list_all = ('user.id', 'user.email', 'sid_s', 'created')

    column_labels = {
        'user.id': 'User ID',
        'user.email': 'Email',
        'sid_s': 'Session ID',
    }
    column_list = list_all
    column_filters = list_all
    column_sortable_list = list_all

    form_ajax_refs = {
        'user': {
            'fields': (User.id, User.email)
        },
    }

    def delete_model(self, model):
        """Delete a specific session."""
        if SessionActivity.is_current(sid_s=model.sid_s):
            flash('You could not remove your current session', 'error')
            return
        delete_session(sid_s=model.sid_s)
        db.session.commit()

    @action('delete', lazy_gettext('Delete selected sessions'),
            lazy_gettext('Are you sure you want to delete selected sessions?'))
    def action_delete(self, ids):
        """Delete selected sessions."""
        is_current = any(SessionActivity.is_current(sid_s=id_) for id_ in ids)
        if is_current:
            flash('You could not remove your current session', 'error')
            return
        for id_ in ids:
            delete_session(sid_s=id_)
        db.session.commit()


session_adminview = {
    'model': SessionActivity,
    'modelview': SessionActivityView,
    'category': _('User Management')
}

user_adminview = {
    'model': User,
    'modelview': UserView,
    'category': _('User Management')
}

role_adminview = {
    'model': Role,
    'modelview': RoleView,
    'category': _('User Management')
}

__all__ = (
    'role_adminview',
    'RoleView',
    'session_adminview',
    'SessionActivityView',
    'user_adminview',
    'UserView',
)
