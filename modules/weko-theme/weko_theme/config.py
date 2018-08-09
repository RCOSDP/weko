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

"""Configuration for weko-theme."""

BASE_PAGE_TEMPLATE = 'weko_theme/page.html'
"""Base template for user facing pages."""

BASE_EDIT_TEMPLATE = 'weko_theme/edit.html'
"""Base template for user facing pages.

The template provides a basic skeleton which takes care of loading assets,
embedding header metadata and define basic template blocks. All other user
facing templates usually extends from this template and thus changing this
template allows to change design and layout of WEKO3.
"""
THEME_HEADER_TEMPLATE = 'weko_theme/header.html'
"""Header template which is normally included in :data:`BASE_TEMPLATE`."""

THEME_HEADER_EDITOR_TEMPLATE = 'weko_theme/header_editor.html'
"""Header editor template."""

THEME_HEADER_WYSIWYG_TEMPLATE = 'weko_theme/header_wysiwyg.html'
"""Header wysiwyg template."""

THEME_HEADER_LOGIN_TEMPLATE = 'weko_theme/header_login.html'
"""Header login template, included in :data:`THEME_HEADER_TEMPLATE`."""

THEME_BODY_TEMPLATE = 'weko_theme/body.html'
"""Body template which is normally included in :data:`BASE_TEMPLATE`."""

THEME_LOGO = 'images/weko-logo.png'
"""The logo to be used on the header and on the cover."""

THEME_LOGO_ADMIN = 'images/weko-logo.png'
"""The logo to be used on the admin views header."""

THEME_FOOTER_TEMPLATE = 'weko_theme/footer.html'
"""Footer template which is normally included in :data:`BASE_TEMPLATE`."""

THEME_FOOTER_EDITOR_TEMPLATE = 'weko_theme/footer_editor.html'
"""Footer editor template."""

THEME_FOOTER_WYSIWYG_TEMPLATE = 'weko_theme/footer_wysiwyg.html'
"""Footer wysiwyg template."""

THEME_SITENAME = 'WEKO3'
"""The name of the site to be used on the header and as a title."""

THEME_SEARCHBAR = True
"""Enable or disable the search bar."""

THEME_FRONTPAGE_TEMPLATE = 'weko_theme/frontpage.html'
"""Template for front page."""
