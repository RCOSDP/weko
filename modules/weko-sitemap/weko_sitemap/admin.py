# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

from __future__ import absolute_import, print_function

from flask import abort, current_app, render_template, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _


class SitemapSettingView(BaseView):
    """Sitemap setting view."""

    @expose('/', methods=['GET'])
    def index(self):
        """Sitemap page."""
        from flask_sitemap import sitemap_page_needed
        # sitemap_page_needed.send(current_app.__get_current_object())
        return self.render(current_app.config["WEKO_SITEMAP_ADMIN_TEMPLATE"])


sitemap_adminview = {
    'view_class': SitemapSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Sitemap'),
        'endpoint': 'sitemap'
    }
}
