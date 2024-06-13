# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for OAI sets."""

from flask_admin.contrib.sqla import ModelView

from .models import OAISet


def _(x):
    """Identity."""
    return x


class OAISetModelView(ModelView):
    """OAISets model view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    column_list = (
        "id",
        "spec",
        "name",
        "updated",
        "created",
    )
    column_details_list = (
        "id",
        "spec",
        "name",
        "description",
        "search_pattern",
        "updated",
        "created",
    )
    column_filters = ("name", "created", "updated")
    column_default_sort = ("updated", True)
    column_searchable_list = ["spec", "name", "description"]
    page_size = 25

    def edit_form(self, obj):
        """Customize edit form."""
        form = super(OAISetModelView, self).edit_form(obj)
        del form.spec
        return form


set_adminview = dict(
    modelview=OAISetModelView,
    model=OAISet,
    category=_("OAI-PMH"),
    name=_("Sets"),
)
