# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""OAI harvest config."""

from __future__ import absolute_import, print_function

OAIHARVESTER_DEFAULT_NAMESPACE_MAP = {
    "OAI-PMH": "http://www.openarchives.org/OAI/2.0/",
}
"""The default namespace used when handling OAI-PMH results."""

OAIHARVESTER_WORKDIR = None
"""Path to directory for oaiharvester related files, default: instance_path."""

OAIHARVESTER_UPDATE_STYLE_OPTIONS = {
    '0': 'Bulk',
    '1': 'Difference',
}
OAIHARVESTER_DEFAULT_UPDATE_STYLE = '0'
"""Default update style option."""

OAIHARVESTER_AUTO_DISTRIBUTION_OPTIONS = {
    '1': 'Run',
    '0': 'Do not run',
}
OAIHARVESTER_DEFAULT_AUTO_DISTRIBUTION = '0'
"""Default auto distribution option."""

OAIHARVESTER_NUMBER_OF_HISTORIES = 20
"""Default display number of histories."""
