# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAI-PMH verbs."""

from __future__ import absolute_import

from flask import current_app, request
from marshmallow import Schema, ValidationError, fields, utils, \
    validates_schema
from marshmallow.fields import DateTime as _DateTime

from .resumption_token import ResumptionTokenSchema


def validate_metadata_prefix(value):
    """Check metadataPrefix.

    :param value: One of the metadata identifiers configured in
        ``OAISERVER_METADATA_FORMATS``.
    """
    metadataFormats = current_app.config['OAISERVER_METADATA_FORMATS']
    if value not in metadataFormats:
        raise ValidationError('metadataPrefix does not exist',
                              field_names=['metadataPrefix'])


class DateTime(_DateTime):
    """DateTime with a permissive deserializer."""

    def from_iso_permissive(datestring, use_dateutil=True):
        """Parse an ISO8601-formatted datetime and return a datetime object.

        Inspired by the marshmallow.utils.from_iso function, but also accepts
        datestrings that don't contain the time.
        """
        dateutil_available = False
        try:
            from dateutil import parser
            dateutil_available = True
        except ImportError:
            dateutil_available = False
            import datetime

        # Use dateutil's parser if possible
        if dateutil_available and use_dateutil:
            return parser.parse(datestring)
        else:
            # Strip off timezone info.
            return datetime.datetime.strptime(datestring[:19],
                                              '%Y-%m-%dT%H:%M:%S')

    DATEFORMAT_DESERIALIZATION_FUNCS = dict(
        _DateTime.DATEFORMAT_DESERIALIZATION_FUNCS,
        permissive=from_iso_permissive
    )


class OAISchema(Schema):
    """Base OAI argument schema."""

    verb = fields.Str(required=True, load_only=True)

    class Meta:
        """Schema configuration."""

        strict = True

    @validates_schema
    def validate(self, data):
        """Check range between dates under keys ``from_`` and ``until``."""
        if 'verb' in data and data['verb'] != self.__class__.__name__:
            raise ValidationError(
                # FIXME encode data
                'This is not a valid OAI-PMH verb:{0}'.format(data['verb']),
                field_names=['verb'],
            )

        if 'from_' in data and 'until' in data and \
                data['from_'] > data['until']:
            raise ValidationError('Date "from" must be before "until".')

        extra = set(request.values.keys()) - set([
            f.load_from or f.name for f in self.fields.values()
        ])
        if extra:
            raise ValidationError('You have passed too many arguments.')


class Verbs(object):
    """List valid verbs and its arguments."""

    class GetRecord(OAISchema):
        """Arguments for GetRecord verb."""

        identifier = fields.Str(required=True)
        metadataPrefix = fields.Str(required=True,
                                    validate=validate_metadata_prefix)

    class GetMetadata(OAISchema):
        """Arguments for GetMetadata verb."""

        identifier = fields.Str(required=True)
        metadataPrefix = fields.Str(required=True,
                                    validate=validate_metadata_prefix)

    class Identify(OAISchema):
        """Arguments for Identify verb."""

    class ListIdentifiers(OAISchema):
        """Arguments for ListIdentifiers verb."""

        from_ = DateTime(format='permissive', load_from='from', dump_to='from')
        until = DateTime(format='permissive')
        set = fields.Str()
        metadataPrefix = fields.Str(required=True,
                                    validate=validate_metadata_prefix)

    class ListMetadataFormats(OAISchema):
        """Arguments for ListMetadataFormats verb."""

        identifier = fields.Str()

    class ListRecords(ListIdentifiers):
        """Arguments for ListRecords verb."""

    class ListSets(OAISchema):
        """Arguments for ListSets verb."""


class ResumptionVerbs(Verbs):
    """List valid verbs when resumption token is defined."""

    class ListIdentifiers(OAISchema, ResumptionTokenSchema):
        """Arguments for ListIdentifiers verb."""

    class ListRecords(OAISchema, ResumptionTokenSchema):
        """Arguments for ListRecords verb."""

        metadataPrefix = fields.Str(load_only=True,
                                    validate=validate_metadata_prefix)

    class ListSets(OAISchema, ResumptionTokenSchema):
        """Arguments for ListSets verb."""


def make_request_validator(request):
    """Validate arguments in incomming request."""
    verb = request.values.get('verb', '', type=str)
    resumption_token = request.values.get('resumptionToken', None)

    schema = Verbs if resumption_token is None else ResumptionVerbs
    return getattr(schema, verb, OAISchema)(partial=False)
