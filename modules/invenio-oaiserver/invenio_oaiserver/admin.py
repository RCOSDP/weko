# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for OAI sets."""

from flask_admin.contrib.sqla import ModelView

from .api import OaiIdentify
from .models import Identify, OAISet


def _(x):
    """Identity."""
    return x


class OAISetModelView(ModelView):
    """OAISets model view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    column_list = ('id', 'spec', 'name', 'updated', 'created',)
    column_details_list = ('id', 'spec', 'name', 'description',
                           'search_pattern', 'updated', 'created')
    column_filters = ('name', 'created', 'updated')
    column_default_sort = ('updated', True)
    column_searchable_list = ['spec', 'name', 'description']
    page_size = 25

    def edit_form(self, obj):
        """Customize edit form."""
        form = super(OAISetModelView, self).edit_form(obj)
        del form.spec
        return form


set_adminview = dict(
    modelview=OAISetModelView,
    model=OAISet,
    category=_('OAI-PMH'),
    name=_('Sets'),
)


class IdentifyModelView(ModelView):
    """OAIPMH model view."""

    can_edit = True
    can_delete = False
    can_view_details = False
    column_list = (
        'outPutSetting',
        'emails',
        'repositoryName',
        'earliestDatastamp')
    column_details_list = (
        'outPutSetting',
        'emails',
        'repositoryName',
        'earliestDatastamp')
    column_labels = dict(
        outPutSetting=_('Output Set'),
        emails=_('Emails'),
        repositoryName=_('Repository Name'),
        earliestDatastamp=_('Earliest Datastamp'),
    )
    form_columns = (
        'outPutSetting',
        'emails',
        'repositoryName',
        'earliestDatastamp')
    page_size = 25

    def edit_form(self, obj):
        """Customize edit form."""
        form = super(IdentifyModelView, self).edit_form(obj)
        return form

    @property
    def can_create(self):
        """Hide create tab if one Identify exists."""
        if Identify.query.filter().first() is not None:
            return False
        return True


set_OAIPMHview = dict(
    modelview=IdentifyModelView,
    model=Identify,
    category=_('OAI-PMH'),
    name=_('Identify'),
)
