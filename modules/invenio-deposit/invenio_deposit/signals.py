# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Deposit module signals."""

from blinker import Namespace

_signals = Namespace()

post_action = _signals.signal('post-action')
"""Signal is sent after the REST action.

Kwargs:

#. action (str) - name of REST action, e.g. "publish".

#. pid (invenio_pidstore.models.PersistentIdentifier) - PID of the deposit.
        The pid_type is assumed to be 'depid'.

#. deposit (invenio_depost.api.Deposit) - API instance of the deposit

Example subscriber:

.. code-block:: python

    def listener(sender, action, pid, deposit):
        pass

    from invenio_deposit.signals import post_action
    post_action.connect(listener)
"""
