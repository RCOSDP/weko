# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI test."""

from __future__ import absolute_import, print_function

from click.testing import CliRunner


def test_basic_cli():
    """Test version import."""
    from invenio_app.cli import cli
    res = CliRunner().invoke(cli)
    assert res.exit_code == 0
