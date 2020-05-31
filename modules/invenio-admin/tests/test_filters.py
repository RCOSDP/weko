# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Filters module tests."""

from __future__ import absolute_import, print_function

import uuid

from invenio_admin.filters import FilterConverter, UUIDEqualFilter


def test_uuid_filter(app, testmodelcls):
    """Test UUID."""
    with app.app_context():
        f = UUIDEqualFilter(testmodelcls.uuidcol, 'uuidcol')
        q = testmodelcls.query
        assert q.whereclause is None

        q_applied = f.apply(testmodelcls.query, str(uuid.uuid4()), None)
        assert q_applied.whereclause is not None

        q_applied = f.apply(testmodelcls.query, "", None)
        assert q_applied.whereclause is None

        q_applied = f.apply(testmodelcls.query, "test", None)
        assert q_applied.whereclause is None


def test_filter_converter_uuid(testmodelcls):
    """Test filter converter."""
    c = FilterConverter()
    f = c.convert('uuidtype', testmodelcls.uuidcol, 'uuidcol')
    assert len(f) == 1
    assert isinstance(f[0], UUIDEqualFilter)


def test_filter_converter_variant(testmodelcls):
    """Test filter converter."""
    c = FilterConverter()
    f = c.convert('variant', testmodelcls.dt, 'dt')
    assert len(f) == 7
