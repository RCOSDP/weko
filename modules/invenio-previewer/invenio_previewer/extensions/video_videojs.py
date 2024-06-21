# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2023 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Render video file using videojs."""

from flask import current_app, render_template

from ..proxies import current_previewer
from ..utils import dotted_exts

# The video file world is complex, because support depends on
# hardware, OS, software and browser. A reasonable choice of supported
# extensions (https://en.wikipedia.org/wiki/HTML5_video#Browser_support) that
# are least likely to lead to an unsupported warning for end-users are
# mp4 and webm files. However, this is made customizable per instance.
previewable_extensions = current_app.config.get("PREVIEWER_VIDEO_EXTS", ["mp4", "webm"])


def can_preview(file):
    """Determine if the given file can be previewed."""
    return file.has_extensions(*dotted_exts(previewable_extensions))


def preview(file):
    """Render the appropriate template with embed flag."""
    data_setup = {
        "controls": True,
        "preload": "metadata",
        "fill": True,
        **current_app.config.get("PREVIEWER_VIDEO_DATA_SETUP", {}),
    }

    return render_template(
        "invenio_previewer/videojs.html",
        file=file,
        data_setup=data_setup,
        js_bundles=current_previewer.js_bundles + ["videojs_js.js"],
        css_bundles=current_previewer.css_bundles + ["video_videojs_css.css"],
    )
