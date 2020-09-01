# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for Invenio-Stats."""
import hashlib
import json
from datetime import datetime
from typing import List
from uuid import uuid4

from celery.utils.log import get_task_logger
from flask import current_app
from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils.models import Timestamp
from sqlalchemy_utils.types import JSONType

logger = get_task_logger(__name__)


class _StataModelBase(Timestamp):
    """Model base."""

    id = db.Column(db.String(100), primary_key=True)
    source_id = db.Column(db.String(100))
    index = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    source = db.Column(
        db.JSON()
        .with_variant(postgresql.JSONB(none_as_null=True), "postgresql",)
        .with_variant(JSONType(), "sqlite",)
        .with_variant(JSONType(), "mysql",),
        default=lambda: dict(),
        nullable=True,
    )
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def get_all(
        cls, start_date: datetime = None, end_date: datetime = None
    ) -> List:
        """Get all stats data.

        :param start_date:
        :param end_date:
        :return:
        """
        query = db.session.query(cls)
        query = cls.get_by_date(query, start_date, end_date)
        return query.all()

    @classmethod
    def get_by_index(
        cls, _index: str, start_date: datetime = None, end_date: datetime = None
    ) -> List:
        """Get stats data by index.

        :param _index: event index
        :param start_date:
        :param end_date:
        :return:
        """
        query = db.session.query(cls)
        query = cls.get_by_date(query, start_date, end_date)
        query = query.filter(cls.index.ilike(_index + "%"))
        return query.all()

    @classmethod
    def get_by_source_id(
        cls, source_id: str, start_date: datetime = None,
        end_date: datetime = None
    ) -> List:
        """Get stats data by source id.

        :param source_id: source id.
        :param start_date:
        :param end_date:
        :return:
        """
        query = db.session.query(cls)
        query = cls.get_by_date(query, start_date, end_date)
        query = query.filter(cls.source_id.ilike(source_id + "%"))
        return query.all()

    @classmethod
    def get_by_date(
        cls, query, start_date: datetime = None, end_date: datetime = None
    ):
        if start_date:
            query = query.filter(cls.date >= start_date)
        if end_date:
            query = query.filter(cls.date <= end_date)
        return query


    @classmethod
    def __convert_data(cls, data_object: dict) -> object:
        if data_object.get("_source"):
            stats_agg = cls(
                id=_generate_id(),
                source_id=data_object.get("_id"),
                index=data_object.get("_index"),
                type=data_object.get("_type"),
                source=json.dumps(data_object.get("_source")),
                date=data_object.get("_source").get("timestamp"),
            )
            return stats_agg
        return None

    @classmethod
    def delete_by_source_id(cls, source_id: str, _index: str) -> bool:
        """Delete stats aggregation by source id.

        :param source_id: source id
        :param _index: index
        :return:
        """
        try:
            with db.session.begin_nested():
                db.session.query(cls).filter_by(
                    source_id=source_id,
                    index=_index
                ).delete()
            return True
        except SQLAlchemyError as err:
            current_app.logger.error("Unexpected error: ", err)
            db.session.rollback()
            return False

    @classmethod
    def save(cls, data_object: dict, delete: bool = False) -> bool:
        """Save stats event.

        :param data_object:stats event object.
        :param delete:
        :return:
        """
        try:
            stats_data = cls.__convert_data(data_object)
            if not stats_data:
                return False
            with db.session.begin_nested():
                if delete:
                    if cls.delete_by_source_id(data_object.get("_id"),
                                               data_object.get("_index")):
                        db.session.add(stats_data)
                    else:
                        return False
                else:
                    db.session.add(stats_data)
            db.session.commit()
            return True
        except SQLAlchemyError as err:
            current_app.logger.error("Unexpected error: ", err)
            db.session.rollback()
            return False


class StatsEvents(db.Model, _StataModelBase):
    """Database for Stats events."""

    __tablename__ = "stats_events"


class StatsAggregation(db.Model, _StataModelBase):
    """Database for Stats Aggregation."""

    __tablename__ = "stats_aggregation"


class StatsBookmark(db.Model, _StataModelBase):
    """Database for Stats Bookmark."""

    __tablename__ = "stats_bookmark"


def _generate_id():
    """Generate identifier.

    :return:
    """
    current_time = datetime.utcnow().isoformat()
    return str(uuid4()) + hashlib.sha1(current_time.encode("utf-8")).hexdigest()


__all__ = [
    "StatsEvents",
    "StatsBookmark",
    "StatsAggregation",
]
