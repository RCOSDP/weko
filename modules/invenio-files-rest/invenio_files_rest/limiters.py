# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""File size limiting functionality for Invenio-Files-REST."""

from __future__ import absolute_import, print_function


def file_size_limiters(bucket):
    """Get default file size limiters.

    :param bucket: The :class:`invenio_files_rest.models.Bucket` instance.
    :returns: A list containing an instance of
        :class:`invenio_files_rest.limiters.FileSizeLimit` with quota left
        value and description and another one with max file size value and
        description.
    """
    return [
        FileSizeLimit(
            bucket.quota_left,
            'Bucket quota exceeded.',
        ),
        FileSizeLimit(
            bucket.max_file_size,
            'Maximum file size exceeded.',
        ),
    ]


class FileSizeLimit(object):
    """File size limiter."""

    not_implemented_error = NotImplementedError(
        'FileSizeLimit supports only comparisons with integers and other '
        'FileSizeLimits.')

    def __init__(self, limit, reason):
        """Instantiate a new file size limit.

        :param limit: The imposed imposed limit.
        :param reason: The limit description.
        """
        self.limit = limit
        self.reason = reason

    def __lt__(self, other):
        """Check if this limit is less than the other one."""
        if isinstance(other, int):
            return self.limit < other
        elif isinstance(other, FileSizeLimit):
            return self.limit < other.limit
        raise self.not_implemented_error

    def __gt__(self, other):
        """Check if this limit is greater than the other one."""
        if isinstance(other, int):
            return self.limit > other
        elif isinstance(other, FileSizeLimit):
            return self.limit > other.limit
        raise self.not_implemented_error

    def __eq__(self, other):
        """Check for equality."""
        if isinstance(other, int):
            return self.limit == other
        elif isinstance(other, FileSizeLimit):
            return self.limit == other.limit
        raise self.not_implemented_error
