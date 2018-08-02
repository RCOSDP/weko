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
from invenio_db import db

from .models import ActionStatus, Action, Activity, ActivityHistory,\
    Flow, Flows, FlowStatusPolicy


@click.group()
def workflow():
    """workflow commands."""


@workflow.command('init')
@click.argument('tables', default='')
@with_appcontext
def init_workflow(tables):
    """
    Init workflow tables.
    """
    def init_action_status():
        """Init ActionStatus Table"""
        db_action_status = list()
        db_action_status.append(dict(
            action_status_id='B',
            action_status_name='開始',
            action_status_desc='アクション開始したことを示す',
            action_scopes='sys',
            action_displays=''
        ))
        db_action_status.append(dict(
            action_status_id='F',
            action_status_name='終了',
            action_status_desc='アクション終了したことを示す',
            action_scopes='sys,user',
            action_displays='作業済み,終了,完了'
        ))
        db_action_status.append(dict(
            action_status_id='E',
            action_status_name='強制終了',
            action_status_desc='フローを中断し、後続のアクションの実行を行わないことを示す',
            action_scopes='user',
            action_displays='中断,取り消し'
        ))
        db_action_status.append(dict(
            action_status_id='C',
            action_status_name='取り消し',
            action_status_desc='フローの作業をやり直すことを示し、開始アクションから行う状態を示す',
            action_scopes='user',
            action_displays='差し戻し,取り消し,やり消し,再処理'
        ))
        db_action_status.append(dict(
            action_status_id='M',
            action_status_name='作業中',
            action_status_desc='アクションが完了しておらず、該当アクションの継続作業が必要な状態を示す',
            action_scopes='user',
            action_displays='作業中,査読中,審査中'
        ))
        return db_action_status

    def init_action():
        """Init Action Table"""
        db_action = list()
        db_action.append(dict(
            action_name='重複チェック',
            action_desc='アイテムの重複登録があるかを確認するため',
            action_version='1.0.0',
            action_lastdate=datetime.date(2018, 5, 15)
        ))
        db_action.append(dict(
            action_name='アイテム登録',
            action_desc='アイテムを登録するためのブラグイン',
            action_version='1.0.1',
            action_lastdate=datetime.date(2018, 5, 22)
        ))
        db_action.append(dict(
            action_name='コンテンツアップロード',
            action_desc='アイテムに関連してアップロードするコンテンツファイル',
            action_version='1.2.1',
            action_lastdate=datetime.date(2018, 4, 22)
        ))
        db_action.append(dict(
            action_name='承認依頼',
            action_desc='アイテムに対しての承認者を設けて、承認を得る',
            action_version='1.1.1',
            action_lastdate=datetime.date(2018, 6, 11)
        ))
        db_action.append(dict(
            action_name='承認',
            action_desc='承認依頼されているアイテムに対しての承認される',
            action_version='2.0.0',
            action_lastdate=datetime.date(2018, 2, 11)
        ))
        db_action.append(dict(
            action_name='ビアレビュー',
            action_desc='アイテムについてのビアレビューをサポートする',
            action_version='1.1.2',
            action_lastdate=datetime.date(2018, 6, 8)
        ))
        return db_action

    def init_flow():
        """Init Flow Table"""
        db_flow = list()
        _uuid = uuid.uuid4()
        db_flow.append(dict(
            flow_id=_uuid,
            flow_name='登録フロー',
            flow_status=FlowStatusPolicy.INUSE,
            action_id=2,
            action_order=1
        ))
        db_flow.append(dict(
            flow_id=_uuid,
            flow_name='登録フロー',
            flow_status=FlowStatusPolicy.INUSE,
            action_id=5,
            action_order=2
        ))
        db_flow.append(dict(
            flow_id=uuid.uuid4(),
            flow_name='登録承認フロー',
            flow_status=FlowStatusPolicy.AVAILABLE,
            action_id=2,
            action_order=1
        ))
        db_flow.append(dict(
            flow_id=uuid.uuid4(),
            flow_name='メタデータ付加フロー',
            flow_status=FlowStatusPolicy.MAKING,
            action_id=2,
            action_order=1
        ))
        return db_flow

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
                        db_flow = init_flow()
                        db.session.execute(Flow.__table__.insert(),
                                           db_flow)
        except BaseException as ex:
            db.session.rollback()
            click.secho(str(ex), fg='blue')
            click.secho('workflow db init failed.', err=ex, fg='red')
        else:
            db.session.commit()
            click.secho('workflow db has been initialised.', fg='green')
