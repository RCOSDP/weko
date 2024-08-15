# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""File reader utility."""

from os.path import basename, splitext

from flask import url_for


class PreviewFile(object):
    """Preview file default implementation."""

    def __init__(self, pid, record, fileobj):
        """Initialize object.

        :param file: ObjectVersion instance from Invenio-Files-REST.
        """
        self.file = fileobj
        self.pid = pid
        self.record = record

    @property
    def size(self):
        """Get file size."""
        return self.file["size"]

    @property
    def filename(self):
        """Get filename."""
        return basename(self.file.key)

    @property
    def bucket(self):
        """Get bucket."""
        return self.file.bucket_id

    @property
    def uri(self):
        """Get file download link.

        ..  note::

            The URI generation assumes that you can download the file using the
            view ``invenio_records_ui.<pid_type>_files``.
        """
        return url_for(
            ".{0}_files".format(self.pid.pid_type),
            pid_value=self.pid.pid_value,
            filename=self.file.key,
        )

    def is_local(self):
        """Check if file is local."""
        return True

    def has_extensions(self, *exts):
        """Check if file has one of the extensions."""
        file_ext = splitext(self.filename)[1].lower()
        return file_ext in exts

    def open(self):
        """Open the file."""
        return self.file.file.storage().open()
