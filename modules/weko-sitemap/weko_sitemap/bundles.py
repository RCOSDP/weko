# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Bundles for weko-sitemap."""

from flask_assets import Bundle

js = Bundle(
    'js/weko_sitemap/sitemap.js',
    # filters='requirejs',
    output="gen/weko_sitemap.%(version)s.js",
)

css = Bundle(
    'css/weko_sitemap/styles.css',
    output="gen/weko_sitemap.%(version)s.css",
)
