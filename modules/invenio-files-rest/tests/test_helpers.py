# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Storage module tests."""

import pytest

from invenio_files_rest.helpers import make_path


def test_make_path():
    """Test path for files."""
    myid = "deadbeef-dead-dead-dead-deaddeafbeef"
    base = "/base"
    f = "data"

    assert (
        make_path(base, myid, f, 1, 1)
        == "/base/d/eadbeef-dead-dead-dead-deaddeafbeef/data"
    )
    assert (
        make_path(base, myid, f, 3, 1)
        == "/base/d/e/a/dbeef-dead-dead-dead-deaddeafbeef/data"
    )
    assert (
        make_path(base, myid, f, 1, 3)
        == "/base/dea/dbeef-dead-dead-dead-deaddeafbeef/data"
    )
    assert (
        make_path(base, myid, f, 2, 2)
        == "/base/de/ad/beef-dead-dead-dead-deaddeafbeef/data"
    )

    pytest.raises(AssertionError, make_path, base, myid, f, 1, 50)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 1)
    pytest.raises(AssertionError, make_path, base, myid, f, 50, 50)
