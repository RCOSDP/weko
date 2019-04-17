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
# from flask_admin.form import rules
from flask_babelex import gettext as _
from flask_login import current_user
from wtforms.fields import StringField

from .models import WidgetItem
from . import config


class WidgetDesign(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_ADMIN_WIDGET_DESIGN"]
        )


class WidgetSettingView(ModelView):
    """Pidstore Identifier admin view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    create_template = config.WEKO_ADMIN_WIDGET_SETTINGS
    edit_template = config.WEKO_ADMIN_WIDGET_SETTINGS

    column_list = (
        'repository_id',
        'widget_type',
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
        'repository_id', 'widget_type', 'label_color', 'has_frame_border')

    column_details_list = (
        'repository_id',
        'widget_type',
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
        'widget_type',
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
                         widget_type=_('Widget Type'),
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
            super(WidgetSettingView, self).create_form()
        )

    def edit_form(self, obj):
        """
        Instantiate model editing form and return it.

        Override to implement custom behavior.

        :param obj: input object
        """
        return self._use_append_repository(
            super(WidgetSettingView, self).edit_form(obj)
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


widget_adminview = dict(
    modelview=WidgetSettingView,
    model=WidgetItem,
    category=_('Setting'),
    name=_('Widget Setting'),
)



widget_design_adminview = {
    'view_class': WidgetDesign,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Widget Design'),
        'endpoint': 'widgetdesign'
    }
}

__all__ = (
    'widget_adminview',
    'widget_design_adminview'
)
