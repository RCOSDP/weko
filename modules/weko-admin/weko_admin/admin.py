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
import hashlib
from flask import abort, current_app, flash, request, jsonify
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from .permissions import admin_permission_factory
from .utils import allowed_file

class StyleSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Block style setting page."""
        wysiwyg_editor_default = [
            '<div class="ql-editor ql-blank" data-gramm="false" '
            'contenteditable="true"><p><br></p></div>']

        body_bg = '#fff'
        panel_bg = '#fff'
        footer_default_bg = 'rgba(13,95,137,0.8)'
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

            from weko_theme.views import blueprint as theme_bp

            # Header
            f_path_header_wysiwyg = os.path.join(theme_bp.root_path,
                                                 theme_bp.template_folder,
                                                 current_app.config['THEME_HEADER_WYSIWYG_TEMPLATE'])
            header_array_wysiwyg = self.get_contents(f_path_header_wysiwyg)

            f_path_header_editor = os.path.join(theme_bp.root_path,
                                                theme_bp.template_folder,
                                                current_app.config['THEME_HEADER_EDITOR_TEMPLATE'])

            if self.cmp_files(f_path_header_wysiwyg, f_path_header_editor):
                header_array_wysiwyg = wysiwyg_editor_default

            # Footer
            f_path_footer_wysiwyg = os.path.join(theme_bp.root_path,
                                                 theme_bp.template_folder,
                                                 current_app.config['THEME_FOOTER_WYSIWYG_TEMPLATE'])
            footer_array_wysiwyg = self.get_contents(f_path_footer_wysiwyg)

            f_path_footer_editor = os.path.join(theme_bp.root_path,
                                                theme_bp.template_folder,
                                                current_app.config['THEME_FOOTER_EDITOR_TEMPLATE'])

            if self.cmp_files(f_path_footer_wysiwyg, f_path_footer_editor):
                footer_array_wysiwyg = wysiwyg_editor_default

            # Color
            if request.method == 'POST':
                if not admin_permission_factory('update-style-action').can():
                    current_app.logger.debug('deny access')
                    flash(_('deny access'))
                else:
                    form_lines = []
                    body_bg = request.form.get('body-bg', '#fff')
                    panel_bg = request.form.get('panel-bg', '#fff')
                    footer_default_bg = request.form.get(
                        'footer-default-bg', 'rgba(13,95,137,0.8)')
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
                    form_lines.append(
                        '$input-bg-transparent: rgba(255, 255, 255, 0);')

                    with open(scss_file, 'w', encoding='utf-8') as fp:
                        fp.writelines('\n'.join(form_lines))
        except BaseException:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return self.render(
            current_app.config["WEKO_ADMIN_BlOCK_STYLE_TEMPLATE"],
            body_bg=body_bg,
            panel_bg=panel_bg,
            footer_default_bg=footer_default_bg,
            navbar_default_bg=navbar_default_bg,
            panel_default_border=panel_default_border,
            header_innerHtml=''.join(header_array_wysiwyg),
            footer_innerHtml=''.join(footer_array_wysiwyg)
        )

    @expose('/upload_editor', methods=['POST'])
    def upload_editor(self):
        """Upload header/footer settings from wysiwyg editor."""

        try:
            from html import unescape
            from weko_theme.views import blueprint as theme_bp
            write_path = folder_path = os.path.join(
                theme_bp.root_path, theme_bp.template_folder)
            data = request.get_json()
            temp = data.get('temp')
            wysiwyg_html = unescape(data.get('content'))

            if 'footer' == temp:
                if 'True' == str(data.get('isEmpty')):
                    read_path = os.path.join(folder_path,
                                             current_app.config[
                                                 'THEME_FOOTER_EDITOR_TEMPLATE'])
                    wysiwyg_html = self.get_contents(read_path)

                write_path = os.path.join(folder_path,
                                          current_app.config[
                                              'THEME_FOOTER_WYSIWYG_TEMPLATE'])
            elif 'header' == temp:
                if 'True' == str(data.get('isEmpty')):
                    read_path = os.path.join(folder_path,
                                             current_app.config[
                                                 'THEME_HEADER_EDITOR_TEMPLATE'])
                    wysiwyg_html = self.get_contents(read_path)

                write_path = os.path.join(folder_path,
                                          current_app.config[
                                              'THEME_HEADER_WYSIWYG_TEMPLATE'])
            else:
                abort(400)

            with open(write_path, 'w+', encoding='utf-8') as fp:
                fp.writelines(wysiwyg_html)
        except Exception:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            abort(500)
        return jsonify({'code': 0, 'msg': 'success'})

    def get_contents(self, f_path):
        """Get the contents of the file."""

        array = []
        try:
            with open(f_path, 'r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    array.append(line)
        except Exception:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            abort(500)
        return array

    def cmp_files(self, f_path1, f_path2):
        """Compare the contents of the file."""

        checksum1 = ''
        checksum2 = ''
        try:
            with open(f_path1, 'rb') as fp1:
                checksum1 = hashlib.md5(fp1.read()).hexdigest()
            with open(f_path2, 'rb') as fp2:
                checksum2 = hashlib.md5(fp2.read()).hexdigest()
        except Exception:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
            abort(500)
        return checksum1 == checksum2

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
)
