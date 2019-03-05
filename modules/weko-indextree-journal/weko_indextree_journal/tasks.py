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

"""Weko Journal celery tasks."""

from celery import shared_task
from celery.utils.log import get_task_logger
from .api import WekoDeposit
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from elasticsearch.exceptions import TransportError

logger = get_task_logger(__name__)

print("[Log]: Register journal tasks.")
@shared_task(ignore_result=True)
def export_journal_task(p_path):
    """
    Delete item Index on ES and update item json column to None
    :param p_path:
    """
    current_app.logger.debug('export journal tasks.')
    print("export journal tasks")
    print("p_path: ")
    print(p_path)