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

"""WEKO3 module docstring."""
import datetime
import json
import os
import shutil
import ssl
import sys
import tempfile
import traceback

from flask import current_app, request, send_file
from invenio_communities.models import Community
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError
from weko_index_tree.api import Indexes

from .config import INVENIO_RESYNC_SAVE_PATH
from .models import ResyncIndexes, ResyncLogs

ssl._create_default_https_context = ssl._create_unverified_context


class ResyncHandler(object):
    """Define API for ResyncIndexes creation and update."""

    def __init__(self, **kwargs):
        """Add extra options."""
        self.id = kwargs.get('id')
        self.status = kwargs.get('status')
        self.repository_name = kwargs.get('repository_name')
        self.index_id = kwargs.get('index_id')
        self.base_url = kwargs.get('base_url')
        self.created = kwargs.get('created')
        self.from_date = kwargs.get('from_date', datetime.datetime.now())
        self.to_date = kwargs.get('to_date', datetime.datetime.now())
        self.updated = kwargs.get('updated')
        self.resync_save_dir = kwargs.get('resync_save_dir')
        self.resync_mode = kwargs.get('resync_mode')
        self.saving_format = kwargs.get('saving_format')
        self.interval_by_day = kwargs.get('interval_by_day')
        self.task_id = kwargs.get('task_id')
        self.is_running = kwargs.get('is_running')
        self.result = kwargs.get('result')
        self.index = kwargs.get('index') or self.get_index()

    def get_index(self):
        """Get Index obj relate to repository_id."""
        if self.index_id:
            return Indexes.get_index(self.index_id)
        else:
            return None

    def to_dict(self):
        """Generate Resource Object to Dict."""
        index_name = self.index.index_name_english

        return dict(**{
            'id': self.id,
            'status': self.status,
            'repository_name': self.repository_name,
            'index_id': self.index_id,
            'base_url': self.base_url,
            'index_name': index_name,
            'created': self.created,
            'from_date': self.from_date if self.from_date else None,
            'to_date': self.to_date if self.to_date else None,
            'updated': self.updated,
            'resync_save_dir': self.resync_save_dir,
            'resync_mode': self.resync_mode,
            'saving_format': self.saving_format,
            'interval_by_day': self.interval_by_day,
            'result': self.result,
            'task_id': self.task_id,
            'is_running': self.is_running,
        })

    def create(self):
        """Create resync item."""
        validate = self.validate()
        if not validate.get('validate'):
            return {
                'success': False,
                'errmsg': validate.get("errmsg")
            }
        try:
            with db.session.begin_nested():
                new_data = self.to_dict()
                new_data.pop('index_name')
                new_data.pop('created')
                new_data.pop('updated')
                resync = ResyncIndexes(**new_data)
                db.session.add(resync)
            db.session.commit()
            return ResyncHandler.from_modal(resync).update({
                'resync_save_dir': '{0}{1}'.format(
                    current_app.config.get(
                        'INVENIO_RESYNC_SAVE_PATH',
                        INVENIO_RESYNC_SAVE_PATH
                    ), resync.id)
            })
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return {
                'success': False,
                'errmsg': [str(ex)]
            }

    def update(self, data={}):
        """
        Update the resync detail info.

        :return: Updated resync info
        """
        current_app.logger.debug(
            '[{0}] [{1}] START'.format(0, 'ResyncHandler.update'))
        validate = self.validate()
        current_app.logger.debug('[{0}] [{1}] validate: {2}'.format(
            0, 'ResyncHandler.update', validate))
        if not validate.get('validate'):
            return {
                'success': False,
                'errmsg': validate.get('errmsg')
            }
        try:
            with db.session.begin_nested():
                resync = self.get_resync(self.id, 'modal')
                if not resync:
                    return {
                        'success': False,
                        'errmsg': ['']
                    }
                resync.repository_name = data.get(
                    "repository_name",
                    resync.repository_name
                )
                resync.index_id = data.get(
                    "index_id",
                    resync.index_id
                )
                resync.base_url = data.get(
                    "base_url",
                    resync.base_url
                )
                resync.status = data.get(
                    "status",
                    resync.status
                )
                resync.interval_by_day = data.get(
                    "interval_by_day",
                    resync.interval_by_day
                )
                resync.resync_mode = data.get(
                    "resync_mode",
                    resync.resync_mode
                )
                resync.saving_format = data.get(
                    "saving_format",
                    resync.saving_format
                )
                resync.from_date = data.get(
                    "from_date",
                ) or resync.from_date
                resync.to_date = data.get(
                    "to_date",
                ) or resync.to_date
                resync.task_id = data.get(
                    "task_id",
                    resync.task_id
                )
                resync.is_running = data.get(
                    "is_running",
                    resync.is_running
                )
                resync.result = data.get(
                    "result",
                    resync.result
                )
                resync.resync_save_dir = data.get(
                    "resync_save_dir",
                    resync.resync_save_dir
                )

                db.session.merge(resync)
            db.session.commit()
            current_app.logger.debug(
                '[{0}] [{1}] END'.format(0, 'ResyncHandler.update'))
            return {
                'success': True,
                'data': ResyncHandler.from_modal(resync).to_dict()
            }
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return {
                'success': False,
                'message': [str(ex)]
            }

    def validate(self):
        """Validate resync item."""
        # check required

        result = []
        if not self.repository_name:
            result.append("Repository is required")
        if not self.index_id:
            result.append("Target Index is required")
        if not self.base_url:
            result.append("Base Url is required")

        if len(result):
            return {
                'validate': False,
                'errmsg': result
            }
        else:
            return {
                'validate': True,
            }

    @classmethod
    def from_modal(cls, resync):
        """Parse ResyncIndexes to ResyncHandler item."""
        return ResyncHandler(
            id=resync.id,
            status=resync.status,
            repository_name=resync.repository_name,
            index_id=resync.index_id,
            base_url=resync.base_url,
            created=resync.created,
            from_date=resync.from_date,
            to_date=resync.to_date,
            updated=resync.updated,
            resync_save_dir=resync.resync_save_dir,
            resync_mode=resync.resync_mode,
            saving_format=resync.saving_format,
            interval_by_day=resync.interval_by_day,
            task_id=resync.task_id,
            result=resync.result,
            is_running=resync.is_running,
        )

    def delete(self):
        """
        Update the index detail info.

        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                resync = self.get_resync(self.id, 'modal')
                if not resync:
                    return {
                        'success': False,
                        'errmsg': ['Resync is not exist']
                    }
                db.session.delete(resync)
            db.session.commit()
            return {
                'success': True
            }
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return {
                'success': False,
                'errmsg': [str(ex)]
            }

    @classmethod
    def get_resync(cls, resync_id, type_result='obj'):
        """
        Update the index detail info.

        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                resync = db.session.query(ResyncIndexes).filter(
                    ResyncIndexes.id == resync_id).one_or_none()

                if type_result == 'obj':
                    return ResyncHandler.from_modal(resync)
                else:
                    return resync
        except Exception as ex:
            current_app.logger.debug(ex)
            return False

    @classmethod
    def get_list_resync(cls, type_result='obj',user=None):
        """
        Update the index detail info.

        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                if not user:
                    resyncs = db.session.query(ResyncIndexes).filter().order_by(db.asc(ResyncIndexes.id)).all()
                else:
                    is_super = any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in user.roles)
                    if is_super:
                        resyncs = db.session.query(ResyncIndexes).filter().order_by(db.asc(ResyncIndexes.id)).all()
                    else:
                        index_list = []
                        repositories = Community.get_repositories_by_user(user)
                        for repository in repositories:
                            index = Indexes.get_child_list_recursive(repository.root_node_id)
                            index_list.extend(index)
                        resyncs = db.session.query(ResyncIndexes).filter(ResyncIndexes.index_id.in_(index_list)).order_by(db.asc(ResyncIndexes.id)).all()

                if type_result == 'obj':
                    return [ResyncHandler.from_modal(res) for res in resyncs]
                else:
                    return resyncs
        except Exception as ex:
            current_app.logger.debug(ex)
            return False

    def get_logs(self):
        """Get logs."""
        try:
            with db.session.begin_nested():
                resync_logs = db.session.query(ResyncLogs).filter_by(
                    resync_indexes_id=int(self.id)
                ).order_by(db.desc(ResyncLogs.id)).all()
                result = [dict(**{
                    "id": logs.id,
                    "start_time": logs.start_time.strftime(
                        '%Y-%m-%dT%H:%M:%S%z'
                    ) if logs.start_time else '',
                    "end_time": logs.end_time.strftime(
                        '%Y-%m-%dT%H:%M:%S%z'
                    ) if logs.end_time else '',
                    "status": logs.status,
                    "errmsg": logs.errmsg,
                    "counter": logs.counter,
                    "log_type": logs.log_type,
                }) for logs in resync_logs]
                return result
        except Exception as ex:
            current_app.logger.debug(ex)
            return False
