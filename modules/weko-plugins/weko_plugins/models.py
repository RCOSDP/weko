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

from datetime import datetime
from flask_babelex import gettext as _
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy_utils.types import UUIDType
from sqlalchemy_utils.types.choice import ChoiceType

from weko_groups.widgets import RadioGroupWidget
from weko_records.models import ItemMetadata


class FlowStatusPolicy(object):
    """Workflow status policies."""

    AVAILABLE = 'A'
    """Flow is availabled."""

    INUSE = 'U'
    """Flow has be used."""

    MAKING = 'M'
    """Flow is making."""

    descriptions = dict([
        (AVAILABLE,
         _('Available.')),
        (INUSE,
         _('In use.')),
        (MAKING,
         _('Making.')),
    ])
    """Policies descriptions."""

    @classmethod
    def describe(cls, policy):
        """
        Policy description.

        :param policy:
        """
        if cls.validate(policy):
            return cls.descriptions[policy]

    @classmethod
    def validate(cls, policy):
        """
        Validate subscription policy value.

        :param policy:
        """
        return policy in [cls.AVAILABLE, cls.INUSE, cls.MAKING]


class StatusPolicy(object):
    """Workflow status policies."""

    NEW = 'N'
    """Record has be created."""

    UPT = 'U'
    """Record has be updated."""

    DEL = 'D'
    """Record has be deleted(logic)."""

    descriptions = dict([
        (NEW,
         _('Created.')),
        (UPT,
         _('Updated.')),
        (DEL,
         _('Deleted.')),
    ])
    """Policies descriptions."""

    @classmethod
    def describe(cls, policy):
        """
        Policy description.

        :param policy:
        """
        if cls.validate(policy):
            return cls.descriptions[policy]

    @classmethod
    def validate(cls, policy):
        """
        Validate subscription policy value.

        :param policy:
        """
        return policy in [cls.NEW, cls.UPT, cls.DEL]


class TimestampMixin(object):
    """Timestamp model mix-in with fractional seconds support.

    SQLAlchemy-Utils timestamp model does not have support for
    fractional seconds.
    """
    STATUSPOLICY = [
        (StatusPolicy.NEW, _('Record has be created.')),
        (StatusPolicy.UPT, _('Record has be updated.')),
        (StatusPolicy.DEL, _('Record has be deleted.')),
    ]
    """Status policy choices."""

    status = db.Column(
        ChoiceType(STATUSPOLICY, impl=db.String(1)), nullable=False,
        default=StatusPolicy.NEW,
        info=dict(
            label=_('Status Policy'),
            widget=RadioGroupWidget(StatusPolicy.descriptions),
        )
    )
    """Policy for status to db record."""

    created = db.Column(db.DateTime, nullable=False, default=datetime.now)
    """Creation timestamp."""

    modified = db.Column(db.DateTime, nullable=False, default=datetime.now,
                         onupdate=datetime.now)
    """Modification timestamp."""


class ActionStatus(db.Model, TimestampMixin):
    """define ActionStatus"""

    __tablename__ = 'action_status'

    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    """ActionStatus identifier."""

    action_status_id = db.Column(
        db.String(1), nullable=False, unique=True, index=True)
    """the id of action status."""

    action_status_name = db.Column(
        db.String(32), nullable=True, unique=False, index=False)
    """the name of action."""

    action_status_desc = db.Column(db.Text, nullable=True)
    """the description of action."""

    action_scopes = db.Column(db.String(64), nullable=True)
    """the scopes of action status(sys,user)."""

    action_displays = db.Column(db.Text, nullable=True, unique=False)
    """the display info of action status."""


class Action(db.Model, TimestampMixin):
    """define Action"""

    __tablename__ = 'action'

    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    """Action identifier."""

    action_name = db.Column(
        db.String(255), nullable=True, unique=False, index=False)
    """the name of action."""

    action_desc = db.Column(db.Text, nullable=True)
    """the description of action."""

    action_version = db.Column(db.String(64), nullable=True)
    """the version of action."""

    action_lastdate = db.Column(
        db.DateTime, nullable=False, default=datetime.now)
    """the last update date of action."""


class Flow(db.Model, TimestampMixin):
    """define Flow"""

    __tablename__ = 'flow'

    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    """Flow identifier."""

    flow_id = db.Column(UUIDType, nullable=False, unique=False, index=True)
    """the id of flow."""

    flow_name = db.Column(
        db.String(255), nullable=True, unique=False, index=False)
    """the name of flow."""

    flow_user = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, unique=False)
    """the user who update the flow."""

    FLOWSTATUSPOLICY = [
        (FlowStatusPolicy.AVAILABLE, _('Available')),
        (FlowStatusPolicy.INUSE, _('In use')),
        (FlowStatusPolicy.MAKING, _('Making')),
    ]
    """Subscription policy choices."""

    flow_status = db.Column(
        ChoiceType(FLOWSTATUSPOLICY, impl=db.String(1)),
        nullable=False,
        default=FlowStatusPolicy.MAKING,
        info=dict(
            label=_('Subscription Policy'),
            widget=RadioGroupWidget(FlowStatusPolicy.descriptions),
        ))
    """the status of flow."""

    action_id = db.Column(db.Integer, db.ForeignKey(Action.id),
                          nullable=False, unique=False)
    """the id of action."""

    action_order = db.Column(db.Integer, nullable=False, unique=False)
    """the order of action."""

    action_condition = db.Column(db.String(255), nullable=True, unique=False)
    """the condition of action."""


class Flows(db.Model, TimestampMixin):
    """define Flows"""

    __tablename__ = 'flows'

    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    """Flows identifier."""

    flows_id = db.Column(db.Integer, nullable=False, unique=True)
    """the id of flows."""

    flows_name = db.Column(
        db.String(255), nullable=True, unique=False, index=False)
    """the name of flows."""

    itemtype_id = db.Column(db.Integer, nullable=False, unique=False)
    """the id of itemtype."""

    flow_id = db.Column(db.Integer, db.ForeignKey(Flow.id),
                        nullable=False, unique=False)
    """the id of flow."""

    flow_order = db.Column(db.Integer, nullable=False, unique=False)
    """the order of flow."""

    flow_condition = db.Column(db.Integer, nullable=False, unique=False)
    """the pre condition of flow."""

    FLOWSTATUSPOLICY = [
        (FlowStatusPolicy.AVAILABLE, _('Available')),
        (FlowStatusPolicy.INUSE, _('In use')),
        (FlowStatusPolicy.MAKING, _('Making')),
    ]
    """Subscription policy choices."""

    flows_status = db.Column(
        ChoiceType(FLOWSTATUSPOLICY, impl=db.String(1)),
        nullable=False,
        default=FlowStatusPolicy.MAKING,
        info=dict(
            label=_('Subscription Policy'),
            widget=RadioGroupWidget(FlowStatusPolicy.descriptions),
        ))
    """the status of flows."""


class Activity(db.Model, TimestampMixin):
    """define Activety"""

    __tablename__ = 'activity'

    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    """Activity identifier."""

    activity_id = db.Column(
        db.String(24), nullable=False, unique=True, index=True)
    """activity id of Activity."""

    activity_name = db.Column(
        db.String(255), nullable=True, unique=False, index=False)
    """activity name of Activity."""

    item_id = db.Column(
        UUIDType, db.ForeignKey(ItemMetadata.id), nullable=False, unique=False, index=True)
    """item id."""

    flows_id = db.Column(
        db.Integer, db.ForeignKey(Flows.id), nullable=False, unique=False)
    """flows id."""

    flows_status = db.Column(
        db.Integer, nullable=True, unique=False)
    """flows status."""

    flow_id = db.Column(
        db.Integer, db.ForeignKey(Flow.id), nullable=True, unique=False)
    """flow id."""

    flow_status = db.Column(
        db.Integer, nullable=True, unique=False)
    """flow status."""

    action_id = db.Column(
        db.Integer, db.ForeignKey(Action.id), nullable=True, unique=False)
    """action id."""

    action_version = db.Column(
        db.String(24), nullable=True, unique=False)
    """action version."""

    action_status = db.Column(
        db.Integer, nullable=True, unique=False)
    """action status."""

    activity_login_user = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, unique=False)
    """the user of create activity."""

    activity_update_user = db.Column(
        db.Integer, db.ForeignKey(User.id), nullable=True, unique=False)
    """the user of update activity."""

    activity_status = db.Column(
        db.Integer, nullable=True)
    """activity status."""

    activity_start = db.Column(db.DateTime, nullable=False)
    """activity start date."""

    activity_end = db.Column(db.DateTime, nullable=False)
    """activity end date."""


class ActivityHistory(db.Model, TimestampMixin):
    """define ActivityHistory"""

    __tablename__ = 'activity_history'

    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    """ActivityHistory identifier."""

    activity_id = db.Column(
        db.String(24), nullable=False, unique=False, index=True)
    """activity id of Activity."""

    action_id = db.Column(db.Integer, nullable=False, unique=False)
    """action id."""

    action_version = db.Column(
        db.String(24), nullable=True, unique=False)
    """the used version of action."""

    action_status = db.Column(db.String(255), nullable=True)
    """the status description of action."""

    action_user = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    """the user of operate action."""

    action_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    """the date of operate action."""

    action_comment = db.Column(db.Text, nullable=True)
    """action comment."""

    user = db.relationship(User, backref=db.backref(
        'activity_history'))
    """User relaionship."""
