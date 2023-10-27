# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

WEKO_SITEMAP_BASE_TEMPLATE = 'weko_sitemap/base.html'
"""Default base template for the demo page."""

WEKO_SITEMAP_ADMIN_TEMPLATE = 'weko_sitemap/sitemap.html'
"""Sitemap templates."""

WEKO_SITEMAP_TOTAL_MAX_URL_COUNT = 10000000
"""Max urls for all pages in total."""

# WEKO_SITEMAP_CACHE_PREFIX = 'sitemap_cache::'
"""Sitemap pages cache prefix."""

WEKO_SITEMAP_URL_SCHEME = 'https'

WEKO_SITEMAP_CACHE_TIMEOUT = 60 * 60 * 24 * 3

# base URL for site (don't chang name)
SITEMAP_BLUEPRINT = None
"""Set our own Blueprint"""

SITEMAP_BLUEPRINT_URL_PREFIX = '/weko/sitemaps'

SITEMAP_ENDPOINT_URL = '/sitemapindex.xml'

SITEMAP_ENDPOINT_PAGE_URL = '/sitemap_<int:page>.xml.gz'

SITEMAP_MAX_URL_COUNT = 10000

WEKO_SITEMAP__ROBOT_TXT = """
User-agent: Bingbot
Crawl-delay: 30
"""
