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


class ModelThree(db.Model):
    """Test model with just one column."""

    id = db.Column(db.Integer, primary_key=True)
    """Id of the model."""


class ModelThreeModelView(ModelView):
    """AdminModelView of the ModelOne."""

    pass

three = dict(modelview=ModelThreeModelView, model=ModelThree)
