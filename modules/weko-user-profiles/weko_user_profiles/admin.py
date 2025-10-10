# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
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

"""Admin views for weko-user-profiles."""
import os
from math import ceil

from flask import current_app, flash, redirect, request
from flask_admin import expose
from flask_admin.babel import gettext
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FormOpts
from flask_admin.helpers import get_redirect_target
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_babelex import lazy_gettext as __
from flask_security import current_user
from invenio_accounts.models import Role, User
from invenio_db import db
from wtforms import SelectField

from .config import USERPROFILES_LANGUAGE_LIST, USERPROFILES_TIMEZONE_LIST, \
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST
from .models import UserProfile
from .utils import get_role_by_position


def _(x):
    """Identity."""
    return x


class UserProfileView(ModelView):
    """Userprofiles view. Link User ID to user/full/display name."""

    can_view_details = True
    can_create = False

    column_list = (
        'user_id',
        '_displayname',
        'fullname',
        'timezone',
        'language',
    )

    column_searchable_list = \
        column_filters = \
        column_details_list = \
        columns_sortable_list = \
        column_list

    form_columns = (
        'username',
        'fullname',
        'timezone',
        'language')

    column_labels = {
        '_displayname': __('Username'),
        'fullname': __('Fullname'),
        'timezone': __('Timezone'),
        'language': __('Language'),
    }

    column_choices = {
        'timezone': USERPROFILES_TIMEZONE_LIST,
        'language': USERPROFILES_LANGUAGE_LIST
    }

    form_args = dict(
        timezone=dict(
            choices=USERPROFILES_TIMEZONE_LIST,
        ),
        language=dict(
            choices=USERPROFILES_LANGUAGE_LIST
        )
    )
    form_overrides = dict(
        timezone=SelectField,
        language=SelectField
    )

    form_widget_args = {
        'otherPosition': {
            'placeholder': __('Input when selecting Others'),
        }
    }

    """column_list"""
    column_list = column_list + (
        'university',
        'department',
        'position',
        'item1',
        'item2',
        'item3',
        'item4',
        'item5',
        'item6',
        'item7',
        'item8',
        'item9',
        'item10',
        'item11',
        'item12',
        'item13',
        'item14',
        'item15',
        'item16'
    )
    """form_columns"""
    form_columns = form_columns + (
        'university',
        'department',
        'position',
        'item1',
        'item2',
        'item3',
        'item4',
        'item5',
        'item6',
        'item7',
        'item8',
        'item9',
        'item10',
        'item11',
        'item12',
        'item13',
        'item14',
        'item15',
        'item16'
    )
    """column_labels"""
    column_labels['university'] = __('University/Institution')
    column_labels['department'] = __('Affiliated Division/Department')
    column_labels['position'] = __('Position')
    column_labels['otherPosition'] = __('Position (Others)')
    column_labels['phoneNumber'] = __('Phone number')
    column_labels['instituteName'] = __('Affiliated Institution Name')
    column_labels['institutePosition'] = \
        __('Affiliated Institution Position')
    column_labels['instituteName2'] = __('Affiliated Institution Name')
    column_labels['institutePosition2'] = \
        __('Affiliated Institution Position')
    column_labels['instituteName3'] = __('Affiliated Institution Name')
    column_labels['institutePosition3'] = \
        __('Affiliated Institution Position')
    column_labels['instituteName4'] = __('Affiliated Institution Name')
    column_labels['institutePosition4'] = \
        __('Affiliated Institution Position')
    column_labels['instituteName5'] = __('Affiliated Institution Name')
    column_labels['institutePosition5'] = \
        __('Affiliated Institution Position')

    """column_choices"""
    column_choices['position'] = WEKO_USERPROFILES_POSITION_LIST
    column_choices['institutePosition'] = \
        WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    column_choices['institutePosition2'] = \
        WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    column_choices['institutePosition3'] = \
        WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    column_choices['institutePosition4'] = \
        WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    column_choices['institutePosition5'] = \
        WEKO_USERPROFILES_INSTITUTE_POSITION_LIST

    """form_args"""
    form_args["position"] = dict(choices=WEKO_USERPROFILES_POSITION_LIST)
    form_args["institutePosition"] = \
        dict(choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST)
    form_args["institutePosition2"] = \
        dict(choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST)
    form_args["institutePosition3"] = \
        dict(choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST)
    form_args["institutePosition4"] = \
        dict(choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST)
    form_args["institutePosition5"] = \
        dict(choices=WEKO_USERPROFILES_INSTITUTE_POSITION_LIST)

    """form_overrides"""
    form_overrides["position"] = SelectField
    form_overrides["institutePosition"] = SelectField
    form_overrides["institutePosition2"] = SelectField
    form_overrides["institutePosition3"] = SelectField
    form_overrides["institutePosition4"] = SelectField
    form_overrides["institutePosition5"] = SelectField

    def search_placeholder(self):
        """Return search placeholder."""
        return 'Search'

    def on_form_prefill(self, form, id):
        """Return form prefill."""
        form_column = current_app.config['WEKO_USERPROFILES_FORM_COLUMN']
        if isinstance(form_column, list):
            for field in list(form):
                if field.name not in form_column:
                    delattr(form, field.name)
        return form

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

        form_column = current_app.config['WEKO_USERPROFILES_FORM_COLUMN']
        if isinstance(form_column, list):
            form_column.append("user_id")
            form_column.append("_displayname")
            new_column = list()
            for column in self._list_columns:
                if column[0] in form_column:
                    new_column.append(column)
            self._list_columns = new_column

        return self.render(
            self.list_template,
            data=data,
            list_forms=list_forms,
            delete_form=delete_form,
            action_form=action_form,

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

            # Extras
            extra_args=view_args.extra_args,
        )

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self):
        """Edit model view."""
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_edit:
            return redirect(return_url)

        id = get_mdict_item_or_list(request.args, 'id')

        if id is None:
            return redirect(return_url)

        model = self.get_one(id)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)
        form = self.edit_form(obj=model)
        if not hasattr(form,
                       '_validated_ruleset') or not form._validated_ruleset:
            self._validate_form_instance(ruleset=self._form_edit_rules,
                                         form=form)

        if self.validate_form(form):
            if self.update_model(form, model):
                try:
                    with db.session.begin_nested():
                        """Get role by position"""
                        if (current_app.config['USERPROFILES_EMAIL_ENABLED']
                                and form.position):
                            role_name = get_role_by_position(form.position.data)
                            roles1 = db.session.query(Role).filter_by(
                                name=role_name).all()
                            """Get account_user by user profile id"""
                            account_user = db.session.query(User).filter_by(
                                id=id).first()
                            admin_role = current_app.config.get(
                                "WEKO_USERPROFILES_ADMINISTRATOR_ROLE")
                            userprofile_roles = current_app.config.get(
                                "WEKO_USERPROFILES_ROLES")
                            roles2 = [
                                role for role in account_user.roles
                                if
                                role not in userprofile_roles or role == admin_role
                            ]
                            roles = roles1 + roles2
                            account_user.roles = roles
                        """Set role for user"""
                        db.session.add(account_user)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(e)
                flash(gettext('Record was successfully saved.'), 'success')
                if '_add_another' in request.form:
                    return redirect(
                        self.get_url('.create_view', url=return_url))
                elif '_continue_editing' in request.form:
                    return redirect(request.url)
                else:
                    # save button
                    return redirect(
                        self.get_save_return_url(model, is_created=False))

        if request.method == 'GET' or form.errors:
            self.on_form_prefill(form, id)

        form_opts = FormOpts(widget_args=self.form_widget_args,
                             form_rules=self._form_edit_rules)
        if self.edit_modal and request.args.get('modal'):
            template = self.edit_modal_template
        else:
            template = self.edit_template

        return self.render(template,
                           model=model,
                           form=form,
                           form_opts=form_opts,
                           return_url=return_url)

    _system_role = os.environ.get('INVENIO_ROLE_SYSTEM',
                                  'System Administrator')

    @property
    def can_delete(self):
        """Check permission for Deleting."""
        return self._system_role in [role.name for role in current_user.roles]

    @property
    def can_edit(self):
        """Check permission for Editing."""
        return self._system_role in [role.name for role in current_user.roles]


user_profile_adminview = {
    'model': UserProfile,
    'modelview': UserProfileView,
    'category': _('User Management'),
}
