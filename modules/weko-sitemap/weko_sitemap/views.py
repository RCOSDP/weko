# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, render_template, abort, request, current_app
from flask_admin import BaseView, expose
from flask_babelex import gettext as _

blueprint = Blueprint(
    'weko_sitemap',
    __name__,
    url_prefix='/weko/sitemaps',
    template_folder='templates',
    static_folder='static',
)

"""
class SitemapSettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        return self.render(current_app.config["WEKO_SITEMAP_ADMIN_TEMPLATE"])

sitemap_adminview = {
  'view_class': SitemapSettingView,
  'kwargs': {
      'category': _('Setting'),
      'name': _('Sitemap'),
      'endpoint': 'sitemap'
  }
}
"""

#@blueprint.route("/")
#def index():
#    """Render a basic view."""
#    return render_template(
#        "weko_sitemap/index.html",
#        module_name=_('weko-sitemap'))

"""
@blueprint.route("/")
def index():
    try:
        result_list = str("No Data")
        if request.method == "POST":

            result_list = str("test url ")
            data = request.args.get('postdata')

            if(data == 'clicked'):
                result = result_list
                return result

        elif request.method == "GET":
            return render_template("weko_sitemap/sitemap.html", result=result_list)
    except Exception as e:
        #return abort(500)
        return str(e)
"""
