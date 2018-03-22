# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

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
