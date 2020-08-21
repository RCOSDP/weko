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
from uuid import uuid4

from celery.utils.log import get_task_logger
from flask import current_app
from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils.models import Timestamp
from sqlalchemy_utils.types import JSONType

logger = get_task_logger(__name__)


class StatsEvents(db.Model, Timestamp):
    """Database for Stats events."""

    __tablename__ = "stats_events"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    source_id = db.Column(db.String(100))
    op_type = db.Column(db.String(10), nullable=False)
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

    @classmethod
    def __convert_data(cls, event_object):
        if event_object.get("_source"):
            stats_event = StatsEvents(
                source_id=event_object.get("_id"),
                op_type=event_object.get("_op_type"),
                index=event_object.get("_index"),
                type=event_object.get("_type"),
                source=json.dumps(event_object.get("_source")),
            )
            return stats_event
        return None

    @classmethod
    def save(cls, event_object):
        """Save stats event.

        :param event_object:stats event object.
        :return:
        """
        try:
            stats_event = cls.__convert_data(event_object)
            if not stats_event:
                return
            with db.session.begin_nested():
                db.session.add(stats_event)
            db.session.commit()
        except SQLAlchemyError as err:
            current_app.logger.error("Unexpected error: ", err)
            db.session.rollback()
            return False

    @classmethod
    def get_all(cls):
        """Get all stats event.

        :return:
        """
        return db.session.query(cls).all()

    @classmethod
    def get_by_index(cls, _index):
        """Get stats event by event index.

        :param _index: event index
        :return:
        """
        return (
            db.session.query(cls)
            .filter(cls.index.ilike(_index + "%"))
            .all()
        )


class StatsAggregation(db.Model, Timestamp):
    """Database for Stats Aggregation."""

    __tablename__ = "stats_aggregation"

    id = db.Column(db.String(100), primary_key=True)
    source_id = db.Column(db.String(120))
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

    @classmethod
    def __convert_data(cls, aggregation_object):
        if aggregation_object.get("_source"):
            current_time = datetime.utcnow().isoformat()
            stats_agg = StatsAggregation(
                id=str(uuid4())
                + hashlib.sha1(current_time.encode("utf-8")).hexdigest(),
                source_id=aggregation_object.get("_id"),
                index=aggregation_object.get("_index"),
                type=aggregation_object.get("_type"),
                source=json.dumps(aggregation_object.get("_source")),
            )
            return stats_agg
        return None

    @classmethod
    def save(cls, aggregation_object):
        """Save stats aggregation.

        :param aggregation_object: aggregation object
        :return:
        """
        try:
            stats_agg = cls.__convert_data(aggregation_object)
            if not stats_agg:
                return
            with db.session.begin_nested():
                if cls.delete_by_source_id(aggregation_object.get("_id")):
                    db.session.add(stats_agg)
                else:
                    return
            db.session.commit()
        except SQLAlchemyError as err:
            current_app.logger.error("Unexpected error: ", err)
            db.session.rollback()

    @classmethod
    def delete_by_source_id(cls, source_id):
        """Delete stats aggregation by source id.

        :param source_id: source id
        :return:
        """
        try:
            with db.session.begin_nested():
                cls.query.filter_by(source_id=source_id).delete()
            return True
        except SQLAlchemyError as err:
            current_app.logger.error("Unexpected error: ", err)
            db.session.rollback()
            return False

    @classmethod
    def get_all(cls):
        """Get all stats aggregation.

        :return:
        """
        return db.session.query(cls).all()

    @classmethod
    def get_by_index(cls, _index):
        """Get stats aggregation by index.

        :param _index:
        :return:
        """
        return (
            db.session.query(cls)
            .filter(cls.index.ilike(_index + "%"))
            .all()
        )


class StatsBookmark(db.Model, Timestamp):
    """Database for Stats Aggregation."""

    __tablename__ = "stats_bookmark"

    id = db.Column(db.BigInteger(), primary_key=True, autoincrement=True)
    source_id = db.Column(db.String(100), primary_key=True)
    index = db.Column(db.String(100))
    type = db.Column(db.String(50), nullable=False)
    source = db.Column(
        db.JSON()
        .with_variant(postgresql.JSONB(none_as_null=True), "postgresql",)
        .with_variant(JSONType(), "sqlite",)
        .with_variant(JSONType(), "mysql",),
        default=lambda: dict(),
        nullable=True,
    )

    @staticmethod
    def __convert_data(bookmark_objects):
        mappings = []
        for _object in bookmark_objects:
            if _object.get("_source"):
                mappings.append(
                    dict(
                        source_id=_object.get("_id"),
                        index=_object.get("_index"),
                        type=_object.get("_type"),
                        source=json.dumps(_object.get("_source")),
                    )
                )
        return mappings

    @classmethod
    def save(cls, bookmark_objects):
        """Save stats bookmark.

        :param bookmark_objects:
        :return:
        """
        bookmark_data = cls.__convert_data(bookmark_objects)
        if not bookmark_data:
            return
        try:
            with db.session.begin_nested():
                db.session.bulk_insert_mappings(cls, bookmark_data)
            db.session.commit()
        except SQLAlchemyError as err:
            current_app.logger.error("Unexpected error: ", err)
            db.session.rollback()

    @classmethod
    def get_all(cls):
        """Get all stats bookmark.

        :return:
        """
        return db.session.query(cls).all()

    @classmethod
    def get_by_index(cls, _index):
        """Get stats bookmark by index.

        :param _index: index
        :return:
        """
        return (
            db.session.query(cls)
            .filter(cls.index.ilike(_index + "%"))
            .all()
        )


__all__ = [
    "StatsEvents",
    "StatsBookmark",
    "StatsAggregation",
]
