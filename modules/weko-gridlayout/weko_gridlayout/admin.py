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

from flask import current_app, request
from flask_admin import BaseView, expose
from flask_admin.model import helpers
from flask_admin.contrib.sqla import ModelView
from flask_babelex import gettext as _
from wtforms.fields import StringField

from .models import WidgetItem
from . import config


class WidgetDesign(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        return self.render(
            current_app.config["WEKO_GRIDLAYOUT_ADMIN_WIDGET_DESIGN"]
        )


class WidgetSettingView(ModelView):
    """Widget Setting admin view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        return self.render(config.WEKO_GRIDLAYOUT_ADMIN_WIDGET_SETTINGS)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """
            Edit model view
        """

        id_list = helpers.get_mdict_item_or_list(request.args, 'id')

        return self.render(config.WEKO_GRIDLAYOUT_ADMIN_WIDGET_SETTINGS)

    column_list = (
        'repository_id',
        'widget_type',
        'label',
        'label_color',
        'is_enabled',
    )

    column_searchable_list = (
        'repository_id', 'widget_type', 'label_color', 'has_frame_border')

    column_details_list = (
        'repository_id',
        'widget_type',
        'label',
        'label_color',
        'has_frame_border',
        'frame_border_color',
        'text_color',
        'background_color',
        'browsing_role',)

    form_extra_fields = {
        'repo_selected': StringField('Repository Selector'),
    }

    column_labels = dict(repository_id=_('Repository'),
                         widget_type=_('Widget Type'),
                         label=_('Label'),
                         label_color=_('Label color'),
                         is_enabled=_('Enable'),
                         )

    def on_form_prefill(self, form, id):
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
    name=_('Widget'),
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
