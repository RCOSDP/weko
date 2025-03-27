# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Weko logging bundles settings."""

from flask_assets import Bundle

weko_logging_export_css = Bundle(
    "css/weko_logging/export.less",
    filters="cleancss",
    output="gen/logExport.%(version)s.css",
)
""" Export log CSS bundle. """

weko_logging_export_js = Bundle(
    "js/weko_logging/export.js",
    filters="jsmin",
    output="gen/logExport.%(version)s.js",
)
""" Export log JS bundle. """