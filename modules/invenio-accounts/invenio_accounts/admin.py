# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for invenio-accounts."""

import os

from flask import current_app, flash
from flask_admin.actions import action
from flask_admin.babel import lazy_gettext
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from flask_admin.contrib.sqla.fields import QuerySelectMultipleField
from flask_admin.form import Select2Widget
from flask_admin.form.fields import DateTimeField
from flask_admin.model.fields import AjaxSelectMultipleField
from flask_babelex import gettext as _
from flask_security import current_user
from flask_security.recoverable import send_reset_password_instructions
from flask_security.utils import hash_password
from invenio_communities.models import Community
from invenio_db import db
from passlib import pwd
from sqlalchemy import func
from werkzeug.local import LocalProxy
from collections import OrderedDict
from wtforms.fields import BooleanField, SelectMultipleField
from wtforms.validators import DataRequired

from weko_workflow.models import WorkFlow, WorkflowRole

from .cli import commit
from .models import Role, SessionActivity, User
from .sessions import delete_session

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class UserView(ModelView):
    """Flask-Admin view to manage users."""

    can_view_details = True

    list_all = (
        'id', 'email', 'active', 'confirmed_at', 'last_login_at',
        'current_login_at', 'last_login_ip', 'current_login_ip', 'login_count'
    )

    column_list = \
        column_searchable_list = \
        column_sortable_list = \
        column_details_list = \
        list_all

    form_columns = ('email', 'password', 'active', 'notification')

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

    def scaffold_form(self):
        form_class = super(UserView, self).scaffold_form()
        form_class.role = QuerySelectMultipleField(
            'Roles',
            query_factory=lambda: Role.query.filter(~Role.name.like('%_groups_%')).all(),
            get_label='name',
            widget=Select2Widget(multiple=True)
        )
        form_class.group = QuerySelectMultipleField(
            'Groups',
            query_factory=lambda: Role.query.filter(Role.name.like('%_groups_%')).all(),
            get_label='name',
            widget=Select2Widget(multiple=True)
        )
        
        return form_class
    
    def _order_fields(self, form):
        custom_order = ['email', 'password', 'active', 'role', 'group', 'notification']
        ordered_fields = OrderedDict()
        for field_name in custom_order:
            ordered_fields[field_name] = form._fields[field_name]
        form._fields = ordered_fields
        return form
    
    def create_form(self, obj=None):
        form = super(UserView, self).create_form(obj)
        return self._order_fields(form)
    
    def edit_form(self, obj=None):
        form = super(UserView, self).edit_form(obj)
        return self._order_fields(form)

    def on_form_prefill(self, form, id):
        obj = self.get_one(id)
        form.role.data = [role for role in obj.roles if '_groups_' not in role.name]
        form.group.data = [role for role in obj.roles if '_groups_' in role.name]
    
    def on_model_change(self, form, User, is_created):
        """Hash password when saving."""
        if form.password.data is not None:
            pwd_ctx = current_app.extensions['security'].pwd_context
            if pwd_ctx.identify(form.password.data) is None:
                User.password = hash_password(form.password.data)

        roles = form.role.data + form.group.data
        User.roles = roles

    def after_model_change(self, form, User, is_created):
        """Send password instructions if desired."""
        if is_created and form.notification.data is True:
            send_reset_password_instructions(User)

    def get_query(self):
        """Return a query for the model type."""
        if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
            return self.session.query(self.model)
        else:
            repositories = Community.get_repositories_by_user(current_user)
            groups = [repository.group for repository in repositories]
            return self.session.query(self.model).filter(self.model.roles.any(Role.id.in_([group.id for group in groups])))

    def get_count_query(self):
        """Return a the count query for the model type"""
        if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
            return self.session.query(func.count('*')).select_from(self.model)
        else:
            repositories = Community.get_repositories_by_user(current_user)
            groups = [repository.group for repository in repositories]
            return self.session.query(func.count('*')).select_from(self.model).filter(self.model.roles.any(Role.id.in_([group.id for group in groups])))

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

    _system_role = os.environ.get('INVENIO_ROLE_SYSTEM',
                                  'System Administrator')
    _repo_role = os.environ.get('INVENIO_ROLE_REPOSITORY',
                                'Repository Administrator')
    _com_role = os.environ.get('INVENIO_ROLE_COMMUNITY',
                               'Community Administrator')
    _admin_roles = [_system_role, _repo_role, _com_role]
    
    @property
    def can_create(self):
        """Check permission for creating."""
        return self._system_role in [role.name for role in current_user.roles]

    @property
    def can_edit(self):
        """Check permission for Editing."""
        return any(role.name in self._admin_roles for role in current_user.roles)

    @property
    def can_delete(self):
        """Check permission for Deleting."""
        return any(role.name in self._admin_roles for role in current_user.roles)


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

    def after_model_change(self, form, model, is_created):
        if is_created and current_app.config.get('ACCOUNTS_WORKFLOW_ROLE_HIDE_FILTER', False):
            try:
                workflows = WorkFlow.query.filter_by(
                    is_deleted=False).all()
                if workflows:
                    id_list = [x.id for x in workflows]
                    with db.session.begin_nested():
                        for i in id_list:
                            wfrole = dict(
                                workflow_id=i,
                                role_id=model.id
                            )
                            db.session.execute(WorkflowRole.__table__.insert(), wfrole)
                    db.session.commit()
            except Exception as ex:
                current_app.logger.error(
                    'Insert workflow_id_list: {}, role_id: {} into workflow_userrole fail.'
                    .format(id_list, model.id)
                )
                current_app.logger.error(str(ex))
                db.session.rollback()


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
        try:
            if SessionActivity.is_current(sid_s=model.sid_s):
                flash('You could not remove your current session', 'error')
                return
            delete_session(sid_s=model.sid_s)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)

    @action('delete', lazy_gettext('Delete selected sessions'),
            lazy_gettext('Are you sure you want to delete selected sessions?'))
    def action_delete(self, ids):
        """Delete selected sessions."""
        try:
            is_current = any(SessionActivity.is_current(sid_s=id_) for id_ in ids)
            if is_current:
                flash('You could not remove your current session', 'error')
                return
            for id_ in ids:
                delete_session(sid_s=id_)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)


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
