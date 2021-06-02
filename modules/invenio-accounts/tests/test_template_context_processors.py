# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Tests for template context processors."""

from __future__ import absolute_import, print_function

from flask import render_template_string


def test_context_processor_jwt(app):
    """Test context processor JWT."""
    template = r"""
    {{ jwt() }}
    """
    with app.test_request_context():
        html = render_template_string(template)
        assert 'authorized_token' in html


def test_context_processor_jwt_token(app):
    """Test context processor token JWT."""
    template = r"""
    {{ jwt_token() }}
    """
    with app.test_request_context():
        html = render_template_string(template)
        assert html
