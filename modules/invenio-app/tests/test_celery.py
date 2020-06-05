# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Celery test."""

from __future__ import absolute_import, print_function


def test_celery():
    """Test celery application."""
    from invenio_app.celery import celery
    celery.loader.import_default_modules()
