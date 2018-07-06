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

from .models import Identify

from .api import OaiIdentify


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

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = False
    column_list = ('outPutSetting', 'emails', 'repositoryName', 'earliestDatastamp')
    column_details_list = ('outPutSetting', 'emails', 'repositoryName', 'earliestDatastamp')
    column_labels = dict(
        outPutSetting=_('outPutSet'),
        emails= _('Emails'),
        repositoryName= _('RepositoryName'),
        earliestDatastamp= _('EarliestDatastamp'),
    )
    form_columns = ('outPutSetting', 'emails', 'repositoryName', 'earliestDatastamp')
    page_size = 25


    def edit_form(self, obj):
        """Customize edit form."""
        form = super(IdentifyModelView, self).edit_form(obj)
        return form


    def after_model_change(self,form,Identify,true):
        """Set Create button Hidden"""
        IdentifyModelView.can_create = False


set_OAIPMHview = dict(
    modelview=IdentifyModelView,
    model=Identify,
    category=_('OAI-PMH'),
    name=_('Identify'),
)
