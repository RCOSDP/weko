# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Indexer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Indexer registry."""


class IndexerRegistry:
    """A simple class to register indexers."""

    def __init__(self):
        """Initialize the registry."""
        self._indexers = {}

    def register(self, indexer_instance, indexer_id):
        """Register a new indexer instance."""
        if indexer_id in self._indexers:
            raise RuntimeError(
                f"Indexer with indexer id '{indexer_id}' " "is already registered."
            )
        self._indexers[indexer_id] = indexer_instance

    def get(self, indexer_id):
        """Get an indexer for a given indexer_id."""
        return self._indexers[indexer_id]

    def get_indexer_id(self, instance):
        """Get the indexer id for a specific instance."""
        for indexer_id, indexer_instance in self._indexers.items():
            if instance == indexer_instance:
                return indexer_id
        raise KeyError("Indexer not found in registry.")

    def all(self):
        """Get all the registered indexers."""
        return self._indexers
