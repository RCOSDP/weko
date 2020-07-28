# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Parent model."""

from invenio_db import db


class Parent(db.Model):
    __tablename__ = 'parent'
    pk = db.Column(db.Integer, primary_key=True)
