# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Normal and versioned models."""

from invenio_db import db


class UnversionedArticle(db.Model):
    """Unversioned test model."""

    __tablename__ = "unversioned_article_b"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(length=50))


class VersionedArticle(db.Model):
    """Versioned test model."""

    __tablename__ = "versioned_article_b"
    __versioned__ = {}

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(length=50))
