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

import sys

from flask import abort, current_app, flash, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from .models import IndexStyle
from invenio_db import db

class IndexSettingView(BaseView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        try:
            # Get record
            style = IndexStyle.get(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
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
                        IndexStyle.update(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                                          width=width, height=height)
                    else:
                        IndexStyle.create(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                                          width=width, height=height)

                    flash(_('The information was updated.'), category='success')

            return self.render(current_app.config['WEKO_INDEX_TREE_ADMIN_TEMPLATE'],
                               widths=current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['widths'],
                               width_selected=width, height=height)

        except:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return abort(400)


class IndexLinkSettingView(BaseView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        try:
            style = IndexStyle.get(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
            if not style:
                IndexStyle.create(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
                    width=3, height=None)
                style = IndexStyle.get(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
            if request.method == 'POST':
                if request.form.get('indexlink') == 'enable':
                    style.index_link_enabled = True
                else:
                    style.index_link_enabled = False
                db.session.commit()
            return self.render(current_app.config['WEKO_INDEX_TREE_LINK_ADMIN_TEMPLATE'],
                    enable=style.index_link_enabled)
        except:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            return abort(400)


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

__all__ = (
    'index_adminview',
    'IndexSettingView',
    'index_link_adminview',
    'IndexLinkSettingView',
)
