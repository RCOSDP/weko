# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Define forms for generating access tokens and clients."""

from flask_babelex import lazy_gettext as _
from flask_wtf import FlaskForm as Form
from oauthlib.oauth2.rfc6749.errors import InsecureTransportError, \
    InvalidRedirectURIError
from wtforms import fields, validators, widgets
from wtforms.widgets import HTMLString
from wtforms_alchemy import model_form_factory

from .models import Client
from .validators import URLValidator, validate_redirect_uri


#
# Widget
#
def scopes_multi_checkbox(field, **kwargs):
    """Render multi checkbox widget."""
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)

    html = [u'<div class="row">']

    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)

        options = dict(
            kwargs,
            name=field.name,
            value=value,
            id=choice_id,
            class_=' ',
        )

        if checked:
            options['checked'] = 'checked'

        html.append(u'<div class="col-md-3">')
        html.append(u'<label for="{0}" class="checkbox-inline">'.format(
            field_id
        ))
        html.append(u'<input {0} /> '.format(widgets.html_params(**options)))
        html.append(u'{0} <br/><small class="text-muted">{1}</small>'.format(
            value, label.help_text
        ))
        html.append(u'</label></div>')
    html.append(u'</div>')

    return HTMLString(u''.join(html))


#
# Redirect URI field
#
class RedirectURIField(fields.TextAreaField):
    """Process redirect URI field data."""

    def process_formdata(self, valuelist):
        """Process form data."""
        if valuelist:
            self.data = '\n'.join([
                x.strip() for x in
                filter(lambda x: x, '\n'.join(valuelist).splitlines())
            ])

    def process_data(self, value):
        """Process data."""
        self.data = '\n'.join(value)


class RedirectURIValidator(object):
    """Validate if redirect URIs."""

    def __call__(self, form, field):
        """Call function."""
        errors = []
        for v in field.data.splitlines():
            try:
                validate_redirect_uri(v)
            except InsecureTransportError:
                errors.append(v)
            except InvalidRedirectURIError:
                errors.append(v)

        if errors:
            raise validators.ValidationError(
                _('Invalid redirect URIs: %(urls)s', urls=', '.join(errors))
            )


#
# Forms
#
class ClientFormBase(model_form_factory(Form)):
    """Base class for Client form."""

    class Meta:
        """Metadata class."""

        model = Client
        exclude = [
            'client_secret',
            'is_internal',
        ]
        strip_string_fields = True
        field_args = dict(
            website=dict(
                validators=[validators.DataRequired(), URLValidator()],
                widget=widgets.TextInput(),
            ),
        )


class ClientForm(ClientFormBase):
    """Client form."""

    # Trick to make redirect_uris render in the bottom of the form.
    redirect_uris = RedirectURIField(
        label=_('Redirect URIs (one per line)'),
        description=_(
            "One redirect URI per line. This is your application's"
            ' authorization callback URLs. HTTPS must be used for all '
            'hosts except localhost (for testing purposes).'),
        validators=[RedirectURIValidator(), validators.DataRequired()],
        default='',
    )

    is_confidential = fields.SelectField(
        label=_('Client type'),
        description=_(
            'Select confidential if your application is capable of keeping '
            'the issued client secret confidential (e.g. a web application), '
            'select public if your application cannot (e.g. a browser-based '
            'JavaScript application). If you select public, your application '
            'MUST validate the redirect URI.'),
        coerce=bool,
        choices=[(True, _('Confidential')), (False, _('Public'))],
        default=True,
    )


class TokenForm(Form):
    """Token form."""

    name = fields.StringField(
        description=_('Name of personal access token.'),
        validators=[
            validators.DataRequired(),
            validators.Length(
                max=40,
                message=_('The name must be less than 40 characters long.'))
        ]
    )

    scopes = fields.SelectMultipleField(
        widget=scopes_multi_checkbox,
        choices=[],  # Must be dynamically provided in view.
        description=_(
            'Scopes assign permissions to your personal access token.'
            ' A personal access token works just like a normal OAuth '
            ' access token for authentication against the API.')
    )
