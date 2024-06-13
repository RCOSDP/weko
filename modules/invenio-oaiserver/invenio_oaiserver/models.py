# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Models for storing information about OAIServer state."""

from invenio_db import db
from invenio_i18n import lazy_gettext as _
from sqlalchemy.orm import validates
from sqlalchemy_utils import Timestamp

from .errors import OAISetSpecUpdateError


class OAISet(db.Model, Timestamp):
    """Information about OAI set."""

    __tablename__ = "oaiserver_set"

    id = db.Column(db.Integer, primary_key=True)

    spec = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        info=dict(
            label=_("Identifier"),
            description=_("Identifier of the set."),
        ),
    )
    """Set identifier."""

    name = db.Column(
        db.String(255),
        info=dict(
            label=_("Long name"),
            description=_("Long name of the set."),
        ),
        index=True,
    )
    """Human readable name of the set."""

    description = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_("Description"),
            description=_("Description of the set."),
        ),
    )
    """Human readable description."""

    search_pattern = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_("Search pattern"),
            description=_("Search pattern to select records"),
        ),
    )
    """Search pattern to get records."""

    system_created = db.Column(
        db.Boolean,
        nullable=False,
        info=dict(
            label=_("System created"),
            description=_("System created set"),
        ),
    )
    """System created field."""

    @validates("spec")
    def validate_spec(self, key, value):
        """Forbit updates of set identifier."""
        if self.spec and self.spec != value:
            raise OAISetSpecUpdateError("Updating spec is not allowed.")
        return value


__all__ = ("OAISet",)
