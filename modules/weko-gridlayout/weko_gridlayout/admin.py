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

import json
from collections import namedtuple

from flask import current_app, flash, redirect, request
from flask_admin import BaseView, expose
from flask_admin._backwards import ObsoleteAttr
from flask_admin.babel import gettext
from flask_admin.contrib.sqla import ModelView
from flask_admin.helpers import get_redirect_target
from flask_admin.model import helpers, typefmt
from flask_babelex import gettext as _
from jinja2 import contextfunction
from sqlalchemy import func
from wtforms.fields import StringField

from . import config
from .api import WidgetItems
from .models import WidgetItem
from .utils import validate_admin_widget_item_setting


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
    can_delete = True
    can_view_details = True
    column_formatters_detail = ObsoleteAttr('column_formatters',
                                            'list_formatters', dict())
    column_type_formatters_detail = dict(typefmt.EXPORT_FORMATTERS)

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_create:
            return redirect(return_url)
        return self.render(config.WEKO_GRIDLAYOUT_ADMIN_CREATE_WIDGET_SETTINGS,
                           return_url=return_url)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """Define Api for edit view.

        Returns:
            HTML page -- Html page for edit view

        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id_list = helpers.get_mdict_item_or_list(request.args, 'id')

        model = self.get_one(id_list)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)
        model = WidgetItems.parse_result(model)

        return self.render(config.WEKO_GRIDLAYOUT_ADMIN_EDIT_WIDGET_SETTINGS,
                           model=json.dumps(model),
                           return_url=return_url)

    @contextfunction
    def get_detail_value(self, context, model, name):
        """Returns the value to be displayed in the detail view.

        :param context:
            :py:class:`jinja2.runtime.Context`
            :param model: Model instance
            :param name: Field name
        """
        data_settings = model.settings
        data_settings = json.loads(data_settings)
        data_settings_model = namedtuple("Settings", data_settings.keys())(
            *data_settings.values())
        if name == "label_color" or name == "has_frame_border" \
                or name == "frame_border_color" or name == "text_color" \
                or name == "background_color":
            return super()._get_list_value(
                context,
                data_settings_model,
                name,
                self.column_formatters_detail,
                self.column_type_formatters_detail,
            )
        else:
            return super()._get_list_value(
                context,
                model,
                name,
                self.column_formatters_detail,
                self.column_type_formatters_detail,
            )

    @expose('/details/')
    def details_view(self):
        """Details model view."""
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_view_details:
            return redirect(return_url)

        id = helpers.get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        if self.details_modal and request.args.get('modal'):
            template = self.details_modal_template
        else:
            template = self.details_template

        return self.render(template,
                           model=model,
                           details_columns=self._details_columns,
                           get_value=self.get_detail_value,
                           return_url=return_url)

    def get_query(self):
        return self.session.query(
            self.model).filter(self.model.is_deleted == 'False')

    def get_count_query(self):
        return self.session.query(
            func.count('*')).filter(self.model.is_deleted == 'False')

    def delete_model(self, model):
        """Delete model.

        :param model:
            Model to delete
        """
        try:
            if not self.on_model_delete(model):
                flash(_("Cannot delete widget (Repository:%(repo)s, "
                        "Widget Type:%(type)s, Label: %(label)s) "
                        "because it's setting in Widget Design.",
                        repo=model.repository_id, type=model.widget_type,
                        label=model.label), 'error')
                return False
            self.session.flush()
            WidgetItem.delete(model.repository_id,
                              model.widget_type,
                              model.label, self.session)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(_('Failed to delete record. %(error)s',
                        error=str(ex)), 'error')
                current_app.logger.error('Failed to delete record: ', ex)

            self.session.rollback()

            return False
        else:
            self.after_model_delete(model)

        return True

    def on_model_delete(self, model):
        """Define action before delete model.

        Arguments:
            model {widget_item} -- [item to be deleted]

        Returns:
            [false] -- [it is being used in widget design]
            [true] -- [it isn't being used in widget design]

        """
        if validate_admin_widget_item_setting(model):
            return False
        return True

    column_list = (
        'repository_id',
        'widget_type',
        'label',
        'is_enabled',
    )

    column_searchable_list = (
        'repository_id', 'widget_type', 'label', 'is_enabled')

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
                         is_enabled=_('Enable'),
                         )


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
