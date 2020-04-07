# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Bundles for weko-index-tree."""

from flask_assets import Bundle
from invenio_assets import NpmBundle

style = Bundle(
    'css/weko_index_tree/styles.bundle.css',
    filters='cleancss',
    output="gen/index_tree_view.%(version)s.css"
)

js_treeview = NpmBundle(
    'js/weko_index_tree/inline.bundle.js',
    'js/weko_index_tree/polyfills.bundle.js',
    'js/weko_index_tree/main.bundle.js',
    output="gen/index_tree_view.js"
)

js = Bundle(
    'js/weko_index_tree/app.js',
    # filters='requirejs',  # JQuery etc is already included in Flask-Admin
    output="gen/index_tree.%(version)s.js"
)
