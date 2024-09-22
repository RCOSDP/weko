# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for Communities."""

from __future__ import absolute_import, print_function

import re

from flask.globals import current_app
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from invenio_db import db
from sqlalchemy import func, or_
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from wtforms.validators import ValidationError

from .models import Community, FeaturedCommunity, InclusionRequest
from .utils import get_user_role_ids


def _(x):
    """Identity function for string extraction."""
    return x


class CommunityModelView(ModelView):
    """ModelView for the Community."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    column_display_all_relations = True
    form_columns = ('id', 'owner', 'index', 'title', 'description', 'page',
                    'curation_policy', 'ranking', 'fixed_points')

    column_list = (
        'id',
        'title',
        'owner.name',
        'index',
        'deleted_at',
        'last_record_accepted',
        'ranking',
        'fixed_points',
    )
    column_searchable_list = ('id', 'title', 'description')

    edit_template = "invenio_communities/admin/edit.html"

    def on_model_change(self, form, model, is_created):
        """Perform some actions before a model is created or updated.

        Called from create_model and update_model in the same transaction
        (if it has any meaning for a store backend).
        By default does nothing.

        :param form:
            Form used to create/update model
        :param model:
            Model that will be created/updated
        :param is_created:
            Will be set to True if model was created and to False if edited
        """
        model.id_user = current_user.get_id()

    def _validate_input_id(self, field):
        the_patterns = {
            "ASCII_LETTER_PATTERN": "[a-zA-Z0-9_-]+$",
            "FIRST_LETTER_PATTERN1": "^[a-zA-Z_-].*",
            "FIRST_LETTER_PATTERN2": "^[-]+[0-9]+",
        }
        the_result = {
            "ASCII_LETTER_PATTERN": "Don't use space or special "
                                    "character except `-` and `_`.",
            "FIRST_LETTER_PATTERN1": 'The first character cannot '
                                     'be a number or special character. '
                                     'It should be an '
                                     'alphabet character, "-" or "_"',
            "FIRST_LETTER_PATTERN2": "Cannot set negative number to ID.",
        }

        m = re.match(the_patterns['FIRST_LETTER_PATTERN1'], field.data)
        if m is None:
            raise ValidationError(the_result['FIRST_LETTER_PATTERN1'])
        m = re.match(the_patterns['FIRST_LETTER_PATTERN2'], field.data)
        if m is not None:
            raise ValidationError(the_result['FIRST_LETTER_PATTERN2'])
        m = re.match(the_patterns['ASCII_LETTER_PATTERN'], field.data)
        if m is None:
            raise ValidationError(the_result['ASCII_LETTER_PATTERN'])
        field.data = field.data.lower()

    form_args = {
        'id': {
            'validators': [_validate_input_id]
        }
    }

    form_widget_args = {
        'id': {
            'placeholder': 'Please select ID',
            'maxlength': 100,
        }
    }

    def role_query_cond(self, role_ids):
        """Query conditions by role_id and user_id."""
        if role_ids:
            return or_(
                Community.id_role.in_(role_ids),
                Community.id_user == current_user.id
            )

    def get_query(self):
        """Return a query for the model type.

        This method can be used to set a "persistent filter" on an index_view.
        If you override this method, don't forget to also override
        `get_count_query`,
        for displaying the correct
        item count in the list view, and `get_one`,
        which is used when retrieving records for the edit view.
        """
        role_ids = get_user_role_ids()

        if (min(role_ids) <=
                current_app.config['COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT']):
            return self.session.query(self.model).filter()

        return self.session.query(
            self.model).filter(self.role_query_cond(role_ids))

    def get_count_query(self):
        """Return a the count query for the model type.

        A ``query(self.model).count()`` approach produces an excessive
        subquery, so ``query(func.count('*'))`` should be used instead.
        """
        role_ids = get_user_role_ids()

        if (min(role_ids) <=
                current_app.config['COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT']):
            return self.session.query(func.count('*')).select_from(self.model)

        return self.session.query(
            func.count('*')
        ).select_from(self.model).filter(self.role_query_cond(role_ids))

    def edit_form(self, obj=None):
        """
        Instantiate model editing form and return it.

        Override to implement custom behavior.

        :param obj: input object
        """
        role_ids = get_user_role_ids()

        if (min(role_ids) <=
                current_app.config['COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT']):
            return super().edit_form(obj)

        return self._use_append_repository_edit(
            super().edit_form(obj),
            str(obj.index.id)
        )

    def _use_append_repository_edit(self, form, index_id: str):
        """Modified query_factory of index column.

        The query_factory callable passed to the field constructor will be
        called to obtain a query.
        """
        setattr(self, 'index_id', index_id)
        form.index.query_factory = self._get_child_index_list
        setattr(form, 'action', 'edit')
        return form

    def _get_child_index_list(self):
        """Query child indexes."""
        index_id = str(getattr(self, 'index_id', ''))

        with db.session.no_autoflush:
            _query = list(
                item.cid for item in Indexes.get_recursive_tree(index_id))
            query = Index.query.filter(
                Index.id.in_(_query)).order_by(Index.id.asc()).all()

        return query


class FeaturedCommunityModelView(ModelView):
    """ModelView for the FeaturedCommunity."""

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    column_display_all_relations = True
    column_list = (
        'community',
        'start_date',
    )


class InclusionRequestModelView(ModelView):
    """ModelView of the InclusionRequest."""

    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    column_list = (
        'id_community',
        'id_record',
        'expires_at',
        'id_user'
    )


community_adminview = {
    'model': Community,
    'modelview': CommunityModelView,
    'category': _('Communities'),
}

request_adminview = {
    'model': InclusionRequest,
    'modelview': InclusionRequestModelView,
    'category': _('Communities'),
}

featured_adminview = {
    'model': FeaturedCommunity,
    'modelview': FeaturedCommunityModelView,
    'category': _('Communities'),
}
