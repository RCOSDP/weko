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
from flask_admin.form import rules
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_babelex import gettext as _
from werkzeug.local import LocalProxy
from . import config
from .models import Identifier
from invenio_db import db
from .models import PDFCoverPageSettings
from .models import InstitutionName

from invenio_communities.models import Community
from datetime import datetime
from wtforms import SelectField, StringField
from wtforms import validators
from weko_user_profiles.models import UserProfile

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


class InstitutionNameSettingView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        if request.method == 'POST':
            rf = request.form.to_dict()
            InstitutionName.set_institution_name(rf['institution_name'])
        institution_name = InstitutionName.get_institution_name()
        return self.render(config.INSTITUTION_NAME_SETTING_TEMPLATE,
                           institution_name = institution_name)


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


class IdentifierSettingView(ModelView):
    """Setting model view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = False
    create_template = config.WEKO_PIDSTORE_IDENTIFIER_TEMPLATE

    column_list = ('repository', 'jalc_doi', 'jalc_crossref_doi', 'jalc_datacite_doi', 'cnri', 'suffix')
    column_searchable_list = ['repository', 'jalc_doi']

    form_create_rules = [rules.Header(_('Prefix')),
        'repository', 'jalc_doi', 'jalc_crossref_doi', 'jalc_datacite_doi',
        'cnri',
        rules.Header(_('Suffix')),
        'suffix',
        rules.Header(_('Enable/Disable')),
    ]

    form_choices = {
        'repository': [
            ('0', 'Root Index 0'),
            ('1', 'Root Index 1'),
            # list communities
        ]
    }

    form_widget_args = {
        'jalc_doi': {
            'readonly': True
        },
        'jalc_crossref_doi': {
            'readonly': True
        },
    }

    column_labels = dict(repository=_('Repository'), jalc_doi=_('JaLC DOI'),
        jalc_crossref_doi=_('JaLC CrossRef DOI'),
        jalc_datacite_doi=_('jaLC DataCite DOI'), cnri=_('CNRI'),
        suffix=_('Semi-automatic Suffix')
    )

    form_edit_rules = form_create_rules

    page_size = 25

    def create_model(self, form):
        """
            Create model from form.
            :param form:
                Form instance
        """
        try:
            model = self.model()
            model.created_userId = current_user.get_id()
            model.updated_userId = current_user.get_id()
            print('_________________Get all COMMUNITY______________', get_all_community())
            form.populate_obj(model)
            self.session.add(model)
            self._on_model_change(form, model, True)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s', error=str(ex)), 'error')
                current_app.logger.warning(ex)
            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def edit_form(self, obj):
        """Customize edit form."""
        form = super(IdentifierSettingView, self).edit_form(obj)
        return form

    def on_model_change(self, form, model, is_created):
        """
            Perform some actions before a model is created or updated.

            Called from create_model and update_model in the same transaction
            (if it has any meaning for a store backend).

            By default does nothing.

            :param form:
                Form used to create/update model
            :param model:
                Model that will be created/updated
            :param is_created:
                Will be set to True if model was created and to False if edited
        """

        ### Update hidden data automation
        if is_created:
            model.created_userId = UserProfile.get_by_userid(current_user.get_id()).username
            model.created_date = datetime.utcnow().replace(microsecond=0)
        model.updated_userId = UserProfile.get_by_userid(current_user.get_id()).username
        model.updated_date = datetime.utcnow().replace(microsecond=0)
        pass


    def edit_form(self, obj):
        """
            Customize edit form
        """
        form = super(IdentifierSettingView, self).edit_form(obj)
        return form


def get_all_community():
    """
    Get communities
    """

    class CommunityIdentify:
        def __init__(self, id, title):
            self.id = id
            self.title = title
    data = []
    for i in Community.query.all():
        c = CommunityIdentify(i.id, i.title)
        data.append(c)
    print('---------------------Data---------------------', data)
    return data


identifier_adminview = dict(
    modelview=IdentifierSettingView,
    model=Identifier,
    category=_('Setting'),
    name=_('Identifier'),
)


__all__ = (
    'pdfcoverpage_adminview',
    'PdfCoverPageSettingView',
    'item_adminview',
    'ItemSettingView',
    'institution_adminview',
    'InstitutionNameSettingView'
)
