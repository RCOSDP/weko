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
from flask_wtf import FlaskForm
from invenio_db import db

from .api import Indexes
from .models import IndexStyle
from .permissions import index_tree_permission
from .utils import get_admin_coverpage_setting
from weko_accounts.api import sync_shib_gakunin_map_groups

class IndexLinkSettingView(BaseView):
    """Index link setting view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
            form = FlaskForm(request.form)
            style = IndexStyle.get(
                current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
            if not style:
                IndexStyle.create(
                    current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                    width=3,
                    height=None)
                style = IndexStyle.get(
                    current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
            if request.method == 'POST' and form.validate():
                if request.form.get('indexlink') == 'enable':
                    style.index_link_enabled = True
                else:
                    style.index_link_enabled = False
                db.session.commit()
                flash(_('IndexLink flag was updated.'), category='success')
            return self.render(
                current_app.config['WEKO_INDEX_TREE_LINK_ADMIN_TEMPLATE'],
                enable=style.index_link_enabled,form=form)
        except BaseException:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
            return abort(400)


class IndexEditSettingView(BaseView):
    """Index link setting view."""

    @index_tree_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    @expose('/<int:index_id>', methods=['GET'])
    def index(self, index_id=0):
        """Render the index tree edit page."""
        sync_shib_gakunin_map_groups()
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
            current_app.instance_path,
            current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
            'indextree',
            fp.filename)
        file_uri = '/data/' + 'indextree/' + fp.filename
        fp.save(filename)
        return jsonify({'code': 0,
                        'msg': 'file upload success',
                        'data': {'path': file_uri}})


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
        'category': _('Index Tree'),
        'name': _('Edit Tree'),
        'endpoint': 'indexedit'
    }
}

__all__ = (
    'index_link_adminview',
    'IndexLinkSettingView',
    'index_edit_adminview',
    'IndexEditSettingView',
)
