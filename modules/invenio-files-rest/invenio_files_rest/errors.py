# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Errors for Invenio-Files-REST."""

from __future__ import absolute_import, print_function

from invenio_rest.errors import RESTException


class FilesException(RESTException):
    """Base exception for all errors ."""

    code = 500


class StorageError(FilesException):
    """Exception raised when a storage operation fails."""


class UnexpectedFileSizeError(StorageError):
    """Exception raised when a file does not match its expected size."""

    code = 400
    description = "Content-Length does not match file size."


class InvalidOperationError(FilesException):
    """Exception raised when an invalid operation is performed."""

    code = 403


class MissingQueryParameter(FilesException):
    """Exception raised when missing a query parameter."""

    code = 400
    description = "Missing required query argument '{arg_name}'"

    def __init__(self, arg_name, **kwargs):
        """Initialize RESTException."""
        self.arg_name = arg_name
        super(MissingQueryParameter, self).__init__(**kwargs)

    def get_description(self, environ=None):
        """Get the description."""
        return self.description.format(arg_name=self.arg_name)


class FileInstanceAlreadySetError(InvalidOperationError):
    """Exception raised when file instance already set on object."""


class FileInstanceUnreadableError(InvalidOperationError):
    """Exception raised when trying to get an unreadable file."""

    code = 503
    description = "File storage is offline."


class BucketLockedError(InvalidOperationError):
    """Exception raised when a bucket is locked."""

    code = 403
    description = "Bucket is locked for modifications."


class InvalidKeyError(InvalidOperationError):
    """Invalid key."""

    code = 400
    description = "Filename is too long."


class FileSizeError(StorageError):
    """Exception raised when a file larger than allowed."""

    code = 400


class MultipartException(FilesException):
    """Exception for multipart objects."""


class MultipartAlreadyCompleted(MultipartException):
    """Exception raised when multipart object is already completed."""

    code = 403
    description = "Multipart upload is already completed."


class MultipartNotCompleted(MultipartException):
    """Exception raised when multipart object is not already completed."""

    code = 400
    description = "Multipart upload is already completed."


class MultipartInvalidChunkSize(MultipartException):
    """Exception raised when multipart object is already completed."""

    code = 400
    description = "Invalid part size."


class MultipartInvalidPartNumber(MultipartException):
    """Exception raised when multipart object is already completed."""

    code = 400
    description = "Invalid part number."


class MultipartInvalidSize(MultipartException):
    """Exception raised when multipart object is already completed."""

    code = 400
    description = "Invalid file size."


class MultipartMissingParts(MultipartException):
    """Exception raised when multipart object is already completed."""

    code = 400
    description = "Not all parts have been uploaded."


class MultipartNoPart(MultipartException):
    """Exception raised by part factories when no part was detected."""

    code = 400
    description = "No upload part detected in request."
