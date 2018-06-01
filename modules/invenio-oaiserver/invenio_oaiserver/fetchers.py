# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier fetchers."""

from __future__ import absolute_import, print_function

from invenio_pidstore.errors import PersistentIdentifierError
from invenio_pidstore.fetchers import FetchedPID

from .provider import OAIIDProvider


def oaiid_fetcher(record_uuid, data):
    """Fetch a record's identifier.

    :param record_uuid: The record UUID.
    :param data: The record data.
    :returns: A :class:`invenio_pidstore.fetchers.FetchedPID` instance.
    """
    pid_value = data.get('_oai', {}).get('id')
    if pid_value is None:
        raise PersistentIdentifierError()
    return FetchedPID(
        provider=OAIIDProvider,
        pid_type=OAIIDProvider.pid_type,
        pid_value=str(pid_value),
    )
