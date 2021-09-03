# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

from __future__ import absolute_import, print_function

from flask import abort, current_app, flash, redirect, render_template, \
    request, url_for
from flask_babelex import lazy_gettext as _
from flask_breadcrumbs import register_breadcrumb
from flask_login import login_required
from flask_menu import register_menu
from flask_security import current_user
from invenio_db import db

from ..forms import RevokeForm
from ..models import SessionActivity
from ..sessions import delete_session
from .settings import blueprint


@login_required
@register_menu(
    blueprint, 'settings.security',
    # NOTE: Menu item text (icon replaced by a user icon).
    _('%(icon)s Security', icon='<i class="fa fa-shield fa-fw"></i>'),
    order=2)
@register_breadcrumb(blueprint, 'breadcrumbs.settings.security', _('Security'))
def security():
    """View for security page."""
    sessions = SessionActivity.query_by_user(
        user_id=current_user.get_id()
    ).all()
    master_session = None
    for index, session in enumerate(sessions):
        if SessionActivity.is_current(session.sid_s):
            master_session = session
            del sessions[index]
    return render_template(
        current_app.config['ACCOUNTS_SETTINGS_SECURITY_TEMPLATE'],
        formclass=RevokeForm,
        sessions=[master_session] + sessions,
        is_current=SessionActivity.is_current
    )


@login_required
def revoke_session():
    """Revoke a session."""
    form = RevokeForm(request.form)
    if not form.validate_on_submit():
        abort(403)

    sid_s = form.data['sid_s']
    if SessionActivity.query.filter_by(
            user_id=current_user.get_id(), sid_s=sid_s).count() == 1:
        delete_session(sid_s=sid_s)
        db.session.commit()
        if not SessionActivity.is_current(sid_s=sid_s):
            # if it's the same session doesn't show the message, otherwise
            # the session will be still open without the database record
            flash('Session {0} successfully removed.'.format(sid_s), 'success')
    else:
        flash('Unable to remove the session {0}.'.format(sid_s), 'error')
    return redirect(url_for('invenio_accounts.security'))
