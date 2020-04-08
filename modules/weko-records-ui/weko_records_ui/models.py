# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.


"""Database models for weko-admin."""

from datetime import datetime

from flask import current_app, json
from flask_babelex import lazy_gettext as _
from invenio_communities.models import Community
from invenio_db import db
from sqlalchemy import desc
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
    """File download permission."""

    __tablename__ = 'file_permission'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    """Id."""

    user_id = db.Column(db.Integer, nullable=False)
    """User Id."""

    record_id = db.Column(db.String(255), nullable=False)
    """Record id."""

    file_name = db.Column(db.String(255), nullable=False)
    """File name."""

    usage_application_activity_id = db.Column(db.String(255), nullable=False)
    """Usage Application Activity id."""

    status = db.Column(db.Integer, nullable=False)
    """Status of the permission."""
    """-1 : Initialized, 0 : Processing, 1: Approved."""

    open_date = db.Column(db.DateTime, nullable=False, default=datetime.now())

    def __init__(self, user_id, record_id, file_name,
                 usage_application_activity_id, status):
        """Init."""
        self.user_id = user_id
        self.record_id = record_id
        self.file_name = file_name
        self.usage_application_activity_id = usage_application_activity_id
        self.status = status

    @classmethod
    def find(cls, user_id, record_id, file_name):
        """Find user 's permission by user_id, record_id, file_name."""
        permission = db.session.query(cls).filter_by(user_id=user_id,
                                                     record_id=record_id,
                                                     file_name=file_name)\
            .first()
        return permission

    @classmethod
    def find_list_permission_by_date(cls, user_id, record_id, file_name,
                                     duration):
        list_permission = db.session.query(cls).filter(
            cls.open_date >= duration).filter_by(user_id=user_id,
                                                 record_id=record_id,
                                                 file_name=file_name).order_by(
            desc(cls.id)).all()
        return list_permission

    @classmethod
    def init_file_permission(cls, user_id, record_id, file_name, activity_id):
        """Init a file permission with status = Doing."""
        status_initialized = -1
        file_permission = FilePermission(user_id, record_id, file_name,
                                         activity_id, status_initialized)
        db.session.add(file_permission)
        db.session.commit()
        return cls

    @classmethod
    def update_status(cls, permission, status):
        """Update a permission 's status."""
        permission.status = status
        db.session.merge(permission)
        db.session.commit()
        return permission

    @classmethod
    def update_open_date(cls, permission, open_date):
        """Update a permission 's open date."""
        permission.open_date = open_date
        db.session.merge(permission)
        db.session.commit()
        return permission

    @classmethod
    def find_by_activity(cls, activity_id):
        """Find user 's permission activity id."""
        permission = db.session.query(cls).filter_by(
            usage_application_activity_id=activity_id) \
            .first()
        return permission


__all__ = ('PDFCoverPageSettings')
