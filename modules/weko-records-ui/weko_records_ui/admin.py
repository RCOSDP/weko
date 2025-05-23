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
import unicodedata
from datetime import datetime

from flask import abort, current_app, flash, jsonify, request
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_babelex import gettext as _
from flask_login import current_user
from flask_wtf import FlaskForm
from invenio_db import db
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.orm import load_only
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoRecord
from weko_records.api import ItemsMetadata
from weko_search_ui.api import get_search_detail_keyword
from werkzeug.local import LocalProxy

from . import config
from .models import InstitutionName, PDFCoverPageSettings
from .utils import check_items_settings

_app = LocalProxy(lambda: current_app.extensions['weko-admin'].app)


class ItemSettingView(BaseView):
    """Item setting view."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        try:
            form = FlaskForm(request.form)
            check_items_settings()
            email_display_flg = '0'
            search_author_flg = 'name'
            open_date_display_flg = current_app.config.get('OPEN_DATE_HIDE_VALUE')
            is_display_request_form = current_app.config.get('DISPLAY_REQUEST_FORM', False)
            # Get display request form settings
            items_display_settings = AdminSettings.get('items_display_settings')
            if items_display_settings:
                is_display_request_form = items_display_settings.__dict__.get('display_request_form')

            if current_app.config['EMAIL_DISPLAY_FLG']:
                email_display_flg = '1'
            if 'ITEM_SEARCH_FLG' in current_app.config:
                search_author_flg = current_app.config['ITEM_SEARCH_FLG']
            if current_app.config.get('OPEN_DATE_DISPLAY_FLG'):
                open_date_display_flg = current_app.config.get(
                    'OPEN_DATE_DISPLAY_VALUE')

            if request.method == 'POST' and form.validate():
                # Process forms
                form = request.form.get('submit', None)
                if form == 'set_search_author_form':
                    settings = items_display_settings.__dict__
                    email_display_flg = request.form.get('displayRadios', '0')
                    is_email_display = (email_display_flg == '1')
                    settings['items_display_email'] = is_email_display

                    open_date_display_flg = request.form.get('openDateDisplayRadios', '0')
                    is_open_date_display = open_date_display_flg == '1'
                    settings['item_display_open_date'] = is_open_date_display

                    request_form_display_value = request.form.get('requestFormDisplayRadios', '0')
                    is_display_request_form = request_form_display_value == '1'
                    settings['display_request_form'] = is_display_request_form

                    AdminSettings.update('items_display_settings', settings)
                    flash(_('Author flag was updated.'), category='success')

            return self.render(config.ADMIN_SET_ITEM_TEMPLATE,
                               search_author_flg=search_author_flg,
                               email_display_flg=email_display_flg,
                               open_date_display_flg=open_date_display_flg,
                               is_request_form_display=is_display_request_form,
                               form=form)
        except BaseException:
            import traceback
            exc, val, tb = sys.exc_info()
            current_app.logger.error(
                'Unexpected error: {}'.format(sys.exc_info()))
            current_app.logger.error(
                traceback.format_exception(exc, val, tb)
            )
        return abort(400)

class PdfCoverPageSettingView(BaseView):
    """PdfCover Page settings."""

    @expose('/', methods=['GET'])
    def index(self):
        """Index."""
        db.create_all()
        record = PDFCoverPageSettings.find(1)
        try:
            header_output_image = record.header_output_image
            if header_output_image:
                header_output_image = header_output_image.replace(
                    current_app.instance_path, "")
            return self.render(
                current_app.config["WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE"],
                avail=record.avail,
                header_display_type=record.header_display_type,
                header_output_string=record.header_output_string,
                header_output_image=header_output_image,
                header_display_position=record.header_display_position
            )
        except AttributeError:
            try:
                makeshift = PDFCoverPageSettings(
                    avail='disable',
                    header_display_type=None,
                    header_output_string=None,
                    header_output_image=None,
                    header_display_position=None)
                db.session.add(makeshift)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(e)
                return self.render(
                    current_app.config["WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE"],
                    avail='',
                    header_display_type='',
                    header_output_string='',
                    header_output_image='',
                    header_display_position=''
                )
            record = PDFCoverPageSettings.find(1)
            return self.render(
                current_app.config["WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE"],
                avail=record.avail,
                header_display_type=record.header_display_type,
                header_output_string=record.header_output_string,
                header_output_image=record.header_output_image,
                header_display_position=record.header_display_position
            )


class InstitutionNameSettingView(BaseView):
    """Institution Names Setting."""

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        """Index."""
        form = FlaskForm(request.form)
        if request.method == 'POST' and form.validate():
            rf = request.form.to_dict()
            InstitutionName.set_institution_name(rf['institution_name'])
            flash(_('Institution Name was updated.'), category='success')
        institution_name = InstitutionName.get_institution_name()
        return self.render(config.INSTITUTION_NAME_SETTING_TEMPLATE,
                           institution_name=institution_name,form=form)


class ItemManagementBulkUpdate(BaseView):
    """Item Management - Bulk Update view."""

    @expose('/', methods=['GET'])
    def index(self):
        """Render view."""
        detail_condition = get_search_detail_keyword('')
        return self.render(
            current_app.config['WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE'],
            fields=current_app.config['WEKO_RECORDS_UI_BULK_UPDATE_FIELDS'][
                'fields'],
            licences=current_app.config['WEKO_RECORDS_UI_LICENSE_DICT'],
            management_type='update',
            detail_condition=detail_condition)

    @expose('/items_metadata', methods=['GET'])
    def get_items_metadata(self):
        """Get the metadata of items to bulk update."""
        def get_file_data(meta):
            file_data = {}
            for key in meta:
                if isinstance(meta.get(key), list):
                    for item in meta.get(key):
                        if isinstance(item, dict) and 'filename' in item:
                            file_data[key] = meta.get(key)
                            break
            return file_data

        pids = request.values.get('pids')
        pid_list = []
        if pids is not None:
            pid_list = pids.split('/')

        data = {}
        for pid_value in pid_list:
            record = WekoRecord.get_record_by_pid(pid_value)
            indexes = []
            if isinstance(record.get('path'), list):
                indexes = record.get('path')

            pid = PersistentIdentifier.get('recid', pid_value)
            meta = ItemsMetadata.get_record(pid.object_uuid)
            last_pid = PIDVersioning(child=pid).last_child

            if meta:
                data[pid_value] = {}
                data[pid_value]['meta'] = meta
                data[pid_value]['index'] = {"index": indexes}
                data[pid_value]['contents'] = get_file_data(meta)
                data[pid_value]['version'] = last_pid.pid_value

        return jsonify(data)


institution_adminview = {
    'view_class': InstitutionNameSettingView,
    'kwargs': {
        'category': _('Setting'),
        'name': _('Others'),
        'endpoint': 'others'
    }
}

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

item_management_bulk_update_adminview = {
    'view_class': ItemManagementBulkUpdate,
    'kwargs': {
        'category': _('Items'),
        'name': _('Bulk Update'),
        'endpoint': 'items/bulk/update'
    }
}

__all__ = (
    'pdfcoverpage_adminview',
    'PdfCoverPageSettingView',
    'item_adminview',
    'ItemSettingView',
    'institution_adminview',
    'InstitutionNameSettingView'
)
