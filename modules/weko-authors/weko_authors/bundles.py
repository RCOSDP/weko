# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Bundles for weko-authors."""

from flask_assets import Bundle
from invenio_assets import NpmBundle

css = Bundle(
    'css/weko_authors/styles.bundle.css',
    filters='cleancss',
    output="gen/author.%(version)s.css"
)

js = NpmBundle(
    'js/weko_authors/inline.bundle.js',
    'js/weko_authors/polyfills.bundle.js',
    'js/weko_authors/main.bundle.js',
    filters='jsmin',
    output="gen/author.%(version)s.js",
)
author_search_css = Bundle(
    'css/weko_authors/styles.search.bundle.css',
    filters='cleancss',
    output="gen/authorSearch.%(version)s.css"
)

author_search_js = NpmBundle(
    'js/weko_authors/inline.search.bundle.js',
    'js/weko_authors/polyfills.search.bundle.js',
    'js/weko_authors/main.search.bundle.js',
    filters='jsmin',
    output="gen/authorSearch.%(version)s.js",
)

author_prefix_css = Bundle(
    'css/weko_authors/styles.prefix.bundle.css',
    filters='cleancss',
    output="gen/authorPrefix.%(version)s.css",
)

author_prefix_js = Bundle(
    'js/weko_authors/inline.prefix.bundle.js',
    'js/weko_authors/polyfills.prefix.bundle.js',
    'js/weko_authors/main.prefix.bundle.js',
    filters='jsmin',
    output="gen/authorPrefix.%(version)s.js",
)
