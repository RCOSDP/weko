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

import hashlib
import os
import sys
import unicodedata
from datetime import datetime

from flask import abort, current_app, flash, jsonify, request
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import rules
from flask_babelex import gettext as _
from flask_login import current_user
from wtforms.fields import StringField
from wtforms.validators import ValidationError
from .permissions import admin_permission_factory
from .utils import allowed_file
from .models import ChunkItem
from . import config


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
            f_path_header_wysiwyg = os.path.join(
                theme_bp.root_path,
                theme_bp.template_folder,
                current_app.config['THEME_HEADER_WYSIWYG_TEMPLATE'])
            header_array_wysiwyg = self.get_contents(f_path_header_wysiwyg)

            f_path_header_editor = os.path.join(
                theme_bp.root_path,
                theme_bp.template_folder,
                current_app.config['THEME_HEADER_EDITOR_TEMPLATE'])

            if self.cmp_files(f_path_header_wysiwyg, f_path_header_editor):
                header_array_wysiwyg = wysiwyg_editor_default

            # Footer
            f_path_footer_wysiwyg = os.path.join(
                theme_bp.root_path,
                theme_bp.template_folder,
                current_app.config['THEME_FOOTER_WYSIWYG_TEMPLATE'])
            footer_array_wysiwyg = self.get_contents(f_path_footer_wysiwyg)

            f_path_footer_editor = os.path.join(
                theme_bp.root_path,
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
                    read_path = os.path.join(
                        folder_path, current_app.config['THEME_FOOTER_EDITOR_TEMPLATE'])
                    wysiwyg_html = self.get_contents(read_path)

                write_path = os.path.join(folder_path,
                                          current_app.config[
                                              'THEME_FOOTER_WYSIWYG_TEMPLATE'])
            elif 'header' == temp:
                if 'True' == str(data.get('isEmpty')):
                    read_path = os.path.join(
                        folder_path, current_app.config['THEME_HEADER_EDITOR_TEMPLATE'])
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


class ReportView(BaseView):

    @expose('/', methods=['GET'])
    def index(self):
        try:
            aggs_query = {
                "size": 0,
                "aggs": {
                    "aggs_term": {
                        "terms": {
                            "field": "publish_status",
                            "order": {"_count": "desc"}
                        }
                    }
                }
            }

            from invenio_stats.utils import get_aggregations
            aggs_results = get_aggregations('weko', aggs_query)

            total = 0
            result = {}
            if aggs_results and 'aggs_term' in aggs_results:
                for bucket in aggs_results['aggs_term']['buckets']:
                    bkt = {
                        'open': bucket['doc_count']} if bucket['key'] == '0' else {
                        'private': bucket['doc_count']}
                    result.update(bkt)
                    total = total + bucket['doc_count']

            result.update({'total': total})

            return self.render(
                current_app.config['WEKO_ADMIN_REPORT_TEMPLATE'],
                result=result)
        except Exception:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return abort(400)


class LanguageSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_LANG_SETTINGS"]
        )

class WebApiAccount(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_WEB_API_ACCOUNT"]
        )


class WidgetDesign(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_CHUNK_DESIGN"]
        )


class ChunkSettingView(ModelView):
    """Pidstore Identifier admin view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    create_template = config.WEKO_ADMIN_CHUNK_SETTINGS
    edit_template = config.WEKO_ADMIN_CHUNK_SETTINGS

    column_list = (
        'repository_id',
        'chunk_type',
        'label_color',
        'has_frame_border',
        'frame_border_color',
        'text_color',
        'background_color',
        'browsing_role',
        'edit_role',
        'is_enabled',
    )

    column_searchable_list = (
        'repository_id', 'chunk_type', 'label_color', 'has_frame_border')

    column_details_list = (
        'repository_id',
        'chunk_type',
        'label_color',
        'has_frame_border',
        'frame_border_color',
        'text_color',
        'background_color',
        'browsing_role',)

    form_extra_fields = {
        'repo_selected': StringField('Repository Selector'),
    }

    form_create_rules = [
        'repository_id',
        'chunk_type',
        'label_color',
        'has_frame_border',
        'frame_border_color',
        'text_color',
        'background_color',
        'browsing_role',
        'edit_role',
        'is_enabled',
        'repo_selected'
    ]

    form_edit_rules = form_create_rules

    column_labels = dict(repository_id=_('Repository'),
                         chunk_type=_('Chunk Type'),
                         label_color=_('Label color'),
                         has_frame_border=_('Has frame'),
                         frame_border_color=_('Frame border Color'),
                         text_color=_('Text color'),
                         background_color=_('Background color'),
                         browsing_role=_('Browsing role'),
                         )

    # def _validator_halfwidth_input(form, field):
    #     """
    #     Valid input character set.
    #
    #     :param form: Form used to create/update model
    #     :param field: Template fields contain data need validator
    #     """
    #     if field.data is None:
    #         return
    #     else:
    #         try:
    #             for inchar in field.data:
    #                 if unicodedata.east_asian_width(inchar) in 'FWA':
    #                     raise ValidationError(
    #                         _('Only allow halfwith 1-bytes character in input'))
    #         except Exception as ex:
    #             raise ValidationError('{}'.format(ex))
    #
    # form_args = {
    #     'jalc_doi': {
    #         'validators': [_validator_halfwidth_input]
    #     },
    #     'jalc_crossref_doi': {
    #         'validators': [_validator_halfwidth_input]
    #     },
    #     'jalc_datacite_doi': {
    #         'validators': [_validator_halfwidth_input]
    #     },
    #     'cnri': {
    #         'validators': [_validator_halfwidth_input]
    #     },
    #     'suffix': {
    #         'validators': [_validator_halfwidth_input]
    #     }
    # }
    #
    # form_widget_args = {
    #     'jalc_doi': {
    #         'maxlength': 100,
    #         'readonly': True,
    #     },
    #     'jalc_crossref_doi': {
    #         'maxlength': 100,
    #         'readonly': True,
    #     },
    #     'jalc_datacite_doi': {
    #         'maxlength': 100,
    #         'readonly': True,
    #     },
    #     'cnri': {
    #         'maxlength': 100,
    #         'readonly': True,
    #     },
    #     'suffix': {
    #         'maxlength': 100,
    #     }
    # }

    form_overrides = {
        'repository_id': QuerySelectField,
    }

    def on_model_change(self, form, model, is_created):
        """
        Perform some actions before a model is created or updated.

        Called from create_model and update_model in the same transaction
        (if it has any meaning for a store backend).
        By default does nothing.

        :param form: Form used to create/update model
        :param model: Model that will be created/updated
        :param is_created: Will be set to True if model was created
            and to False if edited
        """
        # Update hidden data automation
        if is_created:
            model.created_userId = current_user.get_id()
            model.created_date = datetime.utcnow().replace(microsecond=0)
        model.updated_userId = current_user.get_id()
        model.updated_date = datetime.utcnow().replace(microsecond=0)
        model.repository = str(model.repository.id)
        pass

    def on_form_prefill(self, form, id):
        form.repo_selected.data = form.repository.data
        pass

    def create_form(self, obj=None):
        """
        Instantiate model delete form and return it.

        Override to implement custom behavior.
        The delete form originally used a GET request, so delete_form
        accepts both GET and POST request for backwards compatibility.

        :param obj: input object
        """
        return self._use_append_repository(
            super(ChunkSettingView, self).create_form()
        )

    def edit_form(self, obj):
        """
        Instantiate model editing form and return it.

        Override to implement custom behavior.

        :param obj: input object
        """
        return self._use_append_repository(
            super(ChunkSettingView, self).edit_form(obj)
        )

    def _use_append_repository(self, form):
        print(form)
        # form.repository_id.query_factory = self._get_community_list
        # form.repo_selected.data = 'Root Index'
        return form

    def _get_community_list(self):
        try:
            from invenio_communities.models import Community
            query_data = Community.query.all()
            query_data.insert(0, Community(id='Root Index'))
        except Exception as ex:
            current_app.logger.debug(ex)

        return query_data


chunk_adminview = dict(
    modelview=ChunkSettingView,
    model=ChunkItem,
    category=_('Setting'),
    name=_('Widget Setting'),
)


style_adminview = {
    'view_class': StyleSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Style'),
        'endpoint': 'stylesetting'
    }
}

report_adminview = {
    'view_class': ReportView,
    'kwargs': {
        'category': _('Statistics'),
        'name': _('Report'),
        'endpoint': 'report'
    }
}

language_adminview = {
    'view_class': LanguageSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Language'),
        'endpoint': 'language'
    }
}

web_api_account_adminview = {
    'view_class': WebApiAccount,
    'kwargs': {
        'category': _('Setting'),
        'name': _('WebAPI Account'),
        'endpoint': 'webapiaccount'
    }
}


widget_design_adminview = {
    'view_class': WidgetDesign,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Widget Design'),
        'endpoint': 'widgetdesign'
    }
}

__all__ = (
    'chunk_adminview',
    'style_adminview',
    'report_adminview',
    'language_adminview',
    'web_api_account_adminview',
    'widget_design_adminview'
)
