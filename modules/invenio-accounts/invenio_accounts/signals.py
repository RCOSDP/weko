# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Account signals."""

from blinker import Namespace

_signals = Namespace()


datastore_pre_commit = _signals.signal("datastore-pre-commit")
"""Signal sent before the session has been commited.

Parameters:
- ``session`` - a database session

Example receiver:

.. code-block:: python
   def receiver(sender, session):
       # ...

"""


datastore_post_commit = _signals.signal("datastore-post-commit")
"""Signal sent after the session has been commited.

Parameters:
- ``session`` - a database session

Example receiver:

.. code-block:: python
   def receiver(sender, session):
       # ...

"""
