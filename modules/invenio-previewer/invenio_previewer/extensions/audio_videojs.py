# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2023 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Render audio player using videojs."""

from flask import current_app, render_template

from ..proxies import current_previewer
from ..utils import dotted_exts

# The audio file world is complex (but less so than video one), because support
# depends on hardware, OS, software and browser. A reasonable choice of
# supported extensions
# (https://en.wikipedia.org/wiki/HTML5_audio#Supported_audio_coding_formats)
# that are least likely lead to an unsupported warning for end-users are mp3,
# wav, aac and flac, but this could be made changeable per instance.
previewable_extensions = current_app.config.get(
    "PREVIEWER_AUDIO_EXTS", ["mp3", "wav", "aac", "flac"]
)


def can_preview(file):
    """Determine if the given file can be previewed."""
    return file.has_extensions(*dotted_exts(previewable_extensions))


def preview(file):
    """Render the appropriate template with embed flag."""
    data_setup = {
        "controls": True,
        "preload": "metadata",
        "fill": True,
        "audioOnlyMode": True,
        **current_app.config.get("PREVIEWER_AUDIO_DATA_SETUP", {}),
    }

    return render_template(
        "invenio_previewer/audio_videojs.html",
        file=file,
        data_setup=data_setup,
        js_bundles=current_previewer.js_bundles + ["videojs_js.js"],
        css_bundles=current_previewer.css_bundles + ["audio_videojs_css.css"],
    )
