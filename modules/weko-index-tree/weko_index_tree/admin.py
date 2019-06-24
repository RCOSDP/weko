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

"""WEKO3 module docstring."""

import os
import sys

from flask import abort, current_app, flash, jsonify, request, session, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_db import db

from .api import Indexes
from .models import IndexStyle
from .permissions import index_tree_permission
from .utils import get_admin_coverpage_setting


class IndexSettingView(BaseView):
    """Index setting view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
            # Get record
            style = IndexStyle.get(
                current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
            width = style.width if style else '3'
            height = style.height if style else None

            # Post
            if request.method == 'POST':
                # Get form
                form = request.form.get('submit', None)
                if form == 'index_form':
                    width = request.form.get('width', '3')
                    height = request.form.get('height', None)

                    if style:
                        IndexStyle.update(
                            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                            width=width,
                            height=height)
                    else:
                        IndexStyle.create(
                            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                            width=width,
                            height=height)

                    flash(
                        _('The information was updated.'),
                        category='success')

            return self.render(
                current_app.config['WEKO_INDEX_TREE_ADMIN_TEMPLATE'],
                widths=current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['widths'],
                width_selected=width,
                height=height)

        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return abort(400)


class IndexLinkSettingView(BaseView):
    """Index link setting view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
            style = IndexStyle.get(
                current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
            if not style:
                IndexStyle.create(
                    current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                    width=3,
                    height=None)
                style = IndexStyle.get(
                    current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
            if request.method == 'POST':
                if request.form.get('indexlink') == 'enable':
                    style.index_link_enabled = True
                else:
                    style.index_link_enabled = False
                db.session.commit()
            return self.render(
                current_app.config['WEKO_INDEX_TREE_LINK_ADMIN_TEMPLATE'],
                enable=style.index_link_enabled)
        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            return abort(400)


class IndexEditSettingView(BaseView):
    """Index link setting view."""

    @index_tree_permission.require(http_exception=403) # Not needed anymore?
    @expose('/', methods=['GET'])
    @expose('/<int:index_id>', methods=['GET'])
    def index(self, index_id=0):
        """Render the index tree edit page."""
        return self.render(
            current_app.config['WEKO_INDEX_TREE_INDEX_ADMIN_TEMPLATE'],
            get_tree_json=current_app.config['WEKO_INDEX_TREE_LIST_API'],
            upt_tree_json='',
            mod_tree_detail=current_app.config['WEKO_INDEX_TREE_API'],
            admin_coverpage_setting=str(get_admin_coverpage_setting()),
            index_id=index_id,
            lang_code=session.get('selected_language', 'en')  # Set default
        )

    @expose('/upload', methods=['POST'])
    def upload_image(self):
        """Upload images."""
        if 'uploadFile' not in request.files:
            current_app.logger.debug('No file part')
            flash(_('No file part'))
            return abort(400)
        fp = request.files['uploadFile']
        if '' == fp.filename:
            current_app.logger.debug('No selected file')
            flash(_('No selected file'))
            return abort(400)

        filename = os.path.join(
            current_app.static_folder, 'indextree', fp.filename)
        file_uri = url_for('static', filename='indextree/' + fp.filename)
        fp.save(filename)
        return jsonify({'code': 0,
                        'msg': 'file upload success',
                        'data': {'path': file_uri}})


index_adminview = {
    'view_class': IndexSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Index Tree'),
        'endpoint': 'indextree'
    }
}

index_link_adminview = {
    'view_class': IndexLinkSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Index Link'),
        'endpoint': 'indexlink'
    }
}

index_edit_adminview = {
    'view_class': IndexEditSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Edit Tree'),
        'endpoint': 'indexedit'
    }
}

__all__ = (
    'index_adminview',
    'IndexSettingView',
    'index_link_adminview',
    'IndexLinkSettingView',
    'index_edit_adminview',
    'IndexEditSettingView',
)
