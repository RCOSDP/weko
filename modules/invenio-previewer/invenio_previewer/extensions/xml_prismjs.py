# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Previews an XML file."""

import xml.dom.minidom

from flask import current_app, render_template
from invenio_i18n import gettext as _

from ..proxies import current_previewer
from ..utils import detect_encoding

previewable_extensions = ["xml"]


def render(file):
    """Pretty print the XML file for rendering."""
    with file.open() as fp:
        encoding = detect_encoding(fp, default="utf-8")
        try:
            file_content = fp.read().decode(encoding)
            parsed_xml = xml.dom.minidom.parseString(file_content)
            return parsed_xml.toprettyxml(indent="  ", newl="")
        except UnicodeDecodeError:
            return _(
                "Error decoding the file. Are you sure it is '{encoding}'?"
            ).format(encoding)


def validate_xml(file):
    """Validate an XML file."""
    max_file_size = current_app.config.get(
        "PREVIEWER_MAX_FILE_SIZE_BYTES", 1 * 1024 * 1024
    )
    if file.size > max_file_size:
        return False

    with file.open() as fp:
        try:
            content = fp.read().decode("utf-8")
            xml.dom.minidom.parseString(content)
            return True
        except Exception:
            return False


def can_preview(file):
    """Determine if the given file can be previewed."""
    return file.is_local() and file.has_extensions(".xml") and validate_xml(file)


def preview(file):
    """Render appropiate template with embed flag."""
    return render_template(
        "invenio_previewer/xml_prismjs.html",
        file=file,
        content=render(file),
        js_bundles=current_previewer.js_bundles + ["prism_js.js"],
        css_bundles=["prism_css.css"],
    )
