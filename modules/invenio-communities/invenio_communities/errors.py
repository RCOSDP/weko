# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Errors for persistent identifiers."""

from __future__ import absolute_import, print_function


class CommunitiesError(Exception):
    """Base class for errors that deal with a community."""

    def __init__(self, community, *args, **kwargs):
        """Store community information."""
        super(CommunitiesError, self).__init__(*args, **kwargs)
        self.community = community


class CommunityRecordError(CommunitiesError):
    """Base class for errors that deal with a community and a record."""

    def __init__(self, community, record, *args, **kwargs):
        """Store community and record information."""
        super(CommunityRecordError, self).__init__(community, *args, **kwargs)
        self.record = record


class InclusionRequestMissingError(CommunityRecordError):
    """InclusionRequest missing for given community and record."""


class InclusionRequestExistsError(CommunityRecordError):
    """InclusionRequest already exists for given community and record."""


class InclusionRequestObsoleteError(CommunityRecordError):
    """Record already belongs to a community."""


class InclusionRequestExpiryTimeError(CommunityRecordError):
    """Incorrect expiry time for inclusion request."""
