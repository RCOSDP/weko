# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Bundles for weko_indextree_journal."""

from flask_assets import Bundle
from invenio_assets import NpmBundle

style = Bundle(
    'css/weko_indextree_journal/styles.bundle.css',
    filters='cleancss',
    output="gen/indextree_journal_view.%(version)s.css"
)

js_treeview = NpmBundle(
    'js/weko_indextree_journal/inline.bundle.js',
    'js/weko_indextree_journal/polyfills.bundle.js',
    'js/weko_indextree_journal/main.bundle.js',
    output="gen/indextree_journal_view.js"
)

js = Bundle(
    'js/weko_indextree_journal/app.js',
    # filters='requirejs',
    output="gen/indextree_journal.%(version)s.js"
)
