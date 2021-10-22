# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Models for storing information about OAIServer state."""

from datetime import datetime

import sqlalchemy as sa
from flask_babelex import lazy_gettext as _
from invenio_db import db
from sqlalchemy.event import listen
from sqlalchemy.orm import validates
from sqlalchemy_utils import Timestamp

from .errors import OAISetSpecUpdateError
from .proxies import current_oaiserver
from .utils import datetime_to_datestamp


class OAISet(db.Model, Timestamp):
    """Information about OAI set."""

    __tablename__ = 'oaiserver_set'

    id = db.Column(db.BigInteger, primary_key=True)

    spec = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        info=dict(
            label=_('Identifier'),
            description=_('Identifier of the set.'),
        ),
    )
    """Set identifier."""

    name = db.Column(
        db.String(255),
        info=dict(
            label=_('Long name'),
            description=_('Long name of the set.'),
        ),
        index=True,
    )
    """Human readable name of the set."""

    description = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_('Description'),
            description=_('Description of the set.'),
        ),
    )
    """Human readable description."""

    search_pattern = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_('Search pattern'),
            description=_('Search pattern to select records'),
        )
    )
    """Search pattern to get records."""

    # @validates('spec')
    # def validate_spec(self, key, value):
    #    """Forbit updates of set identifier."""
    #    if self.spec and self.spec != value:
    #        raise OAISetSpecUpdateError("Updating spec is not allowed.")
    #    return value

    def add_record(self, record):
        """Add a record to the OAISet.

        :param record: Record to be added.
        :type record: `invenio_records.api.Record` or derivative.
        """
        record.setdefault('_oai', {}).setdefault('sets', [])

        assert not self.has_record(record)

        record['_oai']['sets'].append(self.spec)

    def remove_record(self, record):
        """Remove a record from the OAISet.

        :param record: Record to be removed.
        :type record: `invenio_records.api.Record` or derivative.
        """
        assert self.has_record(record)

        record['_oai']['sets'] = [
            s for s in record['_oai']['sets'] if s != self.spec]

    def has_record(self, record):
        """Check if the record blongs to the OAISet.

        :param record: Record to be checked.
        :type record: `invenio_records.api.Record` or derivative.
        """
        return self.spec in record.get('_oai', {}).get('sets', [])

    @classmethod
    def get_set_by_spec(cls, spec):
        """Get OAISet object by spec info."""
        return cls.query.filter_by(spec=spec).one_or_none()


def oaiset_removed_or_inserted(mapper, connection, target):
    """Invalidate cache on collection insert or delete."""
    current_oaiserver.sets = None


def oaiset_attribute_changed(target, value, oldvalue, initiator):
    """Invalidate cache if dbquery change."""
    if value != oldvalue:
        current_oaiserver.sets = None


# update cache with list of collections
listen(OAISet, 'after_insert', oaiset_removed_or_inserted)
listen(OAISet, 'after_delete', oaiset_removed_or_inserted)
listen(OAISet.search_pattern, 'set', oaiset_attribute_changed)

__all__ = ('OAISet', )

# OAI-PMH


class Identify(db.Model, Timestamp):
    """Information about OAI set."""

    __tablename__ = 'oaiserver_identify'

    id = db.Column(db.Integer, primary_key=True)

    outPutSetting = db.Column(
        db.Boolean(name='outPutSetting'),
        nullable=False,
        unique=True,
        info=dict(
            label=_('OutPut Setting'),
            description=_('output setting of OAI-PMH'),
        ),
    )
    """Set output of OAI-PMH."""

    emails = db.Column(
        db.String(255),
        info=dict(
            label=_('Emails'),
            description=_('Emails of OAI-PMH.'),
        ),
        index=True,
    )
    """Set Emails of OAI-PMH."""

    repositoryName = db.Column(
        db.String(255),
        nullable=True,
        info=dict(
            label=_('Repository Name'),
            description=_('Repository Name of OAI-PMH'),
        ),
    )
    """Set Repository Name of OAI-PMH."""

    earliestDatastamp = db.Column(
        sa.DateTime,
        nullable=True,
        default=datetime.utcnow,
        info=dict(
            label=_('Earliest Data'),
            description=_('The earliest data of OAI-PMH'),
        )
    )

    """The earliest data of OAI-PMH."""


__all__ = ('Identify', )
