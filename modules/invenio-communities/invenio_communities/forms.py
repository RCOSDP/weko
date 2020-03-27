# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015, 2016, 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Forms for communities."""

from __future__ import absolute_import, print_function

import re

from flask_babelex import gettext as _
from flask_wtf import Form
from wtforms import FileField, HiddenField, StringField, TextAreaField, \
    validators
from wtforms.validators import ValidationError

from .models import Community


def _validate_input_id(form, field):
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
                m = re.match(the_patterns['ASCII_LETTER_PATTERN'], field.data)
                if m is None:
                    raise ValidationError(the_result['ASCII_LETTER_PATTERN'])


class CommunityForm(Form):
    """Community form."""

    field_sets = [
        ('Information',
         ['identifier', 'title', 'description', 'curation_policy', 'page',
          'community_header', 'community_footer', 'logo',
          'index_checked_nodeId'],
         {'classes': 'in'}),
    ]

    field_placeholders = {
    }

    field_state_mapping = {
    }

    @property
    def data(self):
        """Form data."""
        d = super(CommunityForm, self).data
        d.pop('csrf_token', None)
        return d

    #
    # Methods
    #
    def get_field_icon(self, name):
        """Return field icon."""
        return self.field_icons.get(name, '')

    def get_field_by_name(self, name):
        """Return field by name."""
        try:
            return self._fields[name]
        except KeyError:
            return None

    def get_field_placeholder(self, name):
        """Return field placeholder."""
        return self.field_placeholders.get(name, '')

    def get_field_state_mapping(self, field):
        """Return field state mapping."""
        try:
            return self.field_state_mapping[field.short_name]
        except KeyError:
            return None

    def has_field_state_mapping(self, field):
        """Check if field has state mapping."""
        return field.short_name in self.field_state_mapping

    def has_autocomplete(self, field):
        """Check if filed has autocomplete."""
        return hasattr(field, 'autocomplete')

    #
    # Fields
    #
    identifier = StringField(
        label=_('Identifier'),
        description=_('The identifier is used in the URL for the community'
                      ' collection, and cannot be modified later.'),
        validators=[validators.DataRequired(),
                    validators.length(
                        max=100,
                        message=_(
                            'Field cannot be longer than 100 characters.')),
                    _validate_input_id]
    )

    title = StringField(
        validators=[validators.DataRequired()]
    )

    description = TextAreaField(
        description=_(
            'Optional. A short description of the community collection,'
            ' which will be displayed on the index page of the community.'),
    )

    curation_policy = TextAreaField(
        description=_(
            'Optional. Please describe briefly and precisely the policy by '
            'which you accepted/reject new uploads in this community.'),
    )

    page = TextAreaField(
        description=_(
            'Optional. A long description of the community collection, '
            'which will be displayed on a separate page linked from '
            'the index page.'),
    )

    field_icons = {
        'identifier': 'barcode',
        'title': 'file-alt',
        'description': 'pencil',
        'curation_policy': 'check',
    }

    logo = FileField(
        label=_('Logo'),
        description=_(
            'Optional. Image file used to aid and promote instant public '
            'recognition. Supported formats: PNG, JPG and SVG. '
            'Max file size: 1.5 MB')
    )

    index_checked_nodeId = HiddenField(
        label=_('')
    )

    #
    # Validation
    #
    def validate_identifier(self, field):
        """Validate field identifier."""
        if field.data:
            field.data = field.data.lower()
            if Community.get(field.data, with_deleted=True):
                raise validators.ValidationError(
                    _('The identifier already exists. '
                      'Please choose a different one.'))


class EditCommunityForm(CommunityForm):
    """Edit community form.

    Same as collection form, except identifier is removed.
    """

    identifier = None


class DeleteCommunityForm(Form):
    """Confirm deletion of a collection."""

    delete = HiddenField(default='yes', validators=[validators.DataRequired()])


class SearchForm(Form):
    """Search Form."""

    p = StringField(
        validators=[validators.DataRequired()]
    )
