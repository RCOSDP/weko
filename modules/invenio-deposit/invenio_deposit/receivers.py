# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Deposit listeners."""

from __future__ import absolute_import, print_function

from invenio_indexer.tasks import index_record


def index_deposit_after_publish(sender, action=None, pid=None, deposit=None):
    """Index the record after publishing.

    .. note:: if the record is not published, it doesn't index.

    :param sender: Who send the signal.
    :param action: Action executed by the sender. (Default: ``None``)
    :param pid: PID object. (Default: ``None``)
    :param deposit: Deposit object. (Default: ``None``)
    """
    if action == 'publish':
        _, record = deposit.fetch_published()
        index_record.delay(str(record.id))
