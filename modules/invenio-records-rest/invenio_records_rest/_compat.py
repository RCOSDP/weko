# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Python 2/3 compatibility helpers."""

try:  # Python 3 way of inspecting functions
    from inspect import signature, Parameter

    def wrap_links_factory(links_factory):
        """Test if the links_factory function accepts kwargs."""
        sign = signature(links_factory)
        kwargs_param = [p for p in sign.parameters.values()
                        if p.kind == Parameter.VAR_KEYWORD]
        return len(kwargs_param) == 0
except ImportError:  # Python 2 way of inspecting functions
    from inspect import getargspec

    def wrap_links_factory(links_factory):
        """Test if the links_factory function accepts kwargs."""
        spec = getargspec(links_factory)
        return spec.keywords is None
