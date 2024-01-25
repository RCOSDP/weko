# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for records."""

import json

from flask import abort, current_app, flash, jsonify, redirect, url_for
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_babelex import gettext as _
from invenio_admin.filters import FilterConverter
from invenio_db import db
from markupsafe import Markup
from sqlalchemy.exc import SQLAlchemyError
from weko_records_ui.utils import restore as restore_imp
from weko_records_ui.utils import soft_delete as soft_delete_imp

from .api import Record
from .models import RecordMetadata


class RecordMetadataModelView(ModelView):
    """Records admin model view."""

    @expose('/soft_delete/<string:id>')
    def soft_delete(self, id):
        """Soft delete."""
        try:
            soft_delete_imp(id)
            db.session.commit()
            return jsonify(code=1, msg='PID: ' + str(id) + ' DELETED')
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(ex)
            if ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                    and ex.args[0].get('is_locked'):
                return jsonify(
                    code=-1,
                    is_locked=True,
                    msg=str(ex.args[0].get('msg', ''))
                )
            abort(500)

    @expose('/restore/<string:id>')
    def restore(self, id):
        """Restore."""
        restore_imp(id)
        return redirect(url_for('recordmetadata.details_view') + '?id=' + id)

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    column_list = ('id', 'status', 'version_id', 'updated', 'created')
    column_details_list = ('id', 'status', 'version_id',
                           'updated', 'created', 'json')
    column_sortable_list = ('status', 'version_id', 'updated', 'created')
    column_labels = dict(
        id=_('UUID'),
        version_id=_('Revision'),
        json=_('JSON')
    )
    column_formatters = dict(
        version_id=lambda v, c, m, p: m.version_id - 1,
        json=lambda v, c, m, p: Markup("<pre>{0}</pre>").format(
            json.dumps(m.json, indent=2, sort_keys=True))
    )
    column_filters = ('created', 'updated', )
    column_default_sort = ('updated', True)
    page_size = 25
    details_template = 'invenio_records/details.html'

    def delete_model(self, model):
        """Delete a record."""
        try:
            if model.json is None:
                return True
            record = Record(model.json, model=model)
            record.delete()
            db.session.commit()
        except SQLAlchemyError as e:
            if not self.handle_view_exception(e):
                flash(_('Failed to delete record. %(error)s', error=str(e)),
                      category='error')
            db.session.rollback()
            return False
        return True


record_adminview = dict(
    modelview=RecordMetadataModelView,
    model=RecordMetadata,
    category=_('Records'))
