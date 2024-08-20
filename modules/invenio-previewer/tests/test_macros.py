# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Views module tests."""

import zipfile

from flask import render_template_string, url_for
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from mock import patch
from six import BytesIO, b


def create_file(record, filename, stream):
    """Create a file and add in record."""
    obj = ObjectVersion.create(record.bucket, filename, stream=stream)
    record.update(
        dict(
            _files=[
                dict(
                    bucket=str(record.bucket.id),
                    key=filename,
                    size=obj.file.size,
                    checksum=str(obj.file.checksum),
                    version_id=str(obj.version_id),
                ),
            ]
        )
    )
    record.commit()
    db.session.commit()


def preview_url(pid_val, filename):
    """Preview URL."""
    return url_for(
        "invenio_records_ui.recid_previewer", pid_value=pid_val, filename=filename
    )


def test_default_extension(testapp, webassets, record):
    """Test view by default."""
    create_file(record, "testfile", BytesIO(b"empty"))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "testfile"))
        assert "we are unfortunately not" in res.get_data(as_text=True)


def test_markdown_extension(testapp, webassets, record):
    """Test view with md files."""
    create_file(record, "markdown.md", BytesIO(b"### Testing markdown ###"))
    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "markdown.md"))
        assert "<h3>Testing markdown" in res.get_data(as_text=True)
        with patch("mistune.markdown", side_effect=Exception):
            res = client.get(preview_url(record["control_number"], "markdown.md"))
            assert "we are unfortunately not" in res.get_data(as_text=True)


def test_pdf_extension(testapp, webassets, record):
    """Test view with pdf files."""
    create_file(record, "test.pdf", BytesIO(b"Content not used"))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.pdf"))
        assert "pdf-file-uri" in res.get_data(as_text=True)


def test_csv_papaparsejs_extension(testapp, webassets, record):
    """Test view with csv files."""
    create_file(record, "test.csv", BytesIO(b"A,B\n1,2"))
    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.csv"))
        assert 'data-csv-source="' in res.get_data(as_text=True)


def test_csv_papaparsejs_delimiter(testapp, webassets, record):
    """Test view with csv files."""
    create_file(record, "test.csv", BytesIO(b"A#B\n1#2"))
    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.csv"))
        assert 'data-csv-source="' in res.get_data(as_text=True)


def test_zip_extension(testapp, webassets, record, zip_fp):
    """Test view with a zip file."""
    create_file(record, "test.zip", zip_fp)

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.zip"))
        assert "Example.txt" in res.get_data(as_text=True)
        assert "Lé UTF8 test.txt" in res.get_data(as_text=True)

        with patch("zipfile.ZipFile", side_effect=zipfile.LargeZipFile):
            res = client.get(preview_url(record["control_number"], "test.zip"))
            assert "Zipfile is too large" in res.get_data(as_text=True)

        with patch("zipfile.ZipFile", side_effect=Exception):
            res = client.get(preview_url(record["control_number"], "test.zip"))
            assert "Zipfile is not previewable" in res.get_data(as_text=True)


def test_json_extension_valid_file(testapp, webassets, record):
    """Test view with JSON files."""
    json_data = (
        '{"name":"invenio","num":42,'
        '"flt":3.14159,"lst":[1,2,3],'
        '"obj":{"field":"<script>alert(1)</script>","num":4}}'
    )
    create_file(record, "test.json", BytesIO(b(json_data)))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.json"))
        assert 'class="language-javascript"' in res.get_data(as_text=True)

        rendered_json = (
            "{\n"
            "    &#34;name&#34;: &#34;invenio&#34;,\n"
            "    &#34;num&#34;: 42,\n"
            "    &#34;flt&#34;: 3.14159,\n"
            "    &#34;lst&#34;: [\n"
            "        1,\n"
            "        2,\n"
            "        3\n"
            "    ],\n"
            "    &#34;obj&#34;: {\n"
            "        &#34;field&#34;: &#34;&lt;script&gt;alert(1)"
            "&lt;/script&gt;&#34;,\n"
            "        &#34;num&#34;: 4\n"
            "    }\n"
            "}"
        )
        assert rendered_json in res.get_data(as_text=True)


def test_json_extension_invalid_file(testapp, webassets, record):
    """Test view with JSON files."""
    wrong_json_data = '{"name":"invenio","num'
    create_file(record, "test_wrong.json", BytesIO(b(wrong_json_data)))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test_wrong.json"))
        assert "we are unfortunately not" in res.get_data(as_text=True)


def test_max_file_size(testapp, webassets, record):
    """Test file size limitation."""
    max_file_size = testapp.config.get("PREVIEWER_MAX_FILE_SIZE_BYTES", 1 * 1024 * 1024)
    too_large_string = "1" * (max_file_size + 1)
    create_file(record, "test.json", BytesIO(b(too_large_string)))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.json"))
        assert "we are unfortunately not" in res.get_data(as_text=True)


def test_xml_extension(testapp, webassets, record):
    """Test view with XML files."""
    xml_data = b'<el a="some"><script>alert(1)</script><c>1</c><c>2</c></el>'
    create_file(record, "test.xml", BytesIO(xml_data))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.xml"))
        assert 'class="language-markup"' in res.get_data(as_text=True)
        assert "&lt;el a=&#34;some&#34;&gt;" in res.get_data(as_text=True)
        assert "&lt;c&gt;1&lt;/c&gt;" in res.get_data(as_text=True)
        assert "&lt;c&gt;2&lt;/c&gt;" in res.get_data(as_text=True)
        assert "&lt;/el&gt;" in res.get_data(as_text=True)

        with patch("xml.dom.minidom.Node.toprettyxml", side_effect=Exception):
            res = client.get(preview_url(record["control_number"], "test.xml"))
            assert "we are unfortunately not" in res.get_data(as_text=True)


def test_ipynb_extension(testapp, webassets, record):
    """Test view with IPython notebooks files."""
    create_file(
        record,
        "test.ipynb",
        BytesIO(
            b"""
{
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "This is an example notebook.<script>alert();</script>"
      ]
    }
  ],
  "metadata":{
      "kernelspec":{
         "display_name":"Python 2",
         "language":"python",
         "name":"python2"
      },
      "language_info":{
         "codemirror_mode":{
            "name":"ipython",
            "version":2
         },
         "file_extension":".py",
         "mimetype":"text/x-python",
         "name":"python",
         "nbconvert_exporter":"python",
         "pygments_lexer":"ipython2",
         "version":"2.7.10"
      }
   },
  "nbformat":4,
  "nbformat_minor":0
}"""
        ),
    )

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.ipynb"))
        as_text = res.get_data(as_text=True)
        assert "This is an example notebook." in as_text
        # test HTML tag sanitize
        assert "<script>alert();</script>" not in as_text


def test_simple_image_extension(testapp, webassets, record):
    """Test view with simple image files (PNG)."""
    create_file(record, "test.png", BytesIO(b"Content not used"))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test.png"))
        as_text = res.get_data(as_text=True)
        assert '<img src="' in as_text
        assert 'class="previewer-simple-image"' in as_text


def test_txt_extension_valid_file(testapp, webassets, record):
    """Text .txt file viewer."""
    create_file(record, "test1.txt", BytesIO(b"test content foobar"))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test1.txt"))
        assert "<pre>test content foobar</pre>" in res.get_data(as_text=True)


def test_txt_extension_large_file(testapp, webassets, record):
    """Text .txt file viewer for large files."""
    max_file_size = testapp.config.get("PREVIEWER_TXT_MAX_BYTES", 1 * 1024 * 1024)
    too_large_string = "1" * (max_file_size + 1)
    create_file(record, "test1.txt", BytesIO(b(too_large_string)))

    with testapp.test_client() as client:
        res = client.get(preview_url(record["control_number"], "test1.txt"))
        assert "file truncated" in res.get_data(as_text=True)


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
