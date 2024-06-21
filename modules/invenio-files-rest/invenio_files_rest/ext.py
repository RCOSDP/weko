# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Files download/upload REST API similar to S3 for Invenio."""

from flask import abort
from werkzeug.exceptions import UnprocessableEntity
from werkzeug.utils import cached_property

from . import config
from .cli import files as files_cmd
from .errors import MultipartNoPart
from .utils import load_or_import_from_config, obj_or_import_string


class _FilesRESTState(object):
    """Invenio Files REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app

    @cached_property
    def storage_factory(self):
        """Load default storage factory."""
        return load_or_import_from_config("FILES_REST_STORAGE_FACTORY", app=self.app)

    @cached_property
    def permission_factory(self):
        """Load default permission factory for Buckets collections."""
        return load_or_import_from_config("FILES_REST_PERMISSION_FACTORY", app=self.app)

    @cached_property
    def file_size_limiters(self):
        r"""Load the file size limiter.

        The file size limiter is a function used to get the file size limiters.
        This function can use anything to limit the file size, for example:
        bucket quota, user quota, custom limit.
        Its prototype is:

            py::function: limiter(bucket=None\
                ) -> [FileSizeLimit, FileSizeLimit, ...]

        An empty list should be returned if there should be no limit. The
        lowest limit will be used.
        """
        return load_or_import_from_config("FILES_REST_SIZE_LIMITERS", app=self.app)

    @cached_property
    def part_factories(self):
        """Get factory for list of webargs schemas for parsing part number."""
        return [
            obj_or_import_string(x)
            for x in self.app.config.get("FILES_REST_MULTIPART_PART_FACTORIES", [])
        ]

    @cached_property
    def upload_factories(self):
        """Get factory for list of webargs schemas for parsing part number."""
        return [
            obj_or_import_string(x)
            for x in self.app.config.get("FILES_REST_UPLOAD_FACTORIES", [])
        ]

    def multipart_partfactory(self):
        """Get factory for content length, part number, stream for a part."""
        for factory in self.part_factories:
            try:
                return factory()
            except (MultipartNoPart, UnprocessableEntity):
                pass
        raise MultipartNoPart()

    def upload_factory(self):
        """Get factory to get stream, content length, checksum for a file."""
        for factory in self.upload_factories:
            try:
                return factory()
            except UnprocessableEntity:
                pass
        abort(400)


class InvenioFilesREST(object):
    """Invenio-Files-REST extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        if hasattr(app, "cli"):
            app.cli.add_command(files_cmd)
        app.extensions["invenio-files-rest"] = _FilesRESTState(app)

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("FILES_REST_"):
                app.config.setdefault(k, getattr(config, k))
