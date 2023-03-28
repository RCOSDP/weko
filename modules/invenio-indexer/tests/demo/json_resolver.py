# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test JSON resolver."""

from __future__ import absolute_import, print_function

import jsonresolver


@jsonresolver.route('/<path:item>', host='dx.doi.org')
def test_resolver(item):
    """Create a nested JSON."""
    return {'data': item}
