# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record validators."""

from jsonschema.validators import Draft4Validator, extend

PartialDraft4Validator = extend(Draft4Validator, {'required': None})
"""Partial JSON Schema (draft 4) validator.

Special validator that contains the same validation rules of Draft4Validator,
except for required fields.
"""
