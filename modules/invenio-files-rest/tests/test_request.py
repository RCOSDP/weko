# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Request customization tests."""

from io import BytesIO

from flask import request

from invenio_files_rest.app import Flask


def test_max_content_length():
    """Test max content length."""
    max_len = 10

    app = Flask("test")
    app.config["MAX_CONTENT_LENGTH"] = max_len

    @app.route("/test", methods=["GET", "PUT"])
    def test():
        # Access request.form to ensure form parser kicks-in.
        request.form.to_dict()
        return request.stream.read()

    with app.test_client() as client:
        # No content-type, no max content length checking
        data = b"a" * (max_len + 1)
        res = client.put("/test", input_stream=BytesIO(data))
        assert res.status_code == 200
        assert res.data == data

        # Non-formdata content-type, no max content length checking
        res = client.put(
            "/test",
            input_stream=BytesIO(data),
            headers={"Content-Type": "application/octet-stream"},
        )
        assert res.status_code == 200
        assert res.data == data

        # With form data content-type (below max content length)
        res = client.put(
            "/test", data={"123": "a" * (max_len - 4)}  # content-length == 10
        )
        assert res.status_code == 200
        # Because formdata parsing reads the data stream, trying to read it
        # again means we just get empty data:
        assert res.data == b""

        # With formdata content-type (above max content length)
        res = client.put(
            "/test", data={"123": "a" * (max_len - 3)}  # content-length == 11
        )
        assert res.status_code == 413
