# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Previews a JSON file."""

import json
from collections import OrderedDict

from flask import current_app, render_template

from ..proxies import current_previewer
from ..utils import detect_encoding

previewable_extensions = ["json"]


def render(file):
    """Pretty print the JSON file for rendering."""
    with file.open() as fp:
        encoding = detect_encoding(fp, default="utf-8")
        file_content = fp.read().decode(encoding)
        json_data = json.loads(file_content, object_pairs_hook=OrderedDict)
        return json.dumps(json_data, indent=4, separators=(",", ": "))


def validate_json(file):
    """Validate a JSON file."""
    max_file_size = current_app.config.get(
        "PREVIEWER_MAX_FILE_SIZE_BYTES", 1 * 1024 * 1024
    )
    if file.size > max_file_size:
        return False

    with file.open() as fp:
        try:
            json.loads(fp.read().decode("utf-8"))
            return True
        except Exception:
            return False


def can_preview(file):
    """Determine if the given file can be previewed."""
    return file.is_local() and file.has_extensions(".json") and validate_json(file)


def preview(file):
    """Render the appropriate template with embed flag."""
    return render_template(
        "invenio_previewer/json_prismjs.html",
        file=file,
        content=render(file),
        js_bundles=current_previewer.js_bundles + ["prism_js.js"],
        css_bundles=["prism_css.css"],
    )
