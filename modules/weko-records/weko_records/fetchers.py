# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""PID Fetchers."""

from __future__ import absolute_import, print_function

from invenio_pidstore.fetchers import FetchedPID


def weko_record_fetcher(dummy_record_uuid, data):
    """Fetch a record's identifiers."""
    return FetchedPID(
        provider=None,
        pid_type='recid',
        pid_value=str(data['recid']),
    )


def weko_doi_fetcher(dummy_record_uuid, data):
    """Fetch a record's DOI."""
    return FetchedPID(
        provider=None,
        pid_type='doi',
        pid_value=str(data['doi']),
    )
