# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2023      University of Münster.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Errors and exceptions for mail module."""


class AttachmentOversizeException(Exception):
    """Size of attachment is too big exception."""
