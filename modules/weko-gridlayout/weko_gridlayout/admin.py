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

import pickle
import json
from collections import namedtuple
from datetime import datetime
from math import ceil

from flask import current_app, flash, redirect, request
from flask_admin import BaseView, expose
from flask_admin._backwards import ObsoleteAttr
from flask_admin.actions import action
from flask_admin.babel import gettext, lazy_gettext, ngettext
from flask_admin.contrib.sqla import ModelView, tools
from flask_admin.helpers import get_redirect_target
from flask_admin.model import helpers, typefmt
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_communities.models import Community
from jinja2 import contextfunction
from sqlalchemy import func
from wtforms.fields import StringField

from . import config
from .models import WidgetItem, WidgetMultiLangData
from .services import WidgetDesignServices, WidgetItemServices
from .utils import convert_data_to_design_pack, convert_data_to_edit_pack, \
    convert_widget_data_to_dict, get_register_language, \
    get_unregister_language


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

    def search_placeholder(self):
        """Return search placeholder."""
        return 'Search'

    @staticmethod
    def get_label_display_to_list(widget_id):
        """Helper to get label to display to list.

        Arguments:
            widget_id {int} -- id of widget item

        Return: label to display to list

        """
        register_language = get_register_language()
        multi_lang_data = WidgetMultiLangData.get_by_widget_id(widget_id)

        for lang in register_language:
            for data in multi_lang_data:
                if lang.get('lang_code') == data.lang_code:
                    return data.label

        unregister_language = get_unregister_language()
        for lang in unregister_language:
            for data in multi_lang_data:
                if lang.get('lang_code') == data.lang_code:
                    return data.label
        return None

    # Views
    @expose('/')
    def index_view(self):
        """List view."""
        if self.can_delete:
            delete_form = self.delete_form()
        else:
            delete_form = None

        # Grab parameters from URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get page size
        page_size = view_args.page_size or self.page_size

        # Get count and data
        count, data = self.get_list(view_args.page, sort_column,
                                    view_args.sort_desc,
                                    view_args.search, view_args.filters,
                                    page_size=page_size)

        list_forms = {}
        if self.column_editable_list:
            for row in data:
                list_forms[self.get_pk_value(row)] = self.list_form(obj=row)

        # Calculate number of pages
        if count is not None and page_size:
            num_pages = int(ceil(count / float(page_size)))
        elif not page_size:
            num_pages = 0  # hide pager for unlimited page_size
        else:
            num_pages = None  # use simple pager

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_list_url(view_args.clone(page=p))

        def sort_url(column, invert=False, desc=None):
            if not desc and invert and not view_args.sort_desc:
                desc = 1

            return self._get_list_url(
                view_args.clone(sort=column, sort_desc=desc))

        def page_size_url(s):
            if not s:
                s = self.page_size

            return self._get_list_url(view_args.clone(page_size=s))

        # Actions
        actions, actions_confirmation = self.get_actions_list()
        if actions:
            action_form = self.action_form()
        else:
            action_form = None

        clear_search_url = self._get_list_url(
            view_args.clone(page=0,
                            sort=view_args.sort,
                            sort_desc=view_args.sort_desc,
                            search=None,
                            filters=None))

        list_data = list()
        for widget_item in data:
            obj = pickle.loads(pickle.dumps(widget_item, -1))
            label = WidgetSettingView.get_label_display_to_list(
                widget_item.widget_id)
            obj.label = label
            list_data.append(obj)

        return self.render(
            self.list_template,
            data=list_data,
            list_forms=list_forms,
            delete_form=delete_form,
            action_form=action_form,
            extra_args=view_args.extra_args,

            # List
            list_columns=self._list_columns,
            sortable_columns=self._sortable_columns,
            editable_columns=self.column_editable_list,
            list_row_actions=self.get_list_row_actions(),

            # Pagination
            count=count,
            pager_url=pager_url,
            num_pages=num_pages,
            can_set_page_size=self.can_set_page_size,
            page_size_url=page_size_url,
            page=view_args.page,
            page_size=page_size,
            default_page_size=self.page_size,

            # Sorting
            sort_column=view_args.sort,
            sort_desc=view_args.sort_desc,
            sort_url=sort_url,

            # Search
            search_supported=self._search_supported,
            clear_search_url=clear_search_url,
            search=view_args.search,
            search_placeholder=self.search_placeholder(),

            # Filters
            filters=self._filters,
            filter_groups=self._get_filter_groups(),
            active_filters=view_args.filters,
            filter_args=self._get_filters(view_args.filters),

            # Actions
            actions=actions,
            actions_confirmation=actions_confirmation,

            # Misc
            enumerate=enumerate,
            get_pk_value=self.get_pk_value,
            get_value=self.get_list_value,
            return_url=self._get_list_url(view_args),
        )

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

        # Check Edit widget is locked by other user.
        locked_widget = WidgetItemServices.get_locked_widget_info(
            id_list)
        if isinstance(locked_widget, WidgetItem):
            locked, locked_time = locked_widget.locked, \
                locked_widget.updated
            return self.render(
                config.WEKO_GRIDLAYOUT_ADMIN_EDIT_WIDGET_SETTINGS,
                model={},
                return_url=return_url, locked=locked)

        widget_data_from_db = self.get_one(id_list)
        widget_data = convert_widget_data_to_dict(widget_data_from_db)
        multi_lang_data = WidgetMultiLangData.get_by_widget_id(id_list)
        converted_data = convert_data_to_design_pack(
            widget_data,
            multi_lang_data)
        model = convert_data_to_edit_pack(converted_data)
        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        if isinstance(locked_widget, str):
            locked_value = locked_widget
            locked = True
        else:
            locked = False
            locked_value = str(datetime.utcnow().timestamp())
            WidgetItemServices.lock_widget(widget_id=id_list,
                                           locked_value=locked_value)
        return self.render(config.WEKO_GRIDLAYOUT_ADMIN_EDIT_WIDGET_SETTINGS,
                           model=json.dumps(model),
                           return_url=return_url,
                           locked_value=locked_value,
                           locked=locked
                           )

    @contextfunction
    def get_detail_value(self, context, model, name):
        """Returns the value to be displayed in the detail view.

        :param context:
            :py:class:`jinja2.runtime.Context`
            :param model: Model instance
            :param name: Field name
        """
        data_settings = model.settings
        data_settings = json.loads(data_settings) \
            if isinstance(data_settings, str) else data_settings
        data_settings_model = namedtuple("Settings", data_settings.keys())(
            *data_settings.values())
        if name == "label_color" or name == "frame_border" \
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

        widget_item_id = helpers.get_mdict_item_or_list(request.args, 'id')
        if widget_item_id is None:
            return redirect(return_url)

        model = self.get_one(widget_item_id)
        label = WidgetSettingView.get_label_display_to_list(model.widget_id)
        model.label = label

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

    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete selected records?'))
    def action_delete(self, ids):
        try:
            query = tools.get_query_for_ids(self.get_query(), self.model, ids)

            if self.fast_mass_delete:
                count = query.delete(synchronize_session=False)
            else:
                count = 0
                for m in query.all():
                    if self.delete_model(m, self.session):
                        count += 1

            self.session.commit()

            flash(ngettext('Record was successfully deleted.',
                           '%(count)s records were successfully deleted.',
                           count,
                           count=count), 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to delete records. %(error)s',
                          error=str(ex)), 'error')

    def get_query(self):
        if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
            return self.session.query(self.model).filter(
                self.model.is_deleted == 'False')
        else:
            repositories = Community.get_repositories_by_user(current_user)
            repository_ids = [repository.id for repository in repositories]
            return self.session.query(self.model).filter(
                self.model.is_deleted == 'False').filter(
                    self.model.repository_id.in_(repository_ids))

    def get_count_query(self):
        if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
            return self.session.query(func.count('*')).filter(
                self.model.is_deleted == 'False')
        else:
            repositories = Community.get_repositories_by_user(current_user)
            repository_ids = [repository.id for repository in repositories]
            return self.session.query(func.count('*')).filter(
                self.model.is_deleted == 'False').filter(
                    self.model.repository_id.in_(repository_ids))


    def delete_model(self, model, session=None):
        """Delete model.

        :param
        model: Model to delete
        session: session to delete
        """
        if not self.on_model_delete(model):
            flash(_("Cannot delete widget (ID: %(widget_id)s, "
                    "because it's setting in Widget Design.",
                    widget_id=model.widget_id),
                  'error')
            return False
        try:
            if session:
                WidgetItemServices.delete_multi_item_by_id(model.widget_id,
                                                           session)
                return True
            else:
                self.session.flush()
                WidgetItemServices.delete_by_id(model.widget_id)
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
        if WidgetDesignServices.is_used_in_widget_design(
                model.widget_id):
            return False
        return True

    column_list = (
        'widget_id',
        'repository_id',
        'widget_type',
        'label',
        'is_enabled',
    )

    column_searchable_list = (
        'widget_id','repository_id', 'widget_type', 'is_enabled')

    column_sortable_list = (
        'widget_id', 'repository_id', 'widget_type', 'is_enabled')

    column_filters = ('widget_id','repository_id', 'widget_type','is_enabled')

    column_details_list = (
        'repository_id',
        'widget_type',
        'label',
        'label_color',
        'frame_border',
        'frame_border_color',
        'text_color',
        'background_color',
        'browsing_role',)

    form_extra_fields = {
        'repo_selected': StringField('Repository Selector'),
    }

    column_labels = dict(widget_id=_('ID'),
                         repository_id=_('Repository'),
                         widget_type=_('Widget Type'),
                         label=_('Label'),
                         is_enabled=_('Enable'),
                         frame_border=_('Has Frame Border'),
                         )


widget_adminview = dict(
    modelview=WidgetSettingView,
    model=WidgetItem,
    category=_('Web Design'),
    name=_('Widget'),
)

widget_design_adminview = {
    'view_class': WidgetDesign,
    'kwargs': {
        'category': _('Web Design'),
        'name': _('Page Layout'),
        'endpoint': 'widgetdesign'
    }
}

__all__ = (
    'widget_adminview',
    'widget_design_adminview'
)
