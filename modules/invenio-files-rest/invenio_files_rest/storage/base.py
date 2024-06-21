# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""File storage base module."""

import hashlib
from calendar import timegm
from functools import partial

from ..errors import FileSizeError, StorageError, UnexpectedFileSizeError
from ..helpers import chunk_size_or_default, compute_checksum, send_stream


def check_sizelimit(size_limit, bytes_written, total_size):
    """Check if size limit was exceeded.

    :param size_limit: The size limit.
    :param bytes_written: The total number of bytes written.
    :param total_size: The total file size.
    :raises invenio_files_rest.errors.UnexpectedFileSizeError: If the bytes
        written exceed the total size.
    :raises invenio_files_rest.errors.FileSizeError: If the bytes
        written are major than the limit size.
    """
    if size_limit is not None and bytes_written > size_limit:
        desc = (
            "File size limit exceeded."
            if isinstance(size_limit, int)
            else size_limit.reason
        )
        raise FileSizeError(description=desc)

    # Never write more than advertised
    if total_size is not None and bytes_written > total_size:
        raise UnexpectedFileSizeError(description="File is bigger than expected.")


def check_size(bytes_written, total_size):
    """Check if expected amounts of bytes have been written.

    :param bytes_written: The total number of bytes written.
    :param total_size: The total file size.
    :raises invenio_files_rest.errors.UnexpectedFileSizeError: If the bytes
        written exceed the total size.
    """
    if total_size and bytes_written < total_size:
        raise UnexpectedFileSizeError(description="File is smaller than expected.")


class FileStorage(object):
    """Base class for storage interface to a single file."""

    def __init__(self, size=None, modified=None):
        """Initialize storage object."""
        self._size = size
        self._modified = timegm(modified.timetuple()) if modified else None

    def open(self, mode=None):
        """Open the file.

        The caller is responsible for closing the file.
        """
        raise NotImplementedError

    def delete(self):
        """Delete the file."""
        raise NotImplementedError

    def initialize(self, size=0):
        """Initialize the file on the storage + truncate to the given size."""
        raise NotImplementedError

    def save(
        self,
        incoming_stream,
        size_limit=None,
        size=None,
        chunk_size=None,
        progress_callback=None,
    ):
        """Save incoming stream to file storage."""
        raise NotImplementedError

    def update(
        self,
        incoming_stream,
        seek=0,
        size=None,
        chunk_size=None,
        progress_callback=None,
    ):
        """Update part of file with incoming stream."""
        raise NotImplementedError

    #
    # Default implementation
    #
    def send_file(
        self,
        filename,
        mimetype=None,
        restricted=True,
        checksum=None,
        trusted=False,
        chunk_size=None,
        as_attachment=False,
    ):
        """Send the file to the client."""
        try:
            fp = self.open(mode="rb")
        except Exception as e:
            raise StorageError("Could not send file: {}".format(e))

        try:
            md5_checksum = None
            if checksum:
                algo, value = checksum.split(":")
                if algo == "md5":
                    md5_checksum = value

            # Send stream is responsible for closing the file.
            return send_stream(
                fp,
                filename,
                self._size,
                self._modified,
                mimetype=mimetype,
                restricted=restricted,
                etag=checksum,
                content_md5=md5_checksum,
                chunk_size=chunk_size,
                trusted=trusted,
                as_attachment=as_attachment,
            )
        except Exception as e:
            fp.close()
            raise StorageError("Could not send file: {}".format(e))

    def checksum(self, chunk_size=None, progress_callback=None, **kwargs):
        """Compute checksum of file."""
        fp = self.open(mode="rb")
        try:
            value = self._compute_checksum(
                fp,
                size=self._size,
                chunk_size=None,
                progress_callback=progress_callback,
            )
        except StorageError:
            raise
        finally:
            fp.close()
        return value

    def copy(self, src, chunk_size=None, progress_callback=None):
        """Copy data from another file instance.

        :param src: Source stream.
        :param chunk_size: Chunk size to read from source stream.
        """
        fp = src.open(mode="rb")
        try:
            return self.save(
                fp, chunk_size=chunk_size, progress_callback=progress_callback
            )
        finally:
            fp.close()

    #
    # Helpers
    #
    def _init_hash(self):
        """Initialize message digest object.

        Overwrite this method if you want to use different checksum
        algorithm for your storage backend.
        """
        return "md5", hashlib.md5()

    def _compute_checksum(
        self, stream, size=None, chunk_size=None, progress_callback=None, **kwargs
    ):
        """Get helper method to compute checksum from a stream.

        Naive implementation that can be overwritten by subclasses in order to
        provide more efficient implementation.
        """
        if progress_callback and size:
            progress_callback = partial(progress_callback, size)
        else:
            progress_callback = None

        try:
            algo, m = self._init_hash()
            return compute_checksum(
                stream,
                algo,
                m,
                chunk_size=chunk_size,
                progress_callback=progress_callback,
                **kwargs
            )
        except Exception as e:
            raise StorageError("Could not compute checksum of file: {0}".format(e))

    def _write_stream(
        self,
        src,
        dst,
        size=None,
        size_limit=None,
        chunk_size=None,
        progress_callback=None,
    ):
        """Get helper to save stream from src to dest + compute checksum.

        :param src: Source stream.
        :param dst: Destination stream.
        :param size: If provided, this exact amount of bytes will be
            written to the destination file.
        :param size_limit: ``FileSizeLimit`` instance to limit number of bytes
            to write.
        """
        chunk_size = chunk_size_or_default(chunk_size)

        algo, m = self._init_hash()
        bytes_written = 0

        while 1:
            # Check that size limits aren't bypassed
            check_sizelimit(size_limit, bytes_written, size)

            chunk = src.read(chunk_size)

            if not chunk:
                if progress_callback:
                    progress_callback(bytes_written, bytes_written)
                break

            dst.write(chunk)

            bytes_written += len(chunk)

            if m:
                m.update(chunk)

            if progress_callback:
                progress_callback(None, bytes_written)

        check_size(bytes_written, size)

        return bytes_written, "{0}:{1}".format(algo, m.hexdigest()) if m else None
