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
