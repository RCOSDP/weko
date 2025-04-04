# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2019, 2020 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""S3 file storage interface."""
from __future__ import absolute_import, division, print_function

from functools import partial, wraps

import s3fs
from flask import current_app
from invenio_files_rest.errors import StorageError
from invenio_files_rest.storage import PyFSFileStorage, pyfs_storage_factory

from .helpers import redirect_stream


def set_blocksize(f):
    """Decorator to set the correct block size according to file size."""
    @wraps(f)
    def inner(self, *args, **kwargs):
        size = kwargs.get('size', None)
        block_size = (
            size // current_app.config['S3_MAXIMUM_NUMBER_OF_PARTS']  # Integer
            if size
            else current_app.config['S3_DEFAULT_BLOCK_SIZE']
        )

        if block_size > self.block_size:
            self.block_size = block_size
        return f(self, *args, **kwargs)

    return inner


class S3FSFileStorage(PyFSFileStorage):
    """File system storage using Amazon S3 API for accessing files."""

    def __init__(self, fileurl, **kwargs):
        """Storage initialization."""
        self.block_size = current_app.config['S3_DEFAULT_BLOCK_SIZE']
        super(S3FSFileStorage, self).__init__(fileurl, **kwargs)

    def _get_fs(self, *args, **kwargs):
        """Get PyFilesystem instance and S3 real path."""
        if not self.fileurl.startswith('s3://'):
            return super(S3FSFileStorage, self)._get_fs(*args, **kwargs)

        info = current_app.extensions['invenio-s3'].init_s3fs_info
        fs = s3fs.S3FileSystem(default_block_size=self.block_size, **info)

        return (fs, self.fileurl)

    @set_blocksize
    def initialize(self, size=0):
        """Initialize file on storage and truncate to given size."""
        fs, path = self._get_fs()

        if fs.exists(path):
            fp = fs.rm(path)
        fp = fs.open(path, mode='wb')

        try:
            to_write = size
            fs_chunk_size = fp.blocksize  # Force write every time
            while to_write > 0:
                current_chunk_size = (
                    to_write if to_write <= fs_chunk_size else fs_chunk_size
                )
                fp.write(b'\0' * current_chunk_size)
                to_write -= current_chunk_size
        except Exception:
            fp.close()
            self.delete()
            raise
        finally:
            fp.close()

        self._size = size

        return self.fileurl, size, None

    def delete(self):
        """Delete a file."""
        fs, path = self._get_fs()
        if fs.exists(path):
            fs.rm(path)
        return True

    @set_blocksize
    def update(
        self,
        incoming_stream,
        seek=0,
        size=None,
        chunk_size=None,
        progress_callback=None,
    ):
        """Update a file in the file system."""
        old_fp = self.open(mode='rb')
        updated_fp = S3FSFileStorage(self.fileurl, size=self._size).open(
            mode='wb'
        )
        try:
            if seek >= 0:
                to_write = seek
                fs_chunk_size = updated_fp.blocksize
                while to_write > 0:
                    current_chunk_size = (
                        to_write
                        if to_write <= fs_chunk_size
                        else fs_chunk_size
                    )
                    updated_fp.write(old_fp.read(current_chunk_size))
                    to_write -= current_chunk_size

            bytes_written, checksum = self._write_stream(
                incoming_stream,
                updated_fp,
                chunk_size=chunk_size,
                size=size,
                progress_callback=progress_callback,
            )

            if (bytes_written + seek) < self._size:
                old_fp.seek((bytes_written + seek))
                to_write = self._size - (bytes_written + seek)
                fs_chunk_size = updated_fp.blocksize
                while to_write > 0:
                    current_chunk_size = (
                        to_write
                        if to_write <= fs_chunk_size
                        else fs_chunk_size
                    )
                    updated_fp.write(old_fp.read(current_chunk_size))
                    to_write -= current_chunk_size
        finally:
            old_fp.close()
            updated_fp.close()

        return bytes_written, checksum

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
            fs, path = self._get_fs()
            s3_url_builder = partial(
                fs.url, path, expires=current_app.config['S3_URL_EXPIRATION']
            )

            return redirect_stream(
                s3_url_builder,
                filename,
                mimetype=mimetype,
                restricted=restricted,
                trusted=trusted,
                as_attachment=as_attachment,
            )
        except Exception as e:
            raise StorageError('Could not send file: {}'.format(e))

    @set_blocksize
    def copy(self, src, *args, **kwargs):
        """Copy data from another file instance.

        If the source is an S3 stored object the copy process happens on the S3
        server side, otherwise we use the normal ``FileStorage`` copy method.
        """
        if src.fileurl.startswith('s3://'):
            fs, path = self._get_fs()
            fs.copy(src.fileurl, path)
        else:
            super(S3FSFileStorage, self).copy(src, *args, **kwargs)

    @set_blocksize
    def save(self, *args, **kwargs):
        """Save incoming stream to storage.

        Just overwrite parent method to allow set the correct block size.
        """
        return super(S3FSFileStorage, self).save(*args, **kwargs)


def s3fs_storage_factory(**kwargs):
    """File storage factory for S3."""
    return pyfs_storage_factory(filestorage_class=S3FSFileStorage, **kwargs)
