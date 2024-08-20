# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Views module tests."""

from flask import render_template_string


def test_view_macro_file_list(testapp):
    """Test file list macro."""
    with testapp.test_request_context():
        files = [
            {
                "key": "test1.txt",
                "size": 10,
                "date": "2016-07-12",
            },
            {
                "key": "test2.txt",
                "size": 12000000,
                "date": "2016-07-12",
            },
        ]

        pid = {"pid_value": 1}

        result = render_template_string(
            """
            {%- from "invenio_previewer/macros.html" import file_list %}
            {{ file_list(files, pid) }}
            """,
            files=files,
            pid=pid,
        )

        assert 'href="/record/1/files/test1.txt?download=1"' in result
        assert "<td>10 Bytes</td>" in result
        assert 'href="/record/1/files/test2.txt?download=1"' in result
        assert "<td>12.0 MB</td>" in result


def test_previewable_test(testapp):
    """Test template test."""
    file = {"type": "md"}
    template = (
        "{% if file.type is previewable %}Previewable"
        "{% else %}Not previewable{% endif %}"
    )
    assert render_template_string(template, file=file) == "Previewable"

    file["type"] = "no"
    assert render_template_string(template, file=file) == "Not previewable"

    file["type"] = "pdf"
    assert render_template_string(template, file=file) == "Previewable"

    file["type"] = ""
    assert render_template_string(template, file=file) == "Not previewable"
