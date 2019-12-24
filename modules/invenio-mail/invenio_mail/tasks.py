# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Background tasks for mail module."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask import current_app
from flask_mail import Message


@shared_task
def send_email(data):
    """Celery task for sending emails.

    .. warning::

       Due to an incompatibility between MessagePack serialization and Message,
       support for attachments and dates is limited. Consult the tests for
       details.
    """
    msg = Message()
    msg.__dict__.update(data)
    current_app.extensions['mail'].send(msg)
