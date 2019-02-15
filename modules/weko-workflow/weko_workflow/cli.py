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

import click
import datetime
import uuid
from flask.cli import with_appcontext
from sqlalchemy import asc
from invenio_db import db

from weko_records.api import ItemTypes

from .models import ActionStatus, Action, ActionStatusPolicy, FlowDefine, \
    FlowAction, FlowStatusPolicy, WorkFlow


@click.group()
def workflow():
    """workflow commands."""


@workflow.command('init')
@click.argument('tables', default='')
@with_appcontext
def init_workflow_tables(tables):
    """
    Init workflow tables.
    """
    def init_action_status():
        """Init ActionStatus Table"""
        db_action_status = list()
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_BEGIN,
            action_status_name='action_begin',
            action_status_desc='Indicates that the action has started.',
            action_scopes='sys',
            action_displays=''
        ))
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_DONE,
            action_status_name='action_done',
            action_status_desc='Indicates that the action has been completed.',
            action_scopes='sys,user',
            action_displays='Complete'
        ))
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_NOT_DONE,
            action_status_name='action_not_done',
            action_status_desc='Indicates that the flow is suspended and no subsequent action is performed.',
            action_scopes='user',
            action_displays='Suspend'
        ))
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_RETRY,
            action_status_name='action_retry',
            action_status_desc='Indicates that redo the workflow.(from start action)',
            action_scopes='user',
            action_displays='Redo'
        ))
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_DOING,
            action_status_name='action_doing',
            action_status_desc='Indicates that the action is not completed.(There are following actions)',
            action_scopes='user',
            action_displays='Doing'
        ))
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_THROWN_OUT,
            action_status_name='action_thrown_out',
            action_status_desc='Indicates that the action has been rejected.',
            action_scopes='user',
            action_displays='Reject'
        ))
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_SKIPPED,
            action_status_name='action_skipped',
            action_status_desc='Indicates that the action has been skipped.',
            action_scopes='user',
            action_displays='Skip'
        ))
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_ERROR,
            action_status_name='action_error',
            action_status_desc='Indicates that the action has been errored.',
            action_scopes='user',
            action_displays='Error'
        ))
        return db_action_status

    def init_action():
        """Init Action Table"""
        db_action = list()
        db_action.append(dict(
            action_name='Start',
            action_desc='Indicates that the action has started.',
            action_version='1.0.0',
            action_endpoint='begin_action',
            action_makedate=datetime.date(2018, 5, 15),
            action_lastdate=datetime.date(2018, 5, 15)
        ))
        db_action.append(dict(
            action_name='End',
            action_desc='Indicates that the action has been completed.',
            action_version='1.0.0',
            action_endpoint='end_action',
            action_makedate=datetime.date(2018, 5, 15),
            action_lastdate=datetime.date(2018, 5, 15)
        ))
        db_action.append(dict(
            action_name='Duplicate Check',
            action_desc='Confirm duplicate registration of items.',
            action_version='1.0.0',
            action_endpoint='double_check',
            action_makedate=datetime.date(2018, 5, 15),
            action_lastdate=datetime.date(2018, 5, 15)
        ))
        db_action.append(dict(
            action_name='Item Registration',
            action_desc='Plug-in for registering items.',
            action_version='1.0.1',
            action_endpoint='item_login',
            action_makedate=datetime.date(2018, 5, 22),
            action_lastdate=datetime.date(2018, 5, 22)
        ))
        db_action.append(dict(
            action_name='Content Upload',
            action_desc='Action for uploading item content.',
            action_version='1.2.1',
            action_endpoint='file_upload',
            action_makedate=datetime.date(2018, 4, 22),
            action_lastdate=datetime.date(2018, 4, 22)
        ))
        db_action.append(dict(
            action_name='Approval Request',
            action_desc='Establish an approver for items and get approval.',
            action_version='1.1.1',
            action_endpoint='approval_request',
            action_makedate=datetime.date(2018, 6, 11),
            action_lastdate=datetime.date(2018, 6, 11)
        ))
        db_action.append(dict(
            action_name='Approval',
            action_desc='Approval action for approval requested items.',
            action_version='2.0.0',
            action_endpoint='approval',
            action_makedate=datetime.date(2018, 2, 11),
            action_lastdate=datetime.date(2018, 2, 11)
        ))
        db_action.append(dict(
            action_name='Via Review',
            action_desc='Supports via review for items.',
            action_version='1.1.2',
            action_endpoint='review_action',
            action_makedate=datetime.date(2018, 6, 8),
            action_lastdate=datetime.date(2018, 6, 8)
        ))
        #
        db_action.append(dict(
            action_name='Item Link',
            action_desc='Plug-in for link items.',
            action_version='1.0.1',
            action_endpoint='item_link',
            action_makedate=datetime.date(2018, 5, 22),
            action_lastdate=datetime.date(2018, 5, 22)
        ))
        #
        return db_action

    def init_flow():
        """Init Flow Table"""
        db_flow = list()
        db_flow_action = list()
        action_list = Action.query.order_by(asc(Action.id)).all()
        _uuid = uuid.uuid4()
        db_flow.append(dict(
            flow_id=_uuid,
            flow_name='Registration Flow',
            flow_status=FlowStatusPolicy.AVAILABLE,
            flow_user=1
        ))
        for i, _idx in enumerate([0, 1, 3, 4]):
            """action.id: [1, 2, 4, 5]"""
            db_flow_action.append(dict(
                flow_id=_uuid,
                action_id=action_list[_idx].id,
                action_version=action_list[_idx].action_version,
                action_order=(i+1),
                action_condition='',
                action_date=datetime.date(2018, 7, 28)
            ))
        _uuid = uuid.uuid4()
        db_flow.append(dict(
            flow_id=_uuid,
            flow_name='Registration Approval Flow',
            flow_status=FlowStatusPolicy.AVAILABLE,
            flow_user=1
        ))
        for i, _idx in enumerate([1, 3, 4]):
            """action.id: [2, 4, 5]"""
            db_flow_action.append(dict(
                flow_id=_uuid,
                action_id=action_list[_idx].id,
                action_version=action_list[_idx].action_version,
                action_order=(i+1),
                action_condition='',
                action_date=datetime.date(2018, 8, 5)
            ))
        _uuid = uuid.uuid4()
        db_flow.append(dict(
            flow_id=_uuid,
            flow_name='Metadata Addition Flow',
            flow_status=FlowStatusPolicy.AVAILABLE,
            flow_user=1
        ))
        for i, _idx in enumerate([1, 2, 3, 4, 5]):
            """action.id: [2, 3, 4, 5, 6]"""
            db_flow_action.append(dict(
                flow_id=_uuid,
                action_id=action_list[_idx].id,
                action_version=action_list[_idx].action_version,
                action_order=(i+1),
                action_condition='',
                action_date=datetime.date(2018, 8, 7)
            ))
        return db_flow, db_flow_action

    def init_workflow():
        """Init WorkFlow Table"""
        db_workflow = list()
        flow_list = FlowDefine.query.order_by(asc(FlowDefine.id)).all()
        itemtypesname_list = ItemTypes.get_latest()
        db_workflow.append(dict(
            flows_id=uuid.uuid4(),
            flows_name='Article Registration Flow',
            itemtype_id=itemtypesname_list[0].item_type[0].id,
            flow_id=flow_list[0].id
        ))
        db_workflow.append(dict(
            flows_id=uuid.uuid4(),
            flows_name='Report Registration Flow',
            itemtype_id=itemtypesname_list[1].item_type[0].id,
            flow_id=flow_list[1].id
        ))
        db_workflow.append(dict(
            flows_id=uuid.uuid4(),
            flows_name='Metadata Addition Flow',
            itemtype_id=itemtypesname_list[2].item_type[0].id,
            flow_id=flow_list[2].id
        ))
        return db_workflow

    if len(tables):
        try:
            with db.session.begin_nested():
                _tables = tables.split(',')
                for table in _tables:
                    if 'action_status' == table:
                        db_action_status = init_action_status()
                        db.session.execute(ActionStatus.__table__.insert(),
                                           db_action_status)
                    if 'Action' == table:
                        db_action = init_action()
                        db.session.execute(Action.__table__.insert(),
                                           db_action)
                    if 'Flow' == table:
                        db_flow, db_flow_action = init_flow()
                        db.session.execute(FlowDefine.__table__.insert(),
                                           db_flow)
                        db.session.execute(FlowAction.__table__.insert(),
                                           db_flow_action)
                    if 'WorkFlow' == table:
                        db_workflow = init_workflow()
                        db.session.execute(WorkFlow.__table__.insert(),
                                           db_workflow)
        except BaseException as ex:
            db.session.rollback()
            click.secho(str(ex), fg='blue')
            click.secho('workflow db init failed.', err=ex, fg='red')
        else:
            db.session.commit()
            click.secho('workflow db has been initialised.', fg='green')
