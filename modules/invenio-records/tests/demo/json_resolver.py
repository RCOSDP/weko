# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Test JSON resolver."""


import jsonresolver


@jsonresolver.route("/<item>", host="nest.ed")
def test_resolver(item):
    """Create a nested JSON."""
    next_ = (
        {
            "$ref": "http://nest.ed/{}".format(item[1:]),
        }
        if len(item[1:])
        else "."
    )
    return {"letter": item[0], "next": next_}
