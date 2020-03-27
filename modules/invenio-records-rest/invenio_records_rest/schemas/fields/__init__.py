# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom marshmallow fields."""

from .datetime import DateString
from .generated import GenFunction, GenMethod
from .marshmallow_contrib import Function, Method
from .persistentidentifier import PersistentIdentifier
from .sanitizedhtml import SanitizedHTML
from .sanitizedunicode import SanitizedUnicode
from .trimmedstring import TrimmedString

__all__ = (
    'DateString',
    'Function',
    'GenFunction',
    'GenMethod',
    'Method',
    'PersistentIdentifier',
    'SanitizedHTML',
    'SanitizedUnicode',
    'TrimmedString',
)
