# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Error."""

from __future__ import absolute_import, print_function


class OAIBadMetadataFormatError(Exception):
    """Metadata format required doesn't exist."""


class OAISetSpecUpdateError(Exception):
    """Spec attribute cannot be updated.

    The correct way is to delete the set and create a new one.
    """
