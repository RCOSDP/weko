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

"""Weko Deposit Storage."""
import base64
import hashlib
import os

import cchardet as chardet
from flask import current_app
from invenio_files_rest.storage.base import StorageError
from invenio_files_rest.storage.pyfs import PyFSFileStorage

from .logger import weko_logger
from .errors import WekoDepositError, WekoDepositStorageError


class WekoFileStorage(PyFSFileStorage):
    """Weko file storage."""

    def _init_hash(self):
        """Initialize message digest object.

        Overwrite this method if you want to use different checksum
        algorithm for your storage backend.

        Returns:
            tuple: \
                A tuple containing the checksum algorithm and the \
                message digest object.
        """
        result =  hashlib.sha256()
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=('sha256', result))
        return 'sha256', result

    def upload_file(self, fjson):
        """Upload file.

        Upload a file to the storage.

        Args:
            fjson (dict): \
                The JSON object containing file information.
        Raises:
            WekoDepositError: \
                If there is an error encoding/decoding the file.
            StorageError: \
                If there is an error sending the file in invenio.

        Returns:
            None
        """
        if fjson is None or len(fjson) == 0:
            return

        try:
            fp = self.open(mode='rb')
        except EnvironmentError as ex:
            # FIXME: get the file name from the fjson if we use this method.
            weko_logger(key='WEKO_DEPOSIT_FAILED_FILE_UPLOAD',
                        file_name="", ex=ex)
            raise StorageError(description="Could not upload file") from ex
        except Exception as ex:
            weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            raise StorageError(description="Could not upload file") from ex

        mime = fjson.get('mimetype', '')
        if 'text' in mime:
            s = fp.read()
            ecd = chardet.detect(s).get('encoding')
            if ecd and 'UTF-8' not in ecd:
                try:
                    s = s.decode(ecd).encode('utf-8')
                except UnicodeError as ex:
                    # FIXME: get the file name from the fjson.
                    weko_logger(
                        key="WEKO_DEPOSIT_FAILED_ENCODING_DECODING_FILE",
                        file_name="", ex=ex)
                    raise WekoDepositError(ex=ex,
                                msg="Could not encoding/decoding file") from ex
            strb = base64.b64encode(s).decode("utf-8")
        else:
            strb = base64.b64encode(fp.read()).decode("utf-8")
        fp.close()

        # FIXME: get the file id if we use this method.
        weko_logger(key='WEKO_DEPOSIT_UPLOAD_FILE', file_id="")
        fjson.update({"file": strb})


def make_path(base_uri, path, filename, path_dimensions, split_length):
    """make path for file instance

    Generates a path for a file instance relative to a base location.
    Splits the path by split_length characters path_dimensions times
    and appends the file name.

    Args:
        base_uri (str): \
            The base URI.
        path (str): \
            The relative path.
        filename (str): \
            The filename to be appended to the URL.
        path_dimensions (int): \
            The number of widgets the path should be split into.
        split_length (int): \
            The length of each chunk.
    Returns:
        str: \
            A string representing the full path.
    Raises:
        WekoDepositError: \
            If the length of the path is not greater than \
            path_dimensions * split_length.
    """
    if len(path) <= path_dimensions * split_length:
        weko_logger(key='WEKO_DEPOSIT_FAILED_MAKE_PATH',
                    path=path, length=path_dimensions * split_length)
        raise WekoDepositError(f"Path length must be at least  \
                             {path_dimensions * split_length}.")

    uri_parts = []
    for i in range(path_dimensions):
        uri_parts.append(path[0:split_length])
        path = path[split_length:]
    uri_parts.append(path)
    uri_parts.append(filename)

    url = os.path.join(base_uri, *uri_parts)

    result = url.replace("\\", "/") if os.sys.platform == 'win32' else url
    return result


def pyfs_storage_factory(fileinstance=None, default_location=None,
                         default_storage_class=None,
                         filestorage_class=WekoFileStorage, fileurl=None,
                         size=None, modified=None, clean_dir=True):
    """Get factory function

    Get factory function for creating a PyFS file storage instance.

    Note:
        * Either fileinstance or both fileurl and size must be specified.
        * if fileinstance is specified, the file URL and size are ignored.

    Args:
        fileinstance (:obj:`FileInstance`, Optional): \
            The file instance. Defaults to `None`.<br>
        default_location (str, Optional): \
            The default location. Defaults to `None`.
        default_storage_class (`FileStorage`, Optional): \
            The default storage class. Defaults to `None`.
        filestorage_class (`FileStorage`, Optional): \
            The file storage class. Defaults to `WekoFileStorage`.
        fileurl (str, Optional): \
            The file URL. Defaults to `None`.
        size (int, Optional): \
            The size of the file. Defaults to `None`.
        modified (datetime, Optional): \
            The modified date of the file. Defaults to `None`.
        clean_dir (bool, Optional): \
            Whether to clean the directory. Defaults to `True`.

    Returns:
        filestorage_class: The file storage instance.

    Raises:
        WekoDepositError: \
            If either the file instance or the file URL and size \
                are not specified.
    """
    # Either the FileInstance needs to be specified or all filestorage
    # class parameters need to be specified
    if fileinstance is None and (fileurl is None or size is None):
        weko_logger(key='WEKO_DEPOSIT_FAILED_STORAGE_FACTORY')
        raise WekoDepositStorageError(msg="Either fileinstance or both fileurl and size must be specified.")

    if fileinstance:
        # FIXME: Code here should be refactored since it assumes a lot on the
        # directory structure where the file instances are written
        fileurl = None
        size = fileinstance.size
        modified = fileinstance.updated

        if fileinstance.uri:
            # Use already existing URL.
            fileurl = fileinstance.uri
        else:
            if default_location is None:
                weko_logger(key='WEKO_DEPOSIT_FAILED_STORAGE_FACTORY')
                raise WekoDepositStorageError("default_location was not "\
                            "specified, in spite of fileinstance.uri is None")
            # Generate a new URL.
            fileurl = make_path(
                default_location,
                str(fileinstance.id),
                'data',
                current_app.config['FILES_REST_STORAGE_PATH_DIMENSIONS'],
                current_app.config['FILES_REST_STORAGE_PATH_SPLIT_LENGTH'],
            )

    result = filestorage_class(
        fileurl, size=size, modified=modified, clean_dir=clean_dir)
    weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
    return result
