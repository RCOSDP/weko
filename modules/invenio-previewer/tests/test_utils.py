# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of utilities module."""

from unittest.mock import patch

import pytest
from six import BytesIO

from invenio_previewer import current_previewer
from invenio_previewer.utils import detect_encoding


def test_default_file_reader(testapp, record_with_file):
    """Test view by default."""
    record, testfile = record_with_file
    file_ = current_previewer.record_file_factory(None, record, testfile.key)
    assert file_.version_id == testfile.version_id


@pytest.mark.parametrize(
    "string, confidence, encoding, detect",
    [
        ("Γκρήκ Στρίνγκ".encode("utf-8"), 0.99000, "UTF-8", "UTF-8"),
        ("dhǾk: kjd köd, ddȪj@dd.k".encode("utf-8"), 0.87625, "UTF-8", None),
        ("क्या हाल तुम या कर रहे हो?".encode("utf-8"), 0.99000, "UTF-8", "UTF-8"),
        ("石原氏 移転は「既定路線」".encode("euc-jp"), 0.46666, "EUC-JP", None),
        ("Hi bye sigh die".encode("utf-8"), 1.00000, "UTF-8", "UTF-8"),
        ("Monkey donkey cow crow".encode("euc-jp"), 0.00000, "ASCII", None),
        ("Monkey donkey cow crow".encode("euc-jp"), 0.90000, "EUC-JP", None),
        ("Monkey donkey cow crow".encode("euc-jp"), 0.90001, "EUC-JP", "EUC-JP"),
        ("Monkey donkey cow crow".encode("euc-jp"), 0.50000, "UTF-8", None),
    ],
)
def test_detect_encoding(testapp, string, confidence, encoding, detect):
    """Test encoding detection."""

    f = BytesIO(string)
    initial_position = f.tell()

    with patch("charset_normalizer.detect") as mock_detect:
        mock_detect.return_value = {"encoding": encoding, "confidence": confidence}
        assert detect_encoding(f) is detect
        assert f.tell() == initial_position


def test_detect_encoding_exception(testapp):
    f = BytesIO("Γκρήκ Στρίνγκ".encode("utf-8"))

    with patch("charset_normalizer.detect", Exception):
        assert detect_encoding(f) is None
