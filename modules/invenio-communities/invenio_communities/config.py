# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Invenio Communities configuration."""

from __future__ import unicode_literals

from datetime import timedelta

import pkg_resources

COMMUNITIES_REQUEST_EXPIRY_TIME = timedelta(days=365)
"""Time after which the inclusion requests automatically expire."""

COMMUNITIES_DELETE_HOLDOUT_TIME = timedelta(days=365)
"""Time after which the communities marked for deletion are hard-deleted."""

COMMUNITIES_LOGO_EXTENSIONS = ['png', 'jpg', 'jpeg', 'svg']
"""Allowed file extensions for the communities logo."""

COMMUNITIES_LOGO_MAX_SIZE = 1000 * 1000 * 1.5  # 1.5 MB
"""Allowed file size for the communities logo."""

COMMUNITIES_RECORD_KEY = 'communities'
"""Key inside the JSON record for communities."""

COMMUNITIES_SORTING_OPTIONS = [
    'title',
    'ranking',
]
"""Possible communities sorting options."""

COMMUNITIES_DEFAULT_SORTING_OPTION = 'ranking'
"""Default sorting option."""

COMMUNITIES_OAI_FORMAT = 'user-{community_id}'
"""String template for the community OAISet 'spec'."""

COMMUNITIES_BUCKET_UUID = '00000000-0000-0000-0000-000000000000'
"""UUID for the bucket corresponding to communities."""

COMMUNITIES_INDEX_PREFIX = 'records-'
"""Key inside the JSON record for communities."""

COMMUNITIES_OAI_ENABLED = False
"""Using OAIServer if available."""
try:
    pkg_resources.get_distribution('invenio_oaiserver')
    COMMUNITIES_OAI_ENABLED = True
except pkg_resources.DistributionNotFound:  # pragma: no cover
    pass

COMMUNITIES_MAIL_ENABLED = False
"""Using Flask-Mail if available."""
try:
    pkg_resources.get_distribution('flask_mail')
    COMMUNITIES_MAIL_ENABLED = True
except pkg_resources.DistributionNotFound:  # pragma: no cover
    pass

COMMUNITIES_REQUEST_EMAIL_BODY_TEMPLATE = \
    'invenio_communities/request_email_body.html'
"""Template for InclusionRequest email body."""

COMMUNITIES_REQUEST_EMAIL_TITLE_TEMPLATE = \
    'invenio_communities/request_email_title.html'
"""Template for InclusionRequest email title."""

COMMUNITIES_REQUEST_EMAIL_SENDER = 'info@inveniosoftware.org'
"""Sender email for all inclusion request notification emails."""

COMMUNITIES_JSTEMPLATE_RESULTS_CURATE = \
    'templates/invenio_communities/ng_record_curate.html'
"""Angular template for records in curation view."""

COMMUNITIES_COMMUNITY_TEMPLATE = "invenio_communities/community_base.html"
"""Base template for community pages."""

COMMUNITIES_CURATE_TEMPLATE = "invenio_communities/curate.html"
"""Template for inclusion requests curation page."""

COMMUNITIES_SEARCH_TEMPLATE = "invenio_communities/search.html"
"""Template for the search page."""

COMMUNITIES_INDEX_TEMPLATE = 'invenio_communities/index.html'
"""Template for the index page."""

COMMUNITIES_DETAIL_TEMPLATE = 'invenio_communities/detail.html'
"""Template for the community details page."""

COMMUNITIES_ABOUT_TEMPLATE = 'invenio_communities/about.html'
"""Template for the community about page."""

COMMUNITIES_NEW_TEMPLATE = 'invenio_communities/new.html'
"""Template for the new community page."""

COMMUNITIES_EDIT_TEMPLATE = 'invenio_communities/new.html'
"""Template for the edit communtiy page."""

COMMUNITIES_URL_COMMUNITY_VIEW = \
    '{protocol}://{host}/c/{community_id}/'
"""String pattern to generate the URL for the view of a community."""

THEME_MATHJAX_CDN = '//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-AMS_HTML'
"""Template for the new community page."""

COMMUNITIES_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'br',
    'code',
    'div',
    'em',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'i',
    'li',
    'ol',
    'p',
    'pre',
    'span',
    'strike',
    'strong',
    'sub',
    'sup',
    'u',
    'ul',
    'hr',
    'table',
    'thead',
    'tbody',
    'tfoot',
    'tr',
    'th',
    'td',
]
"""List of allowed tags used to sanitize HTML output for communities."""

COMMUNITIES_ALLOWED_ATTRS = {
    '*': ['class', 'style'],
    'a': ['href', 'title', 'name', 'class', 'rel'],
    'abbr': ['title'],
    'acronym': ['title'],
}
"""List of allowed attributes used to sanitize HTML output for communities."""

COMMUNITIES_ALLOWED_STYLES = [
    'font-family', 'font-size', 'color', 'background-color',
    'text-align', 'font-weight', 'font-style', 'text-decoration',
]
"""List of allowed styles used to sanitize HTML output for communities."""

COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT = 2
"""Allowed Role's id higher than this number full access to list Indexes."""

COMMUNITIES_LIST_THUMBNAIL_WIDTH = 256
"""community thumbnail width in community list."""

COMMUNITIES_LIST_THUMBNAIL_HEIGHT = 256
"""community thumbnail height in community list."""
