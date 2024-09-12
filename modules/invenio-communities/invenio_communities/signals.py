# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Communities module signals."""

from __future__ import absolute_import, print_function

from blinker import Namespace

_signals = Namespace()

inclusion_request_created = _signals.signal('inclusion_request_created')
"""Signal is sent after an inclusion request is created.

Example subscriber:

.. code-block:: python

    def receiver(sender, request=None, **kwargs):
        # ...

    The sender is the current Flask application.

    from invenio_communities.signals import inclusion_request_created
    inclusion_request_created.connect(receiver)
"""

community_created = _signals.signal('community_created')
