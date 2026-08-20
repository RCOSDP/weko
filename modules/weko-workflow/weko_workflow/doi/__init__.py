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

"""DOI registration against the agencies' APIs.

WEKO grants a DOI by writing it into the metadata and the PID store; this
package is what actually registers it with Crossref, and is built so that the
other agencies plug into the same orchestration.
"""

from .base import AgencyCapabilities, DepositRequest, DepositResult, \
    DepositStatus, DoiRegistrationAgency
from .metadata import DoiMetadataSource
from .orchestrator import request_doi_deposit
from .registry import get_agency, is_supported

__all__ = (
    'AgencyCapabilities',
    'DepositRequest',
    'DepositResult',
    'DepositStatus',
    'DoiMetadataSource',
    'DoiRegistrationAgency',
    'get_agency',
    'is_supported',
    'request_doi_deposit',
)
