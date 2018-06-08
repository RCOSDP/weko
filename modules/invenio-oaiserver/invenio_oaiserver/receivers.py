# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record field function."""

from __future__ import absolute_import, print_function

from time import sleep

from .percolator import _delete_percolator, _new_percolator, get_record_sets
from .tasks import update_affected_records


class OAIServerUpdater(object):
    """Return the right update oaisets function."""

    def __call__(self, sender, record, **kwargs):
        """Update sets list.

        :param record: The record data.
        """
        if '_oai' in record and 'id' in record['_oai']:
            new_sets = set(get_record_sets(record=record))
            # Update only if old and new sets differ
            if set(record['_oai'].get('sets', [])) != new_sets:
                record['_oai'].update({
                    'sets': list(new_sets)
                })


def after_insert_oai_set(mapper, connection, target):
    """Update records on OAISet insertion."""
    _new_percolator(spec=target.spec, search_pattern=target.search_pattern)
    sleep(2)
    update_affected_records.delay(
        search_pattern=target.search_pattern
    )


def after_update_oai_set(mapper, connection, target):
    """Update records on OAISet update."""
    _delete_percolator(spec=target.spec, search_pattern=target.search_pattern)
    _new_percolator(spec=target.spec, search_pattern=target.search_pattern)
    sleep(2)
    update_affected_records.delay(
        spec=target.spec, search_pattern=target.search_pattern
    )


def after_delete_oai_set(mapper, connection, target):
    """Update records on OAISet deletion."""
    _delete_percolator(spec=target.spec, search_pattern=target.search_pattern)
    sleep(2)
    update_affected_records.delay(
        spec=target.spec
    )
