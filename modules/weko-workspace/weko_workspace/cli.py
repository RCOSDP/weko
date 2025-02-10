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

# import datetime
# import uuid

# import click
# from flask import current_app
# from flask.cli import with_appcontext
# from invenio_db import db
# from sqlalchemy import asc
# from weko_records.api import ItemTypes

# from .models import Action, ActionStatus, ActionStatusPolicy, FlowAction, \
#     FlowDefine, FlowStatusPolicy, WorkFlow


# @click.group()
# def workflow():
#     """Workflow commands."""


# @workflow.command('init')
# @click.argument('tables', default='')
# @with_appcontext
# def init_workflow_tables(tables):
#     """Init workflow tables."""
#     def init_action_status():
#         """Init ActionStatus Table."""
#         db_action_status = list()
#         db_action_status.append(dict(
#             action_status_id=ActionStatusPolicy.ACTION_BEGIN,
#             action_status_name='action_begin',
#             action_status_desc='Indicates that the action has started.',
#             action_scopes='sys',
#             action_displays=''
#         ))
#         db_action_status.append(dict(
#             action_status_id=ActionStatusPolicy.ACTION_DONE,
#             action_status_name='action_done',
#             action_status_desc='Indicates that the action has been completed.',
#             action_scopes='sys,user',
#             action_displays='Complete'
#         ))
#         db_action_status.append(
#             dict(
#                 action_status_id=ActionStatusPolicy.ACTION_NOT_DONE,
#                 action_status_name='action_not_done',
#                 action_status_desc='Indicates that the flow is suspended and\
#                     no subsequent action is performed.',
#                 action_scopes='user',
#                 action_displays='Suspend'))
#         db_action_status.append(
#             dict(
#                 action_status_id=ActionStatusPolicy.ACTION_RETRY,
#                 action_status_name='action_retry',
#                 action_status_desc='Indicates that redo the workflow.\
#                     (from start action)',
#                 action_scopes='user',
#                 action_displays='Redo'))
#         db_action_status.append(
#             dict(
#                 action_status_id=ActionStatusPolicy.ACTION_DOING,
#                 action_status_name='action_doing',
#                 action_status_desc='Indicates that the action is not \
#                     completed.(There are following actions)',
#                 action_scopes='user',
#                 action_displays='Doing'))
#         db_action_status.append(dict(
#             action_status_id=ActionStatusPolicy.ACTION_THROWN_OUT,
#             action_status_name='action_thrown_out',
#             action_status_desc='Indicates that the action has been rejected.',
#             action_scopes='user',
#             action_displays='Reject'
#         ))
#         db_action_status.append(dict(
#             action_status_id=ActionStatusPolicy.ACTION_SKIPPED,
#             action_status_name='action_skipped',
#             action_status_desc='Indicates that the action has been skipped.',
#             action_scopes='user',
#             action_displays='Skip'
#         ))
#         db_action_status.append(dict(
#             action_status_id=ActionStatusPolicy.ACTION_ERROR,
#             action_status_name='action_error',
#             action_status_desc='Indicates that the action has been errored.',
#             action_scopes='user',
#             action_displays='Error'
#         ))
#         db_action_status.append(dict(
#             action_status_id=ActionStatusPolicy.ACTION_CANCELED,
#             action_status_name='action_canceled',
#             action_status_desc='Indicates that the action has been canceled.',
#             action_scopes='user',
#             action_displays='Cancel'
#         ))
#         return db_action_status

#     def init_action():
#         """Init Action Table."""
#         db_action = list()
#         db_action.append(dict(
#             action_name=current_app.config['WEKO_WORKFLOW_ACTION_START'],
#             action_desc='Indicates that the action has started.',
#             action_version='1.0.0',
#             action_endpoint='begin_action',
#             action_makedate=datetime.date(2018, 5, 15),
#             action_lastdate=datetime.date(2018, 5, 15),
#             action_is_need_agree=False
#         ))
#         db_action.append(dict(
#             action_name=current_app.config['WEKO_WORKFLOW_ACTION_END'],
#             action_desc='Indicates that the action has been completed.',
#             action_version='1.0.0',
#             action_endpoint='end_action',
#             action_makedate=datetime.date(2018, 5, 15),
#             action_lastdate=datetime.date(2018, 5, 15),
#             action_is_need_agree=False
#         ))
#         if current_app.config[
#                 'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION']:
#             db_action.append(dict(
#                 action_name=current_app.config[
#                     'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION'],
#                 action_desc='Registering items.',
#                 action_version='1.0.1',
#                 action_endpoint='item_login',
#                 action_makedate=datetime.date(2018, 5, 22),
#                 action_lastdate=datetime.date(2018, 5, 22),
#                 action_is_need_agree=False
#             ))
#         if current_app.config['WEKO_WORKFLOW_ACTION_APPROVAL']:
#             db_action.append(dict(
#                 action_name=current_app.config['WEKO_WORKFLOW_ACTION_APPROVAL'],
#                 action_desc='Approval action for approval requested items.',
#                 action_version='2.0.0',
#                 action_endpoint='approval',
#                 action_makedate=datetime.date(2018, 2, 11),
#                 action_lastdate=datetime.date(2018, 2, 11),
#                 action_is_need_agree=False
#             ))
#         #
#         if current_app.config['WEKO_WORKFLOW_ACTION_ITEM_LINK']:
#             db_action.append(dict(
#                 action_name=current_app.config[
#                     'WEKO_WORKFLOW_ACTION_ITEM_LINK'],
#                 action_desc='Plug-in for link items.',
#                 action_version='1.0.1',
#                 action_endpoint='item_link',
#                 action_makedate=datetime.date(2018, 5, 22),
#                 action_lastdate=datetime.date(2018, 5, 22),
#                 action_is_need_agree=False
#             ))
#         if current_app.config['WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION']:
#             db_action.append(dict(
#                 action_name=current_app.config[
#                     'WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION'],
#                 action_desc='Action for OA Policy confirmation.',
#                 action_version='1.0.0',
#                 action_endpoint='oa_policy',
#                 action_makedate=datetime.date(2019, 3, 15),
#                 action_lastdate=datetime.date(2019, 3, 15),
#                 action_is_need_agree=False
#             ))
#         if current_app.config['WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT']:
#             # Identifier Grant
#             db_action.append(dict(
#                 action_name=current_app.config[
#                     'WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT'],
#                 action_desc='Select DOI issuing organization and CNRI.',
#                 action_version='1.0.0',
#                 action_endpoint='identifier_grant',
#                 action_makedate=datetime.date(2019, 3, 15),
#                 action_lastdate=datetime.date(2019, 3, 15),
#                 action_is_need_agree=False
#             ))
#         if current_app.config[
#                 'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION']:
#             db_action.append(dict(
#                 action_name=current_app.config[
#                     'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION'],
#                 action_desc='Item Registration for Usage Application.',
#                 action_version='1.0.0',
#                 action_endpoint='item_login_application',
#                 action_makedate=datetime.date(2019, 12, 31),
#                 action_lastdate=datetime.date(2019, 12, 31),
#                 action_is_need_agree=True
#             ))
#         if current_app.config['WEKO_WORKFLOW_ACTION_GUARANTOR']:
#             db_action.append(dict(
#                 action_name=current_app.config[
#                     'WEKO_WORKFLOW_ACTION_GUARANTOR'],
#                 action_desc='Approval action performed by Guarantor.',
#                 action_version='1.0.0',
#                 action_endpoint='approval_guarantor',
#                 action_makedate=datetime.date(2019, 12, 31),
#                 action_lastdate=datetime.date(2019, 12, 31),
#                 action_is_need_agree=False
#             ))
#         if current_app.config['WEKO_WORKFLOW_ACTION_ADVISOR']:
#             db_action.append(dict(
#                 action_name=current_app.config['WEKO_WORKFLOW_ACTION_ADVISOR'],
#                 action_desc='Approval action performed by Advisor.',
#                 action_version='1.0.0',
#                 action_endpoint='approval_advisor',
#                 action_makedate=datetime.date(2019, 12, 31),
#                 action_lastdate=datetime.date(2019, 12, 31),
#                 action_is_need_agree=False
#             ))
#         if current_app.config['WEKO_WORKFLOW_ACTION_ADMINISTRATOR']:
#             db_action.append(dict(
#                 action_name=current_app.config[
#                     'WEKO_WORKFLOW_ACTION_ADMINISTRATOR'],
#                 action_desc='Approval action performed by Administrator.',
#                 action_version='1.0.0',
#                 action_endpoint='approval_administrator',
#                 action_makedate=datetime.date(2019, 12, 31),
#                 action_lastdate=datetime.date(2019, 12, 31),
#                 action_is_need_agree=False
#             ))
#         return db_action

#     def init_flow():
#         """Init Flow Table."""
#         db_flow = list()
#         db_flow_action = list()
#         action_list = Action.query.order_by(asc(Action.id)).all()
#         _uuid = uuid.uuid4()
#         db_flow.append(dict(
#             flow_id=_uuid,
#             flow_name='Registration Flow',
#             flow_status=FlowStatusPolicy.AVAILABLE,
#             flow_user=1
#         ))
#         for i, _idx in enumerate([0, 2, 4, 6, 3, 1]):
#             # action.id: [1, 3, 5, 7, 4, 2]
#             db_flow_action.append(dict(
#                 flow_id=_uuid,
#                 action_id=action_list[_idx].id,
#                 action_version=action_list[_idx].action_version,
#                 action_order=(i + 1),
#                 action_condition='',
#                 action_date=datetime.date(2018, 7, 28)
#             ))
#         return db_flow, db_flow_action

#     def init_workflow():
#         """Init WorkFlow Table."""
#         db_workflow = list()
#         flow_list = FlowDefine.query.order_by(asc(FlowDefine.id)).all()
#         itemtypesname_list = ItemTypes.get_latest()
#         db_workflow.append(dict(
#             flows_id=uuid.uuid4(),
#             flows_name='Registration WorkFlow',
#             itemtype_id=itemtypesname_list[0].item_type[0].id,
#             flow_id=flow_list[0].id
#         ))
#         return db_workflow

#     def init_gakuninrdm_data():
#         """Insert flow and action."""
#         gakuninrdm_data = current_app.config.get(
#             'WEKO_WORKFLOW_GAKUNINRDM_DATA')
#         for gakuninrdm in gakuninrdm_data:
#             # Insert flow.
#             flow_name = gakuninrdm.get('flow_name')
#             flow_define = FlowDefine.query.filter_by(
#                 id=gakuninrdm.get('flow_id'),
#                 flow_name=gakuninrdm.get('flow_name')
#             ).one_or_none()
#             if not flow_define:
#                 flow_define = FlowDefine(
#                     id=gakuninrdm.get('flow_id'),
#                     flow_id=uuid.uuid4(),
#                     flow_name=flow_name,
#                     flow_user=1
#                 )
#                 db.session.add(flow_define)
#                 # Insert action.
#                 action_endpoint_list = gakuninrdm.get('action_endpoint_list')
#                 order = 1
#                 for action_endpoint in action_endpoint_list:
#                     action = Action.query.filter_by(
#                         action_endpoint=action_endpoint).one_or_none()
#                     flow_action = FlowAction(
#                         flow_id=flow_define.flow_id,
#                         action_id=action.id,
#                         action_version=action.action_version,
#                         action_order=order
#                     )
#                     db.session.add(flow_action)
#                     order += 1
#             # Insert workflow.
#             workflow = WorkFlow.query.filter_by(
#                 id=gakuninrdm.get('workflow_id'),
#                 flows_name=gakuninrdm.get('workflow_name')
#             ).one_or_none()
#             if not workflow:
#                 workflow = dict(
#                     id=gakuninrdm.get('workflow_id'),
#                     flows_name=gakuninrdm.get('workflow_name'),
#                     itemtype_id=gakuninrdm.get('item_type_id'),
#                     flow_id=flow_define.id,
#                     open_restricted=False,
#                     is_gakuninrdm=True
#                 )
#                 db.session.execute(WorkFlow.__table__.insert(), workflow)

#     if len(tables):
#         try:
#             with db.session.begin_nested():
#                 _tables = tables.split(',')
#                 for table in _tables:
#                     if 'action_status' == table:
#                         db_action_status = init_action_status()
#                         db.session.execute(ActionStatus.__table__.insert(),
#                                            db_action_status)
#                     if 'Action' == table:
#                         db_action = init_action()
#                         db.session.execute(Action.__table__.insert(),
#                                            db_action)
#                     if 'Flow' == table:
#                         db_flow, db_flow_action = init_flow()
#                         db.session.execute(FlowDefine.__table__.insert(),
#                                            db_flow)
#                         db.session.execute(FlowAction.__table__.insert(),
#                                            db_flow_action)
#                     if 'WorkFlow' == table:
#                         db_workflow = init_workflow()
#                         db.session.execute(WorkFlow.__table__.insert(),
#                                            db_workflow)
#                     if 'gakuninrdm_data' == table:
#                         init_gakuninrdm_data()
#             db.session.commit()
#             click.secho('workflow db has been initialised.', fg='green')
#         except BaseException as ex:
#             db.session.rollback()
#             click.secho(str(ex), fg='blue')
#             click.secho('workflow db init failed.', err=ex, fg='red')
