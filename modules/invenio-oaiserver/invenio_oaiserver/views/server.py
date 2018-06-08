# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAI-PMH 2.0 server."""

from __future__ import absolute_import

from flask import Blueprint, make_response
from invenio_pidstore.errors import PIDDoesNotExistError
from itsdangerous import BadSignature
from lxml import etree
from marshmallow.exceptions import ValidationError
from webargs.flaskparser import use_args

from .. import response as xml
from ..verbs import make_request_validator

blueprint = Blueprint(
    'invenio_oaiserver',
    __name__,
    static_folder='../static',
    template_folder='../templates',
)


@blueprint.errorhandler(ValidationError)
@blueprint.errorhandler(422)
def validation_error(exception):
    """Return formatter validation error."""
    messages = getattr(exception, 'messages', None)
    if messages is None:
        messages = getattr(exception, 'data', {'messages': None})['messages']

    def extract_errors():
        """Extract errors from exception."""
        if isinstance(messages, dict):
            for field, message in messages.items():
                if field == 'verb':
                    yield 'badVerb', '\n'.join(message)
                else:
                    yield 'badArgument', '\n'.join(message)
        else:
            for field in exception.field_names:
                if field == 'verb':
                    yield 'badVerb', '\n'.join(messages)
                else:
                    yield 'badArgument', '\n'.join(messages)

            if not exception.field_names:
                yield 'badArgument', '\n'.join(messages)

    return (etree.tostring(xml.error(extract_errors())),
            422,
            {'Content-Type': 'text/xml'})


@blueprint.errorhandler(PIDDoesNotExistError)
def pid_error(exception):
    """Handle PID Exceptions."""
    return (etree.tostring(xml.error([('idDoesNotExist',
                                       'No matching identifier')])),
            422,
            {'Content-Type': 'text/xml'})


@blueprint.errorhandler(BadSignature)
def resumptiontoken_error(exception):
    """Handle resumption token exceptions."""
    return (etree.tostring(xml.error([(
        'badResumptionToken',
        'The value of the resumptionToken argument is invalid or expired.')
    ])), 422, {'Content-Type': 'text/xml'})


@blueprint.route('/oai2d', methods=['GET', 'POST'])
@use_args(make_request_validator)
def response(args):
    """Response endpoint."""
    e_tree = getattr(xml, args['verb'].lower())(**args)

    response = make_response(etree.tostring(
        e_tree,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8',
    ))
    response.headers['Content-Type'] = 'text/xml'
    return response
