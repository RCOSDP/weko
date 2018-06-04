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

from flask import abort, current_app, flash, redirect, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _

from .permissions import admin_permission_factory
from .utils import allowed_file


class StyleSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Block style setting page."""
        body_bg = '#fff'
        panel_bg = '#fff'
        footer_default_bg = '#8a8a8a'
        navbar_default_bg = '#f8f8f8'
        panel_default_border = '#ddd'
        scss_file = os.path.join(current_app.static_folder,
                                 'css/weko_theme/_variables.scss')
        try:
            with open(scss_file, 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    line = line.strip()
                    if '$body-bg:' in line:
                        body_bg = line[line.find('#'):-1]
                    if '$panel-bg:' in line:
                        panel_bg = line[line.find('#'):-1]
                    if '$footer-default-bg:' in line:
                        footer_default_bg = line[line.find('#'):-1]
                    if '$navbar-default-bg:' in line:
                        navbar_default_bg = line[line.find('#'):-1]
                    if '$panel-default-border:' in line:
                        panel_default_border = line[line.find('#'):-1]
            footer_array = []
            header_array = []
            from weko_theme.views import blueprint as theme_bp
            f_path = os.path.join(theme_bp.root_path, theme_bp.template_folder,
                                  current_app.config['THEME_FOOTER_TEMPLATE'])
            with open(f_path, 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    footer_array.append(line)
            f_path = os.path.join(theme_bp.root_path, theme_bp.template_folder,
                                  current_app.config['THEME_HEADER_TEMPLATE'])
            with open(f_path, 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    header_array.append(line)
            if request.method == 'POST':
                if not admin_permission_factory('update-style-action').can():
                    current_app.logger.debug('deny access')
                    flash(_('deny access'))
                else:
                    form_lines = []
                    body_bg = request.form.get('body-bg', '#fff')
                    panel_bg = request.form.get('panel-bg', '#fff')
                    footer_default_bg = request.form.get(
                        'footer-default-bg', '#8a8a8a')
                    navbar_default_bg = request.form.get(
                        'navbar-default-bg', '#f8f8f8')
                    panel_default_border = request.form.get(
                        'panel-default-border', '#ddd')
                    form_lines.append(
                        '$body-bg: ' + body_bg + ';')
                    form_lines.append(
                        '$panel-bg: ' + panel_bg + ';')
                    form_lines.append(
                        '$footer-default-bg: ' + footer_default_bg + ';')
                    form_lines.append(
                        '$navbar-default-bg: ' + navbar_default_bg + ';')
                    form_lines.append(
                        '$panel-default-border: ' + panel_default_border + ';')
                    with open(scss_file, 'w', encoding='utf-8') as fp:
                        fp.writelines('\n'.join(form_lines))
        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return self.render(
            'weko_admin/admin/block_style.html',
            body_bg=body_bg,
            panel_bg=panel_bg,
            footer_default_bg=footer_default_bg,
            navbar_default_bg=navbar_default_bg,
            panel_default_border=panel_default_border,
            header_innerHtml=''.join(header_array),
            footer_innerHtml=''.join(footer_array)
        )

    @expose('/upload_logo', methods=['POST'])
    def upload_logo(self):
        if not admin_permission_factory('update-style-action').can():
            return abort(403)
        if 'logo_file' not in request.files:
            current_app.logger.debug('No file part')
            flash(_('No file part'))
            return abort(400)
        fp = request.files['logo_file']
        if '' == fp.filename:
            current_app.logger.debug('No selected file')
            flash(_('No selected file'))
            return abort(400)
        if fp and allowed_file(fp.filename):
            filename = os.path.join(
                current_app.static_folder, current_app.config['THEME_LOGO'])
            fp.save(filename)
        return redirect(url_for('stylesetting.index'))

    def is_visible(self):
        return True if admin_permission_factory(
            'update-style-action').can() else admin_permission_factory(
            action='read-style-action').can()

    def is_accessible(self):
        return self.is_visible()


style_adminview = {
    'view_class': StyleSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Style'),
        'endpoint': 'stylesetting'
    }
}

__all__ = (
    'style_adminview',
    'StyleSettingView',
)
