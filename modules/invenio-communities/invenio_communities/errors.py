# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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
