# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.


"""Database models for weko-admin."""

from datetime import datetime

from flask import current_app, json
from flask_babelex import lazy_gettext as _
from invenio_communities.models import Community
from invenio_db import db
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy_utils.types import JSONType

""" PDF cover page model"""


class PDFCoverPageSettings(db.Model):
    """PDF Cover Page Settings."""

    __tablename__ = 'pdfcoverpage_set'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    avail = db.Column(db.Text, nullable=True, default='disable')
    """ PDF Cover Page Availability """

    header_display_type = db.Column(db.Text, nullable=True, default='string')
    """ Header Display('string' or 'image')"""

    header_output_string = db.Column(db.Text, nullable=True, default='')
    """ Header Output String"""

    header_output_image = db.Column(db.Text, nullable=True, default='')
    """ Header Output Image"""

    header_display_position = db.Column(
        db.Text, nullable=True, default='center')
    """ Header Display Position """

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    """ Created Date"""

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now)
    """ Updated Date """

    def __init__(
        self,
        avail,
        header_display_type,
        header_output_string,
        header_output_image,
        header_display_position):
        """Init."""
        self.avail = avail
        self.header_display_type = header_display_type
        self.header_output_string = header_output_string
        self.header_output_image = header_output_image
        self.header_display_position = header_display_position

    @classmethod
    def find(cls, id):
        """Find record by ID."""
        record = db.session.query(cls).filter_by(id=id).first()
        return record

    @classmethod
    def update(
        cls,
        id,
        avail,
        header_display_type,
        header_output_string,
        header_output_image,
        header_display_position):
        """Update."""
        settings = PDFCoverPageSettings(
            avail,
            header_display_type,
            header_output_string,
            header_output_image,
            header_display_position)

        """ update record by ID """
        record = db.session.query(cls).filter_by(id=id).first()

        record.avail = settings.avail
        record.header_display_type = settings.header_display_type
        record.header_output_string = settings.header_output_string
        record.header_output_image = settings.header_output_image
        record.header_display_position = settings.header_display_position
        db.session.commit()
        return record


""" Record UI models """


class InstitutionName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    institution_name = db.Column(db.String(255), default='')

    @classmethod
    def get_institution_name(cls):
        if len(cls.query.all()) < 1:
            db.session.add(cls())
            db.session.commit()
        return cls.query.get(1).institution_name

    @classmethod
    def set_institution_name(cls, new_name):
        cfg = cls.query.get(1)
        cfg.institution_name = new_name
        db.session.commit()

        """ Record UI models """


class FilePermission(db.Model):
    __tablename__ = 'file_permission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    record_id = db.Column(db.Integer)
    file_name = db.Column(db.String(255))
    status = db.Column(db.Integer)
    open_date = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, user_id, record_id, file_name, status):
        self.user_id = user_id
        self.record_id = record_id
        self.file_name = file_name
        self.status = status

    @classmethod
    def find(cls, user_id, record_id, file_name):
        permission = db.session.query(cls).filter_by(user_id=user_id, record_id=record_id, file_name=file_name).first()
        return permission


__all__ = ('PDFCoverPageSettings')
