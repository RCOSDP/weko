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

"""Group Forms."""

from flask_babelex import gettext as _
from flask_wtf import FlaskForm
from sqlalchemy_utils.types.choice import ChoiceType
from wtforms import RadioField, TextAreaField
from wtforms.validators import (
    DataRequired, Email, StopValidation, ValidationError)
from wtforms_alchemy import ClassMap, model_form_factory

from .models import Group

ModelForm = model_form_factory(FlaskForm)


class EmailsValidator(object):
    """Validates TextAreaField containing emails.

    Runs DataRequired validator on whole field and additionaly for each email
    parsed it runs Email validator.
    """

    def __init__(self):
        """Init all used validators."""
        self.validate_data = DataRequired()
        self.validate_email = Email()

    def __call__(self, form, field):
        """
        Parse emails and run validators.

        :param form:
        :param field:
        """
        self.validate_data(form, field)

        emails_org = field.data
        emails = filter(None, emails_org.splitlines())
        for email in emails:
            try:
                field.data = email
                self.validate_email(form, field)
            except (ValidationError, StopValidation):
                raise ValidationError('Invalid email: ' + email)
            finally:
                field.data = emails_org


class GroupForm(ModelForm):
    """Form for creating and updating a group."""

    class Meta:
        """Metadata class."""

        model = Group
        type_map = ClassMap({ChoiceType: RadioField})
        exclude = [
            'is_managed',
            'privacy_policy',
            'subscription_policy',
        ]


class NewMemberForm(FlaskForm):
    """For for adding new members to a group."""

    emails = TextAreaField(
        description=_(
            'Required. Provide list of the emails of the users'
            ' you wish to be added. Put each email in new line.'),
        validators=[EmailsValidator()]
    )
