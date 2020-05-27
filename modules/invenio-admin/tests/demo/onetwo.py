# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Mocks of DB Models and Admin's ModelViews for entrypoint testing."""

from flask_admin.contrib.sqla import ModelView
from invenio_db import db


class ModelOne(db.Model):
    """Test model with just one column."""

    id = db.Column(db.Integer, primary_key=True)
    """Id of the model."""


class ModelTwo(db.Model):
    """Test model with just one column."""

    id = db.Column(db.Integer, primary_key=True)
    """Id of the model."""


class ModelOneModelView(ModelView):
    """AdminModelView of the ModelOne."""

    pass


class ModelTwoModelView(ModelView):
    """AdminModelView of the ModelTwo."""

    pass

# Invalid admin entry point:
zero = {}

# Old deprecated way of specifying admin entry points:
one = dict(
    modelview=ModelOneModelView,
    model=ModelOne,
    category='OneAndTwo'
)
# New way of specifying admin entry points:
two = dict(
    view_class=ModelTwoModelView,
    args=[ModelTwo, db.session],
    kwargs=dict(category='OneAndTwo')
 )
