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

"""Weko Authors admin."""

from __future__ import absolute_import, print_function

from flask import current_app, json, jsonify, request, session
from flask_admin import BaseView, expose
from flask_babelex import gettext as _

from .models import Authors
from .permissions import author_permission


class AuthorManagementView(BaseView):
    """Weko authors admin view."""

    @author_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    def index(self):
        """Render author list view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_LIST_TEMPLATE'],
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get('selected_language', 'en')  # Set default lang
        )

    @author_permission.require(http_exception=403)
    @expose('/add', methods=['GET'])
    def add(self):
        """Render author edit view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE'],
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get('selected_language', 'en')  # Set default lang
        )

    @author_permission.require(http_exception=403)
    @expose('/edit', methods=['GET'])
    def edit(self):
        """Render an adding author view."""
        return self.render(
            current_app.config['WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE'],
            render_widgets=False,  # Moved to admin, no need for widgets
            lang_code=session.get('selected_language', 'en')  # Set default
        )


authors_list_adminview = {
    'view_class': AuthorManagementView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Author Management'),
        'endpoint': 'authors'
    }
}

__all__ = (
    'authors_list_adminview',
)
