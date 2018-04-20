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
import os, base64, hashlib
import cchardet as chardet

from flask import current_app
from invenio_files_rest.storage.pyfs import PyFSFileStorage
from invenio_files_rest.storage.base import StorageError


class WekoFileStorage(PyFSFileStorage):
    """"""
    def _init_hash(self):
        """Initialize message digest object.

        Overwrite this method if you want to use different checksum
        algorithm for your storage backend.
        """
        return 'sha256', hashlib.sha256()

    def upload_file(self, fjson):
        """"""
        if fjson is None or len(fjson) == 0:
            return

        try:
            fp = self.open(mode='rb')
        except Exception as e:
            raise StorageError('Could not send file: {}'.format(e))

        mime = fjson.get('mimetype', '')
        if 'text' in mime:
            s = fp.read()
            ecd = chardet.detect(s).get('encoding')
            if ecd and 'UTF-8' not in ecd:
                try:
                    s = s.decode(ecd).encode('utf-8')
                except:
                    pass
            strb = base64.b64encode(s).decode("utf-8")
        else:
            strb = base64.b64encode(fp.read()).decode("utf-8")
        fp.close()

        fjson.update({"file": strb})


def make_path(base_uri, path, filename, path_dimensions, split_length):
    """Generate a path as base location for file instance.

    :param base_uri: The base URI.
    :param path: The relative path.
    :param path_dimensions: Number of chunks the path should be split into.
    :param split_length: The length of any chunk.
    :returns: A string representing the full path.
    """
    assert len(path) > path_dimensions * split_length

    uri_parts = []
    for i in range(path_dimensions):
        uri_parts.append(path[0:split_length])
        path = path[split_length:]
    uri_parts.append(path)
    uri_parts.append(filename)

    url = os.path.join(base_uri, *uri_parts)
    return url.replace("\\", "/") if os.sys.platform == 'win32' else url


def pyfs_storage_factory(fileinstance=None, default_location=None,
                         default_storage_class=None,
                         filestorage_class=WekoFileStorage, fileurl=None,
                         size=None, modified=None, clean_dir=True):
    """Get factory function for creating a PyFS file storage instance."""
    # Either the FileInstance needs to be specified or all filestorage
    # class parameters need to be specified
    assert fileinstance or (fileurl and size)

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
            assert default_location
            # Generate a new URL.
            fileurl = make_path(
                default_location,
                str(fileinstance.id),
                'data',
                current_app.config['FILES_REST_STORAGE_PATH_DIMENSIONS'],
                current_app.config['FILES_REST_STORAGE_PATH_SPLIT_LENGTH'],
            )

    return filestorage_class(
        fileurl, size=size, modified=modified, clean_dir=clean_dir)
