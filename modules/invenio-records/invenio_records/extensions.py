# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2021 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Extensions allow integration of features into a record class.

For instance, the system fields feature is built as an extension.
"""


class ExtensionMixin:
    """Defines the methods needed by an extension."""

    def pre_init(self, record, data, model=None, **kwargs):
        """Called when a new record instance is initialized.

        Called when a new record is instantiated (i.e. during all
        ``Record({...})``). This means it's also called when e.g. a record
        is created via ``Record.create()``.

        :param data: The dict passed to the record's constructor.
        :param model: The model class used for initialization.
        """

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized."""

    def pre_dump(self, record, data, dumper=None):
        """Called before a record is dumped."""

    def post_dump(self, record, data, dumper=None):
        """Called after a record is dumped."""

    def pre_load(self, data, loader=None):
        """Called before a record is loaded."""

    def post_load(self, record, data, loader=None):
        """Called after a record is loaded."""

    def pre_create(self, record):
        """Called before a record is created."""

    def post_create(self, record):
        """Called after a record is created."""

    def pre_commit(self, record):
        """Called before a record is committed."""

    def post_commit(self, record):
        """Called after a record is committed."""

    def pre_delete(self, record, force=False):
        """Called before a record is deleted."""

    def post_delete(self, record, force=False):
        """Called after a record is deleted."""

    def pre_revert(self, record, revision):
        """Called before a record is reverted."""

    def post_revert(self, new_record, revision):
        """Called after a record is reverted."""


class RecordExtension(ExtensionMixin):
    """Base class for a record extensions."""


class RecordMeta(type):
    """Metaclass responsible for initializing the extension registry."""

    def __new__(mcs, name, bases, attrs):
        """Create a new record class."""
        # Initialise an "_extensions" attribute on each class, to ensure each
        # class have a separate extensions registry.
        if "_extensions" not in attrs:
            attrs["_extensions"] = []

        # Construct the class.
        return super().__new__(mcs, name, bases, attrs)
