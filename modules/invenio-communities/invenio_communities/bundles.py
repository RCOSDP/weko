# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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

js_trumbowyg = NpmBundle(
    "node_modules/trumbowyg/dist/trumbowyg.min.js",
    "node_modules/trumbowyg/dist/plugins/colors/trumbowyg.colors.min.js",
    "node_modules/trumbowyg/dist/plugins/fontfamily/trumbowyg.fontfamily.min.js",
    "node_modules/trumbowyg/dist/plugins/fontsize/trumbowyg.fontsize.min.js",
    "node_modules/trumbowyg/dist/plugins/table/trumbowyg.table.min.js",

    npm={
        'trumbowyg': '~2.25.1'
    },
    output='gen/communities_trumbowyg.%(version)s.js'
)

css_trumbowyg = Bundle(
    "node_modules/trumbowyg/dist/ui/trumbowyg.min.css",
    "node_modules/trumbowyg/dist/plugins/colors/ui/trumbowyg.colors.min.css",
    "node_modules/trumbowyg/dist/plugins/table/ui/trumbowyg.table.min.css",
    filters='cleancss',
    output='gen/communities_trumbowyg.%(version)s.css'
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
