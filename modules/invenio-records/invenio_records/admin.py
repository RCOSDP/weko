# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for records."""

import json

from flask import flash
from flask_admin.contrib.sqla import ModelView
from invenio_admin.filters import FilterConverter
from invenio_db import db
from invenio_i18n import gettext as _
from markupsafe import Markup
from sqlalchemy.exc import SQLAlchemyError

from .api import Record
from .models import RecordMetadata


class RecordMetadataModelView(ModelView):
    """Records admin model view."""

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    column_list = (
        "id",
        "version_id",
        "updated",
        "created",
    )
    column_details_list = ("id", "version_id", "updated", "created", "json")
    column_labels = dict(
        id=_("UUID"),
        version_id=_("Revision"),
        json=_("JSON"),
    )
    column_formatters = dict(
        version_id=lambda v, c, m, p: m.version_id - 1,
        json=lambda v, c, m, p: Markup("<pre>{0}</pre>").format(
            json.dumps(m.json, indent=2, sort_keys=True)
        ),
    )
    column_filters = (
        "created",
        "updated",
    )
    column_default_sort = ("updated", True)
    page_size = 25

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
                flash(
                    _("Failed to delete record. {error}").format(error=str(e)),
                    category="error",
                )
            db.session.rollback()
            return False
        return True


record_adminview = dict(
    modelview=RecordMetadataModelView, model=RecordMetadata, category=_("Records")
)
