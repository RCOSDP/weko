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
from invenio_db import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types import JSONType
from sqlalchemy.sql import func
from sqlalchemy.dialects import mysql, postgresql

class PDFCoverPageSettings(db.Model):
    __tablename__ = 'pdfcoverpage_set'

    id = db.Column("ID", db.Integer, primary_key=True, autoincrement=True)

    avail = db.Column("Availability", db.Text, nullable=True, default='disable')
    """ PDF Cover Page Availability """

    header_display_type = db.Column("Header Display Type", db.Text, nullable=True, default='string')
    """ Header Display('string' or 'image')"""

    header_output_string = db.Column("Header Output String", db.Text, nullable=True, default='')
    """ Header Output String"""

    header_output_image = db.Column("Header Output Image", db.Text, nullable=True, default='')
    """ Header Output Image"""

    header_display_position = db.Column("Header Display Position", db.Text, nullable=True, default='center')
    """ Header Display Position """

    created_at = db.Column("Created at", db.DateTime, nullable=False, default=datetime.now)
    """ Created Date"""

    updated_at = db.Column("Updated at", db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    """ Updated Date """

    def __init__(self, avail, header_display_type, header_output_string, header_output_image, header_display_position):
        self.avail = avail
        self.header_display_type = header_display_type
        self.header_output_string = header_output_string
        self.header_output_image = header_output_image
        self.header_display_position = header_display_position

    @classmethod
    def find(cls, id):
        """ find record by id"""
        record = db.session.query(cls).filter_by(id=id).first()
        return record

    @classmethod
    def update(cls, id, avail, header_display_type, header_output_string, header_output_image, header_display_position):

        settings = PDFCoverPageSettings(avail, header_display_type, header_output_string, header_output_image, header_display_position)

        """ update record by id"""
        record = db.session.query(cls).filter_by(id=id).first()

        record.avail = settings.avail
        record.header_display_type = settings.header_display_type
        record.header_output_string = settings.header_output_string
        record.header_output_image = settings.header_output_image
        record.header_display_position = settings.header_display_position
        db.session.commit()
        return record

__all__ = (['PDFCoverPageSettings'])
