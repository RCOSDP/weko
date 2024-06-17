# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Relations system field errors."""

from ...errors import RecordsError


class RelationError(RecordsError):
    """Base relation error class."""


class InvalidRelationValue(RelationError):
    """Invalid relation value."""


class InvalidCheckValue(RelationError):
    """Invalid check value."""
