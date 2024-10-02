# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier fetchers."""

from __future__ import absolute_import

from invenio_pidstore.fetchers import FetchedPID

from .providers import DepositProvider


def deposit_fetcher(record_uuid, data):
    """Fetch a deposit identifier.

    :param record_uuid: Record UUID.
    :param data: Record content.
    :returns: A :class:`invenio_pidstore.fetchers.FetchedPID` that contains
        data['_deposit']['id'] as pid_value.
    """
    return FetchedPID(
        provider=DepositProvider,
        pid_type=DepositProvider.pid_type,
        pid_value=str(data['_deposit']['id']),
    )
