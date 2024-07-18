# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Child model."""

from invenio_db import db

from .parent import Parent


class Child(db.Model):
    """Child demo model."""

    __tablename__ = "child"
    pk = db.Column(db.Integer, primary_key=True)
    fk = db.Column(db.Integer, db.ForeignKey(Parent.pk))
