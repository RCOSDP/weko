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

"""WEKO3 module docstring."""

import sys

from flask import abort, current_app, flash, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy
from . import config
from invenio_db import db
from .models import PDFCoverPageSettings


_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)


class ItemSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        try:
            email_display_flg = '0'
            search_author_flg = 'name'
            if current_app.config['EMAIL_DISPLAY_FLG']:
                email_display_flg = '1'
            if 'ITEM_SEARCH_FLG' in current_app.config:
                search_author_flg = current_app.config['ITEM_SEARCH_FLG']

            if request.method == 'POST':
                # Process forms
                form = request.form.get('submit', None)
                if form == 'set_search_author_form':
                    search_author_flg = request.form.get(
                        'searchRadios', 'name')
                    _app.config['ITEM_SEARCH_FLG'] = search_author_flg
                    email_display_flg = request.form.get('displayRadios', '0')
                    if email_display_flg == '1':
                        _app.config['EMAIL_DISPLAY_FLG'] = True
                    else:
                        _app.config['EMAIL_DISPLAY_FLG'] = False
                    flash(_('Author flag was updated.'), category='success')

            return self.render(config.ADMIN_SET_ITEM_TEMPLATE,
                               search_author_flg=search_author_flg,
                               email_display_flg=email_display_flg)
        except:
            current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        return abort(400)

class PdfCoverPageSettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        db.create_all()
        record = PDFCoverPageSettings.find(1)
        try:
            return self.render(
                current_app.config["WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE"],
                avail = record.avail,
                header_display_type = record.header_display_type,
                header_output_string = record.header_output_string,
                header_output_image = record.header_output_image,
                header_display_position = record.header_display_position
            )
        except AttributeError:
            makeshift = PDFCoverPageSettings(avail='disable', header_display_type=None, header_output_string=None, header_output_image = None, header_display_position = None)
            db.session.add(makeshift)
            db.session.commit()
            record = PDFCoverPageSettings.find(1)
            return self.render(
                current_app.config["WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE"],
                avail = record.avail,
                header_display_type = record.header_display_type,
                header_output_string = record.header_output_string,
                header_output_image = record.header_output_image,
                header_display_position = record.header_display_position
            )



item_adminview = {
    'view_class': ItemSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Items'),
        'endpoint': 'itemsetting'
    }
}

pdfcoverpage_adminview = {
    'view_class': PdfCoverPageSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('PDF Cover Page'),
        'endpoint': 'pdfcoverpage'
    }
}

__all__ = (
    'pdfcoverpage_adminview',
    'PdfCoverPageSettingView',
    'item_adminview',
    'ItemSettingView',
)
