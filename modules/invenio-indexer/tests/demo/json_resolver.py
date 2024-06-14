# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test JSON resolver."""

import jsonresolver


@jsonresolver.route("/<path:item>", host="dx.doi.org")
def test_resolver(item):
    """Create a nested JSON."""
    return {"data": item}
