# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Weko Deposit celery tasks."""

from celery import shared_task
from celery.utils.log import get_task_logger
from elasticsearch.exceptions import TransportError
from flask import current_app
from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy.exc import SQLAlchemyError

from .api import WekoDeposit

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def delete_items_by_id(p_path):
    """
    Delete item Index on ES and update item json column to None.

    :param p_path:

    """
    current_app.logger.debug('index delete task is running.')
    try:
        result = db.session.query(RecordMetadata). filter(
            RecordMetadata.json.op('->>')('path').contains(p_path)).yield_per(1000)
        with db.session.begin_nested():
            for r in result:
                try:
                    WekoDeposit(r.json, r).delete()
                except TransportError:
                    current_app.logger.exception(
                        'Could not deleted index {0}.'.format(result))
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger. \
            exception('Failed to remove items for index delete. err:{0}'.
                      format(e))
        delete_items_by_id.retry(countdown=5, exc=e, max_retries=1)


@shared_task(ignore_result=True)
def update_items_by_id(p_path, target):
    """Update item by id."""
    current_app.logger.debug('index update task is running.')
    try:
        result = db.session.query(RecordMetadata). filter(
            RecordMetadata.json.op('->>')('path').contains(p_path)).yield_per(1000)
        with db.session.begin_nested():
            for r in result:
                obj = WekoDeposit(r.json, r)
                path = obj.get('path')
                if isinstance(path, list):
                    new_path_lst = []
                    for p in path:
                        if p_path in p:
                            p = p.replace(p_path, target)
                            p = p[1:] if p.startswith('/') else p
                            new_path_lst.append(p)
                        else:
                            new_path_lst.append(p)
                    del path
                    obj['path'] = new_path_lst
                obj.update_item_by_task()
                try:
                    obj.indexer.update_path(obj, False)
                except TransportError:
                    current_app.logger.exception(
                        'Could not updated index {0}.'.format(result))
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger. \
            exception('Failed to update items for index update. err:{0}'.
                      format(e))
        update_items_by_id.retry(countdown=5, exc=e, max_retries=1)
