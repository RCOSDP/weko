# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""File size limiting functionality for Invenio-Files-REST."""


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
            "Bucket quota exceeded.",
        ),
        FileSizeLimit(
            bucket.max_file_size,
            "Maximum file size exceeded.",
        ),
    ]


class FileSizeLimit(object):
    """File size limiter."""

    not_implemented_error = NotImplementedError(
        "FileSizeLimit supports only comparisons with integers and other "
        "FileSizeLimits."
    )

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
