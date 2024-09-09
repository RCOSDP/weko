# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Communities bundles."""

from __future__ import absolute_import, print_function

from flask_assets import Bundle
from invenio_assets import NpmBundle, RequireJSFilter

js = Bundle(
    "js/invenio_communities/main.js",
    filters=RequireJSFilter(),
    output='gen/communities.%(version)s.js'
)

js_tree = NpmBundle(
    'js/invenio_communities/inline.community.bundle.js',
    'js/invenio_communities/polyfills.community.bundle.js',
    'js/invenio_communities/main.community.bundle.js',
    output='gen/communities_tree.%(version)s.js'
)

js_tree_display = NpmBundle(
    'js/invenio_communities/inline.bundle.js',
    'js/invenio_communities/polyfills.bundle.js',
    'js/invenio_communities/main.bundle.js',
    output='gen/communities_tree_display.%(version)s.js'
)

ckeditor = Bundle(
    "js/invenio_communities/ckeditor.js",
    filters=RequireJSFilter(),
    output='gen/communities_editor.%(version)s.js'
)

css = NpmBundle(
    'scss/invenio_communities/communities.scss',
    filters='scss, cleancss',
    output='gen/communities.%(version)s.css',
    npm={
        'ckeditor': '~4.5.8',
    }
)

css_tree = Bundle(
    'scss/invenio_communities/styles.community.bundle.css',
    filters='cleancss',
    output="gen/communities_tree.%(version)s.css.css"
)

css_tree_display = Bundle(
    'scss/invenio_communities/styles.bundle.css',
    filters='cleancss',
    output="gen/communities_tree_display.%(version)s.css.css"
)
