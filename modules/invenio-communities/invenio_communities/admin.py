# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Admin model views for Communities."""

from __future__ import absolute_import, print_function

import re

from flask_admin.contrib.sqla import ModelView
from wtforms.validators import ValidationError

from .models import Community, FeaturedCommunity, InclusionRequest


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
        'owner.id',
        'index.index_name',
        'deleted_at',
        'last_record_accepted',
        'ranking',
        'fixed_points',
    )
    column_searchable_list = ('id', 'title', 'description')
    edit_template = "invenio_communities/admin/edit.html"

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

        if the_patterns['FIRST_LETTER_PATTERN1']:
            m = re.match(the_patterns['FIRST_LETTER_PATTERN1'], field.data)
            if m is None:
                raise ValidationError(the_result['FIRST_LETTER_PATTERN1'])
            if the_patterns['FIRST_LETTER_PATTERN2']:
                m = re.match(the_patterns['FIRST_LETTER_PATTERN2'], field.data)
                if m is not None:
                    raise ValidationError(the_result['FIRST_LETTER_PATTERN2'])
                if the_patterns['ASCII_LETTER_PATTERN']:
                    m = re.match(the_patterns['ASCII_LETTER_PATTERN'],
                                 field.data)
                    if m is None:
                        raise ValidationError(
                            the_result['ASCII_LETTER_PATTERN'])
        if field.data:
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


community_adminview = dict(
    model=Community,
    modelview=CommunityModelView,
    category=_('Communities'),
)

request_adminview = dict(
    model=InclusionRequest,
    modelview=InclusionRequestModelView,
    category=_('Communities'),
)

featured_adminview = dict(
    model=FeaturedCommunity,
    modelview=FeaturedCommunityModelView,
    category=_('Communities'),
)
