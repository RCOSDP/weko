# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier minters."""

from flask import current_app
from invenio_pidstore import current_pidstore

from .provider import OAIIDProvider


def oaiid_minter(record_uuid, data):
    """Mint record identifiers.

    :param record_uuid: The record UUID.
    :param data: The record data.
    :returns: A :class:`invenio_pidstore.models.PersistentIdentifier` instance.
    """
    pid_value = data.get("_oai", {}).get("id")
    if pid_value is None:
        fetcher_name = current_app.config.get(
            "OAISERVER_CONTROL_NUMBER_FETCHER", "recid"
        )
        cn_pid = current_pidstore.fetchers[fetcher_name](record_uuid, data)
        pid_value = current_app.config.get("OAISERVER_ID_PREFIX", "") + str(
            cn_pid.pid_value
        )
    provider = OAIIDProvider.create(
        object_type="rec", object_uuid=record_uuid, pid_value=str(pid_value)
    )
    data.setdefault("_oai", {})
    data["_oai"]["id"] = provider.pid.pid_value
    return provider.pid
