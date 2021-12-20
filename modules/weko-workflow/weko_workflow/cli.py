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
import numbers
import uuid

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy import asc
from weko_records.api import ItemTypes
from weko_records.models import ItemMetadata, ItemType

from .models import Action, ActionStatus, ActionStatusPolicy, FlowAction, \
    FlowDefine, FlowStatusPolicy, WorkFlow


@click.group()
def workflow():
    """Workflow commands."""


@workflow.command('init')
@click.argument('tables', default='')
@with_appcontext
def init_workflow_tables(tables):
    """Init workflow tables."""
    def init_action_status():
        """Init ActionStatus Table."""
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
        db_action_status.append(
            dict(
                action_status_id=ActionStatusPolicy.ACTION_NOT_DONE,
                action_status_name='action_not_done',
                action_status_desc='Indicates that the flow is suspended and\
                    no subsequent action is performed.',
                action_scopes='user',
                action_displays='Suspend'))
        db_action_status.append(
            dict(
                action_status_id=ActionStatusPolicy.ACTION_RETRY,
                action_status_name='action_retry',
                action_status_desc='Indicates that redo the workflow.\
                    (from start action)',
                action_scopes='user',
                action_displays='Redo'))
        db_action_status.append(
            dict(
                action_status_id=ActionStatusPolicy.ACTION_DOING,
                action_status_name='action_doing',
                action_status_desc='Indicates that the action is not \
                    completed.(There are following actions)',
                action_scopes='user',
                action_displays='Doing'))
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
        db_action_status.append(dict(
            action_status_id=ActionStatusPolicy.ACTION_CANCELED,
            action_status_name='action_canceled',
            action_status_desc='Indicates that the action has been canceled.',
            action_scopes='user',
            action_displays='Cancel'
        ))
        return db_action_status

    def init_action():
        """Init Action Table."""
        db_action = list()
        db_action.append(dict(
            action_name=current_app.config['WEKO_WORKFLOW_ACTION_START'],
            action_desc='Indicates that the action has started.',
            action_version='1.0.0',
            action_endpoint='begin_action',
            action_makedate=datetime.date(2018, 5, 15),
            action_lastdate=datetime.date(2018, 5, 15),
            action_is_need_agree=False
        ))
        db_action.append(dict(
            action_name=current_app.config['WEKO_WORKFLOW_ACTION_END'],
            action_desc='Indicates that the action has been completed.',
            action_version='1.0.0',
            action_endpoint='end_action',
            action_makedate=datetime.date(2018, 5, 15),
            action_lastdate=datetime.date(2018, 5, 15),
            action_is_need_agree=False
        ))
        if current_app.config[
                'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION']:
            db_action.append(dict(
                action_name=current_app.config[
                    'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION'],
                action_desc='Registering items.',
                action_version='1.0.1',
                action_endpoint='item_login',
                action_makedate=datetime.date(2018, 5, 22),
                action_lastdate=datetime.date(2018, 5, 22),
                action_is_need_agree=False
            ))
        if current_app.config['WEKO_WORKFLOW_ACTION_APPROVAL']:
            db_action.append(dict(
                action_name=current_app.config['WEKO_WORKFLOW_ACTION_APPROVAL'],
                action_desc='Approval action for approval requested items.',
                action_version='2.0.0',
                action_endpoint='approval',
                action_makedate=datetime.date(2018, 2, 11),
                action_lastdate=datetime.date(2018, 2, 11),
                action_is_need_agree=False
            ))
        #
        if current_app.config['WEKO_WORKFLOW_ACTION_ITEM_LINK']:
            db_action.append(dict(
                action_name=current_app.config[
                    'WEKO_WORKFLOW_ACTION_ITEM_LINK'],
                action_desc='Plug-in for link items.',
                action_version='1.0.1',
                action_endpoint='item_link',
                action_makedate=datetime.date(2018, 5, 22),
                action_lastdate=datetime.date(2018, 5, 22),
                action_is_need_agree=False
            ))
        if current_app.config['WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION']:
            db_action.append(dict(
                action_name=current_app.config[
                    'WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION'],
                action_desc='Action for OA Policy confirmation.',
                action_version='1.0.0',
                action_endpoint='oa_policy',
                action_makedate=datetime.date(2019, 3, 15),
                action_lastdate=datetime.date(2019, 3, 15),
                action_is_need_agree=False
            ))
        if current_app.config['WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT']:
            # Identifier Grant
            db_action.append(dict(
                action_name=current_app.config[
                    'WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT'],
                action_desc='Select DOI issuing organization and CNRI.',
                action_version='1.0.0',
                action_endpoint='identifier_grant',
                action_makedate=datetime.date(2019, 3, 15),
                action_lastdate=datetime.date(2019, 3, 15),
                action_is_need_agree=False
            ))
        if current_app.config[
                'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION']:
            db_action.append(dict(
                action_name=current_app.config[
                    'WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION'],
                action_desc='Item Registration for Usage Application.',
                action_version='1.0.0',
                action_endpoint='item_login_application',
                action_makedate=datetime.date(2019, 12, 31),
                action_lastdate=datetime.date(2019, 12, 31),
                action_is_need_agree=True
            ))
        if current_app.config['WEKO_WORKFLOW_ACTION_GUARANTOR']:
            db_action.append(dict(
                action_name=current_app.config[
                    'WEKO_WORKFLOW_ACTION_GUARANTOR'],
                action_desc='Approval action performed by Guarantor.',
                action_version='1.0.0',
                action_endpoint='approval_guarantor',
                action_makedate=datetime.date(2019, 12, 31),
                action_lastdate=datetime.date(2019, 12, 31),
                action_is_need_agree=False
            ))
        if current_app.config['WEKO_WORKFLOW_ACTION_ADVISOR']:
            db_action.append(dict(
                action_name=current_app.config['WEKO_WORKFLOW_ACTION_ADVISOR'],
                action_desc='Approval action performed by Advisor.',
                action_version='1.0.0',
                action_endpoint='approval_advisor',
                action_makedate=datetime.date(2019, 12, 31),
                action_lastdate=datetime.date(2019, 12, 31),
                action_is_need_agree=False
            ))
        if current_app.config['WEKO_WORKFLOW_ACTION_ADMINISTRATOR']:
            db_action.append(dict(
                action_name=current_app.config[
                    'WEKO_WORKFLOW_ACTION_ADMINISTRATOR'],
                action_desc='Approval action performed by Administrator.',
                action_version='1.0.0',
                action_endpoint='approval_administrator',
                action_makedate=datetime.date(2019, 12, 31),
                action_lastdate=datetime.date(2019, 12, 31),
                action_is_need_agree=False
            ))
        return db_action

    def init_flow():
        """Init Flow Table."""
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
        for i, _idx in enumerate([0, 2, 4, 6, 3, 1]):
            # action.id: [1, 3, 5, 7, 4, 2]
            db_flow_action.append(dict(
                flow_id=_uuid,
                action_id=action_list[_idx].id,
                action_version=action_list[_idx].action_version,
                action_order=(i + 1),
                action_condition='',
                action_date=datetime.date(2018, 7, 28)
            ))
        return db_flow, db_flow_action

    def init_workflow():
        """Init WorkFlow Table."""
        db_workflow = list()
        flow_list = FlowDefine.query.order_by(asc(FlowDefine.id)).all()
        itemtypesname_list = ItemTypes.get_latest()
        db_workflow.append(dict(
            flows_id=uuid.uuid4(),
            flows_name='Registration WorkFlow',
            itemtype_id=itemtypesname_list[0].item_type[0].id,
            flow_id=flow_list[0].id
        ))
        return db_workflow

    def update_incorrect_metadata():
        """Check consistency and update metadata."""
        def get_all_item_type():
            """Get all item type in DB."""
            return ItemType.query.all() or []

        def get_item_meta_by_item_type_id(_id):
            """Get all item metadata by item type id."""
            return ItemMetadata.query.filter_by(item_type_id=_id).all() or []

        def get_record_meta_by_item_meta_id(_id):
            return RecordMetadata.query.filter_by(id=_id).one()

        def get_item_type_form_keys(_keys, _forms):
            """Get all keys in form of item type."""
            for form in _forms:
                if not form.get('items'):
                    replaced_key = form.get('key', '').replace('[]', '')
                    temp_keys = replaced_key.split('.')
                    temp_key = temp_keys[0] if len(temp_keys) == 1 \
                        else '{}.{}'.format(temp_keys[0], temp_keys[1])
                    _keys.append(temp_key)
                else:
                    get_item_type_form_keys(_keys, form.get('items'))
            return _keys

        def iterate_all(_keys, _iterable, parent_key=''):
            """Get all keys of json metadata."""
            parent_key = parent_key.replace('.attribute_value_mlt', '')
            if isinstance(_iterable, dict):
                for key, value in _iterable.items():
                    if isinstance(value, (str, numbers.Number)) \
                            and key != 'attribute_name':
                        if parent_key:
                            _keys.append('{}.{}'.format(parent_key, key))
                        else:
                            _keys.append(key)
                    if isinstance(value, dict):
                        if parent_key:
                            iterate_all(_keys, value,
                                        '{}.{}'.format(parent_key, key))
                        else:
                            iterate_all(_keys, value, key)
                    if isinstance(value, list):
                        for val in value:
                            if parent_key:
                                iterate_all(_keys, val,
                                            '{}.{}'.format(parent_key, key))
                            else:
                                iterate_all(_keys, val, key)

        def get_deleted_keys(_form_keys, _item_meta_keys):
            """Get all keys which do not consistency."""
            ignore_deleted_keys = [
                "pid", "owners_ext", "title", "owner", "status", "edit_mode",
                "lang", "shared_user_id", "created_by", "id", "$schema"]
            deleted_keys = []
            for item_meta_key in _item_meta_keys:
                key_list = item_meta_key.split('.')
                checked_key = key_list[0] if len(key_list) == 1 \
                    else '{}.{}'.format(key_list[0], key_list[1])
                if checked_key not in _form_keys \
                        and not key_list[0] in ignore_deleted_keys:
                    deleted_keys.append(checked_key)
            return deleted_keys

        def delele_json_by_keys(_deleted_keys, _json):
            """Delele item of json by keys."""
            for deleted_key in _deleted_keys:
                deleted_sub_keys = deleted_key.split('.')
                if len(deleted_sub_keys) == 1:
                    if _json.get(deleted_sub_keys[0]):
                        del _json[deleted_sub_keys[0]]
                elif len(deleted_sub_keys) > 1:
                    data_key = _json.get(deleted_sub_keys[0])
                    if isinstance(_json.get(deleted_sub_keys[0], {}), dict) \
                            and _json.get(deleted_sub_keys[0], {}).get(
                            'attribute_value_mlt'):
                        data_key = data_key.get('attribute_value_mlt')
                    if data_key and isinstance(data_key, dict):
                        if data_key.get(deleted_sub_keys[1]):
                            del data_key[deleted_sub_keys[1]]
                    if data_key and isinstance(data_key, list):
                        for data in data_key:
                            if data.get(deleted_sub_keys[1]):
                                del data[deleted_sub_keys[1]]
                    if isinstance(_json.get(deleted_sub_keys[0], {}), dict) \
                            and _json.get(deleted_sub_keys[0], {}).get(
                            'attribute_value_mlt'):
                        data_key_result = _json.get(deleted_sub_keys[0], {})
                        data_key_result['attribute_value_mlt'] = data_key
                        _json[deleted_sub_keys[0]] = data_key_result
                    else:
                        _json[deleted_sub_keys[0]] = data_key
            return _json

        try:
            with db.session.begin_nested():
                for item_type in get_all_item_type():
                    form_keys = get_item_type_form_keys([], item_type.form)
                    for item_meta in get_item_meta_by_item_type_id(
                            item_type.id):
                        # Update data for item_metadata.
                        item_meta_keys = []
                        iterate_all(item_meta_keys, item_meta.json)
                        deleted_keys = get_deleted_keys(form_keys,
                                                        item_meta_keys)
                        item_meta.json = delele_json_by_keys(deleted_keys,
                                                             item_meta.json)
                        # Update data for records_metadata.
                        rec_meta = get_record_meta_by_item_meta_id(item_meta.id)
                        rec_meta.json = delele_json_by_keys(deleted_keys,
                                                            rec_meta.json)
                        ItemMetadata.query.filter_by(id=item_meta.id).update(
                            {ItemMetadata.json: item_meta.json})
                        RecordMetadata.query.filter_by(id=rec_meta.id).update(
                            {RecordMetadata.json: rec_meta.json})
        except BaseException as ex:
            db.session.rollback()
            click.secho('metadata db update failed.', err=ex, fg='red')
            click.secho(ex, err=ex, fg='red')
        else:
            click.secho('metadata db has been updated.', fg='green')
            db.session.commit()

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

        if 'item_and_record' in tables.split(','):
            update_incorrect_metadata()
