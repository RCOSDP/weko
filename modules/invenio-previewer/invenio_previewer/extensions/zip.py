# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Simple ZIP archive previewer."""

import os
import zipfile

from charset_normalizer import detect
from flask import current_app, render_template

from ..proxies import current_previewer

previewable_extensions = ["zip"]


def make_tree(file):
    """Create tree structure from ZIP archive."""
    max_files_count = current_app.config.get("PREVIEWER_ZIP_MAX_FILES", 1000)
    tree = {"type": "folder", "id": -1, "children": {}}

    try:
        with file.open() as fp:
            zf = zipfile.ZipFile(fp)
            # Detect filenames encoding.
            sample = " ".join(zf.namelist()[:max_files_count])
            if not isinstance(sample, bytes):
                sample = sample.encode("utf-16be")
            encoding = detect(sample).get("encoding", "utf-8")
            for i, info in enumerate(zf.infolist()):
                if i > max_files_count:
                    raise BufferError("Too many files inside the ZIP file.")
                comps = info.filename.split(os.sep)
                node = tree
                for c in comps:
                    if not isinstance(c, str):
                        c = c.decode(encoding)
                    if c not in node["children"]:
                        if c == "":
                            node["type"] = "folder"
                            continue
                        node["children"][c] = {
                            "name": c,
                            "type": "item",
                            "id": "item{0}".format(i),
                            "children": {},
                        }
                    node = node["children"][c]
                node["size"] = info.file_size
    except BufferError:
        return tree, True, None
    except zipfile.LargeZipFile:
        return tree, False, "Zipfile is too large to be previewed."
    except Exception as e:
        current_app.logger.warning(str(e), exc_info=True)
        return tree, False, "Zipfile is not previewable."

    return tree, False, None


def children_to_list(node):
    """Organize children structure."""
    if node["type"] == "item" and len(node["children"]) == 0:
        del node["children"]
    else:
        node["type"] = "folder"
        node["children"] = list(node["children"].values())
        node["children"].sort(key=lambda x: x["name"])
        node["children"] = map(children_to_list, node["children"])
    return node


def can_preview(file):
    """Return True if filetype can be previewed."""
    return file.is_local() and file.has_extensions(".zip")


def preview(file):
    """Return the appropriate template and pass the file and an embed flag."""
    tree, limit_reached, error = make_tree(file)
    list = children_to_list(tree)["children"]
    return render_template(
        "invenio_previewer/zip.html",
        file=file,
        tree=list,
        limit_reached=limit_reached,
        error=error,
        js_bundles=current_previewer.js_bundles + ["fullscreen_js.js"],
        css_bundles=current_previewer.css_bundles + ["zip_css.css"],
    )
