# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Bundles for weko-items-ui."""

from flask_assets import Bundle

js = Bundle(
    'js/weko_schema_ui/app.js',
    filters='jsmin',
    output="gen/weko_schema_ui.%(version)s.js",
)
