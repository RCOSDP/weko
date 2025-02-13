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

from flask_babelex import gettext as _
from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType

class WorkspaceDefaultConditions(db.Model):
    """define WorkspaceDefaultConditions."""

    __tablename__ = 'workspace_default_conditions'

    user_id = db.Column(db.Integer(), nullable=False,primary_key=True,index=True)
    """WorkspaceDefaultConditions identifier."""

    default_con = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        nullable=False
    )
    """the name of WorkspaceDefaultConditions."""

    created = db.Column(
        db.DateTime, nullable=False)
    """the create date of WorkspaceDefaultConditions."""

    updated = db.Column(
        db.DateTime, nullable=False)
    """the last update date of WorkspaceDefaultConditions."""


# class FlowDefine(db.Model, TimestampMixin):
#     """Define Flow."""

#     __tablename__ = 'workflow_flow_define'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """Flow identifier."""

#     flow_id = db.Column(
#         UUIDType, nullable=False, unique=True, index=True,
#         default=uuid.uuid4()
#     )
#     """the id of flow."""

#     flow_name = db.Column(
#         db.String(255), nullable=True, unique=True, index=True)
#     """the name of flow."""

#     flow_user = db.Column(
#         db.Integer(),
#         db.ForeignKey(User.id), nullable=True, unique=False)
#     """the user who update the flow."""

#     user_profile = db.relationship(User)
#     """User relationship"""

#     FLOWSTATUSPOLICY = [
#         (FlowStatusPolicy.AVAILABLE,
#          FlowStatusPolicy.describe(FlowStatusPolicy.AVAILABLE)),
#         (FlowStatusPolicy.INUSE,
#          FlowStatusPolicy.describe(FlowStatusPolicy.INUSE)),
#         (FlowStatusPolicy.MAKING,
#          FlowStatusPolicy.describe(FlowStatusPolicy.MAKING)),
#     ]
#     """Subscription policy choices."""

#     flow_status = db.Column(
#         ChoiceType(FLOWSTATUSPOLICY, impl=db.String(1)),
#         nullable=False,
#         default=FlowStatusPolicy.MAKING,
#         info=dict(
#             label=_('Subscription Policy'),
#             widget=RadioGroupWidget(FlowStatusPolicy.descriptions),
#         ))
#     """the status of flow."""

#     flow_actions = db.relationship('FlowAction', backref=db.backref('flow'))
#     """flow action relationship."""

#     is_deleted = db.Column(db.Boolean(name='is_deleted'), nullable=False, default=False)
#     """flow define delete flag."""


# class FlowAction(db.Model, TimestampMixin):
#     """Action list belong to Flow."""

#     __tablename__ = 'workflow_flow_action'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """FlowAction identifier."""

#     flow_id = db.Column(
#         UUIDType, db.ForeignKey(FlowDefine.flow_id),
#         nullable=False, unique=False, index=True)
#     """the id of flow."""

#     action_id = db.Column(db.Integer(), db.ForeignKey(Action.id),
#                           nullable=False, unique=False)
#     """the id of action."""

#     action_version = db.Column(db.String(64), nullable=True)
#     """the version of used action."""

#     action_order = db.Column(db.Integer(), nullable=False, unique=False)
#     """the order of action."""

#     action_condition = db.Column(db.String(255), nullable=True, unique=False)
#     """the condition of transition."""

#     TATUSPOLICY = [
#         (AvailableStautsPolicy.USABLE,
#          AvailableStautsPolicy.describe(AvailableStautsPolicy.USABLE)),
#         (AvailableStautsPolicy.UNUSABLE,
#          AvailableStautsPolicy.describe(AvailableStautsPolicy.UNUSABLE)),
#     ]
#     """Subscription policy choices."""

#     action_status = db.Column(
#         ChoiceType(TATUSPOLICY, impl=db.String(1)),
#         nullable=False,
#         default=AvailableStautsPolicy.USABLE)
#     """the status of flow action."""

#     action_date = db.Column(
#         db.DateTime, nullable=False, default=datetime.now)
#     """the use date of action."""

#     action = db.relationship(
#         Action, backref=db.backref('flow_action'))
#     """flow action relationship."""

#     action_roles = db.relationship(
#         'FlowActionRole',
#         backref=db.backref('flow_action'))
#     """flow action relationship."""

#     send_mail_setting = db.Column(
#         db.JSON().with_variant(
#             postgresql.JSONB(none_as_null=True),
#             'postgresql',
#         ).with_variant(
#             JSONType(),
#             'sqlite',
#         ).with_variant(
#             JSONType(),
#             'mysql',
#         ),
#         default=lambda: dict(),
#         nullable=True
#     )


# class FlowActionRole(db.Model, TimestampMixin):
#     """FlowActionRole list belong to FlowAction.

#     It relates an allowed action with a role or a user
#     """

#     __tablename__ = 'workflow_flow_action_role'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """FlowAction identifier."""

#     flow_action_id = db.Column(
#         db.Integer(), db.ForeignKey(FlowAction.id),
#         nullable=False, unique=False, index=True)
#     """the id of flow_action."""

#     action_role = db.Column(db.Integer(), db.ForeignKey(Role.id),
#                             nullable=True, unique=False)

#     action_role_exclude = db.Column(
#         db.Boolean(name='role_exclude'),
#         nullable=False, default=False, server_default='0')
#     """If set to True, deny the action, otherwise allow it."""

#     action_user = db.Column(db.Integer(), db.ForeignKey(User.id),
#                             nullable=True, unique=False)

#     action_user_exclude = db.Column(
#         db.Boolean(name='user_exclude'),
#         nullable=False, default=False, server_default='0')
#     """If set to True, deny the action, otherwise allow it."""

#     specify_property = db.Column(
#         db.String(255), nullable=True)
#     """the name of flows."""


# class WorkFlow(db.Model, TimestampMixin):
#     """Define WorkFlow."""

#     __tablename__ = 'workflow_workflow'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """Flows identifier."""

#     flows_id = db.Column(
#         UUIDType,
#         nullable=False,
#         unique=True,
#         index=True,
#         default=uuid.uuid4()
#     )
#     """the id of flows."""

#     flows_name = db.Column(
#         db.String(255), nullable=True, unique=False, index=False)
#     """the name of flows."""

#     itemtype_id = db.Column(
#         db.Integer(), db.ForeignKey(ItemType.id), nullable=False, unique=False)
#     """the id of itemtype."""

#     itemtype = db.relationship(
#         ItemType,
#         backref=db.backref('workflow', lazy='dynamic',
#                            order_by=desc('item_type.tag'))
#     )

#     index_tree_id = db.Column(
#         db.BigInteger, nullable=True, unique=False)
#     """Index tree id that this workflow will belong to"""

#     flow_id = db.Column(db.Integer(), db.ForeignKey(FlowDefine.id),
#                         nullable=False, unique=False)
#     """the id of flow."""

#     flow_define = db.relationship(
#         FlowDefine,
#         backref=db.backref('workflow', lazy='dynamic')
#     )

#     is_deleted = db.Column(db.Boolean(name='is_deleted'), nullable=False, default=False)
#     """workflow delete flag."""

#     open_restricted = db.Column(db.Boolean(name='open_restricted'), nullable=False, default=True)
#     """Open restricted flag."""

#     location_id = db.Column(db.Integer(), db.ForeignKey(Location.id),
#                         nullable=True, unique=False)
#     """the id of location."""

#     location = db.relationship(
#         Location,
#         backref=db.backref('workflow', lazy='dynamic')
#     )

#     is_gakuninrdm = db.Column(db.Boolean(name='is_gakuninrdm'), nullable=False, default=False)
#     """GakuninRDM flag."""


# class Activity(db.Model, TimestampMixin):
#     """Define Activity."""

#     __tablename__ = 'workflow_activity'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """Activity identifier."""

#     activity_id = db.Column(
#         db.String(24), nullable=False, unique=True, index=True)
#     """activity id of Activity."""

#     activity_name = db.Column(
#         db.String(255), nullable=True, unique=False, index=False)
#     """activity name of Activity."""

#     item_id = db.Column(
#         UUIDType,
#         nullable=True, unique=False, index=True)
#     """item id."""

#     workflow_id = db.Column(
#         db.Integer(), db.ForeignKey(WorkFlow.id),
#         nullable=False, unique=False)
#     """workflow id."""

#     workflow = db.relationship(
#         WorkFlow,
#         backref=db.backref('activity', lazy='dynamic')
#     )

#     workflow_status = db.Column(
#         db.Integer(), nullable=True, unique=False)
#     """workflow status."""

#     flow_id = db.Column(
#         db.Integer(), db.ForeignKey(FlowDefine.id),
#         nullable=True, unique=False)
#     """flow id."""

#     flow_define = db.relationship(
#         FlowDefine,
#         backref=db.backref('activity', lazy='dynamic')
#     )

#     action_id = db.Column(
#         db.Integer(), db.ForeignKey(Action.id), nullable=True, unique=False)
#     """action id."""

#     action = db.relationship(
#         Action,
#         backref=db.backref('activity', lazy='dynamic')
#     )

#     action_status = db.Column(
#         db.String(1), db.ForeignKey(ActionStatus.action_status_id),
#         nullable=True, unique=False)
#     """action status."""

#     activity_login_user = db.Column(
#         db.Integer(), db.ForeignKey(User.id),
#         nullable=True, unique=False)
#     """the user of create activity."""

#     activity_update_user = db.Column(
#         db.Integer(), db.ForeignKey(User.id),
#         nullable=True, unique=False)
#     """the user of update activity."""

#     ACTIVITYSTATUSPOLICY = [
#         (ActivityStatusPolicy.ACTIVITY_BEGIN,
#          ActivityStatusPolicy.describe(ActivityStatusPolicy.ACTIVITY_BEGIN)),
#         (ActivityStatusPolicy.ACTIVITY_FINALLY,
#          ActivityStatusPolicy.describe(ActivityStatusPolicy.ACTIVITY_FINALLY)),
#         (ActivityStatusPolicy.ACTIVITY_FORCE_END,
#          ActivityStatusPolicy.describe(
#              ActivityStatusPolicy.ACTIVITY_FORCE_END)),
#         (ActivityStatusPolicy.ACTIVITY_CANCEL,
#          ActivityStatusPolicy.describe(ActivityStatusPolicy.ACTIVITY_CANCEL)),
#         (ActivityStatusPolicy.ACTIVITY_MAKING,
#          ActivityStatusPolicy.describe(ActivityStatusPolicy.ACTIVITY_MAKING)),
#         (ActivityStatusPolicy.ACTIVITY_ERROR,
#          ActivityStatusPolicy.describe(ActivityStatusPolicy.ACTIVITY_ERROR)),
#     ]
#     """Subscription policy choices."""

#     activity_status = db.Column(
#         ChoiceType(ACTIVITYSTATUSPOLICY, impl=db.String(1)),
#         default=ActivityStatusPolicy.ACTIVITY_BEGIN,
#         nullable=True, unique=False, index=False)
#     """activity status."""

#     activity_start = db.Column(db.DateTime, nullable=False)
#     """activity start date."""

#     activity_end = db.Column(db.DateTime, nullable=True)
#     """activity end date."""

#     activity_community_id = db.Column(db.Text, nullable=True)
#     """activity community id"""

#     activity_confirm_term_of_use = db.Column(
#         db.Boolean(name='activity_confirm_term_of_use'), nullable=True,
#         default=True)

#     title = db.Column(db.Text, nullable=True)

#     shared_user_id = db.Column(db.Integer(), nullable=True)

#     temp_data = db.Column(
#         db.JSON().with_variant(
#             postgresql.JSONB(none_as_null=True),
#             'postgresql',
#         ).with_variant(
#             JSONType(),
#             'sqlite',
#         ).with_variant(
#             JSONType(),
#             'mysql',
#         ),
#         default=lambda: dict(),
#         nullable=True
#     )
#     """temp metadata"""

#     approval1 = db.Column(db.Text, nullable=True)

#     approval2 = db.Column(db.Text, nullable=True)

#     # Some extra info want to store
#     extra_info = db.Column(
#         db.JSON().with_variant(
#             postgresql.JSONB(none_as_null=True),
#             'postgresql',
#         ).with_variant(
#             JSONType(),
#             'sqlite',
#         ).with_variant(
#             JSONType(),
#             'mysql',
#         ),
#         default=lambda: dict(),
#         nullable=True
#     )

#     action_order = db.Column(db.Integer(), nullable=True, unique=False)
#     """the order of action."""


# class ActivityAction(db.Model, TimestampMixin):
#     """Define Activety."""

#     __tablename__ = 'workflow_activity_action'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """Activity_Action identifier."""

#     activity_id = db.Column(
#         db.String(24), db.ForeignKey(Activity.activity_id),
#         nullable=False, unique=False, index=True)
#     """activity id of Activity Action."""

#     action_id = db.Column(
#         db.Integer(), db.ForeignKey(Action.id), nullable=True, unique=False)
#     """action id."""

#     action_status = db.Column(
#         db.String(1), db.ForeignKey(ActionStatus.action_status_id),
#         nullable=False, unique=False)
#     """action status."""

#     action_comment = db.Column(db.Text, nullable=True)
#     """action comment."""

#     action_handler = db.Column(db.Integer, nullable=True)
#     """action handler"""

#     action_order = db.Column(db.Integer(), nullable=True, unique=False)
#     """the order of action."""


# class ActivityHistory(db.Model, TimestampMixin):
#     """Define ActivityHistory."""

#     __tablename__ = 'workflow_action_history'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """ActivityHistory identifier."""

#     activity_id = db.Column(
#         db.String(24), nullable=False, unique=False, index=True)
#     """activity id of Activity."""

#     action_id = db.Column(db.Integer(), nullable=False, unique=False)
#     """action id."""

#     action_version = db.Column(
#         db.String(24), nullable=True, unique=False)
#     """the used version of action."""

#     action_status = db.Column(
#         db.String(1), db.ForeignKey(ActionStatus.action_status_id),
#         nullable=True)
#     """the status description of action."""

#     action_user = db.Column(
#         db.Integer(), db.ForeignKey(
#             User.id), nullable=True)
#     """the user of operate action."""

#     action_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
#     """the date of operate action."""

#     action_comment = db.Column(db.Text, nullable=True)
#     """action comment."""

#     user = db.relationship(User, backref=db.backref(
#         'activity_history'))
#     """User relaionship."""

#     action_order = db.Column(db.Integer(), nullable=True, unique=False)
#     """the order of action."""


# class ActionJournal(db.Model, TimestampMixin):
#     """Define journal info."""

#     __tablename__ = 'workflow_action_journal'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """Activity_Action identifier."""

#     activity_id = db.Column(
#         db.String(24), nullable=False, unique=False, index=True)
#     """Activity id of Activity Action."""

#     action_id = db.Column(
#         db.Integer(), db.ForeignKey(Action.id), nullable=True, unique=False)
#     """Action id."""

#     action_journal = db.Column(
#         db.JSON().with_variant(
#             postgresql.JSONB(none_as_null=True),
#             'postgresql',
#         ).with_variant(
#             JSONType(),
#             'sqlite',
#         ).with_variant(
#             JSONType(),
#             'mysql',
#         ),
#         default=lambda: dict(),
#         nullable=True
#     )
#     """Action journal info."""


# class ActionIdentifier(db.Model, TimestampMixin):
#     """Define action identifier info."""

#     __tablename__ = 'workflow_action_identifier'

#     id = db.Column(db.Integer(), nullable=False,
#                    primary_key=True, autoincrement=True)
#     """Activity_Action identifier."""

#     activity_id = db.Column(
#         db.String(24), nullable=False, unique=False, index=True)
#     """Activity id of Activity Action."""

#     action_id = db.Column(
#         db.Integer(), db.ForeignKey(Action.id), nullable=True, unique=False)
#     """Action id."""

#     action_identifier_select = db.Column(db.Integer, nullable=True, default=0)
#     """Action identifier grant."""

#     action_identifier_jalc_doi = db.Column(db.String(255),
#                                            nullable=True,
#                                            default="")
#     """Action identifier grant jalc doi input."""

#     action_identifier_jalc_cr_doi = db.Column(db.String(255),
#                                               nullable=True,
#                                               default="")
#     """Action identifier grant jalc crossref doi input."""

#     action_identifier_jalc_dc_doi = db.Column(db.String(255),
#                                               nullable=True,
#                                               default="")
#     """Action identifier grant jalc datacite doi input."""

#     action_identifier_ndl_jalc_doi = db.Column(db.String(255),
#                                                nullable=True,
#                                                default="")
#     """Action identifier grant ndl jalc doi input."""


# class ActionFeedbackMail(db.Model, TimestampMixin):
#     """Define action identifier info."""

#     __tablename__ = 'workflow_action_feedbackmail'

#     id = db.Column(
#         db.Integer(),
#         nullable=False,
#         primary_key=True,
#         autoincrement=True
#     )
#     """ActionFeedbackMail identifier."""

#     activity_id = db.Column(
#         db.String(24),
#         nullable=False,
#         unique=False,
#         index=True
#     )
#     """Activity id of Activity Action."""

#     action_id = db.Column(
#         db.Integer(),
#         db.ForeignKey(Action.id),
#         nullable=True,
#         unique=False
#     )
#     """Action id."""

#     feedback_maillist = db.Column(
#         db.JSON().with_variant(
#             postgresql.JSONB(none_as_null=True),
#             'postgresql',
#         ).with_variant(
#             JSONType(),
#             'sqlite',
#         ).with_variant(
#             JSONType(),
#             'mysql',
#         ),
#         default=lambda: dict(),
#         nullable=True
#     )
#     """Action journal info."""


# class WorkflowRole(db.Model, TimestampMixin):
#     """Define action identifier info."""

#     __tablename__ = 'workflow_userrole'

#     workflow_id = db.Column(
#         db.Integer(),
#         db.ForeignKey(WorkFlow.id, ondelete='CASCADE'), primary_key=True,
#         nullable=True,
#         unique=False)

#     role_id = db.Column(
#         db.Integer(),
#         db.ForeignKey(Role.id, ondelete='CASCADE'), primary_key=True,
#         nullable=True, unique=False)

#     """Relationship between workflow and roles."""


# class GuestActivity(db.Model, Timestamp):
#     """Guest activity."""

#     __tablename__ = "guest_activity"

#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     """Identifier"""

#     user_mail = db.Column(db.String(255), nullable=False)
#     """User mail"""

#     record_id = db.Column(db.String(255), nullable=False)
#     """Record identifier."""

#     file_name = db.Column(db.String(255), nullable=False)
#     """File name"""

#     activity_id = db.Column(
#         db.String(24), nullable=False, unique=True, index=True)
#     """Activity id of Guest Activity."""

#     token = db.Column(db.String(255), nullable=False)
#     """Token."""

#     expiration_date = db.Column(db.Integer, nullable=False, default=0)
#     """Expiration Date."""

#     is_usage_report = db.Column(db.Boolean(name='is_usage_report'), nullable=False, default=False)
#     """Is Usage Report."""

#     def __init__(self, **kwargs):
#         """Initial guest activity.

#         @param kwargs:
#         """
#         for k, v in kwargs.items():
#             setattr(self, k, v)

#     @classmethod
#     def create(cls, **kwargs):
#         """Create guest activity.

#         @param kwargs:
#         @return:
#         """
#         try:
#             guest_activity = cls(**kwargs)
#             db.session.add(guest_activity)
#             db.session.commit()
#             return guest_activity
#         except Exception as ex:
#             db.session.rollback()
#             current_app.logger.error(ex)
#             return None

#     @classmethod
#     def find_by_activity_id(cls, activity_id):
#         """Find guest activity by activity id.

#         @param activity_id:
#         @return:
#         """
#         with db.session.no_autoflush:
#             return db.session.query(cls).filter(
#                 cls.activity_id == activity_id).all()

#     @classmethod
#     def find(cls, **kwargs):
#         """Find guest activity.

#         @param kwargs:
#         @return:
#         """
#         query = db.session.query(cls)
#         if kwargs.get("user_mail"):
#             query = query.filter(cls.user_mail == kwargs.get("user_mail"))
#         if kwargs.get("record_id"):
#             query = query.filter(cls.record_id == kwargs.get("record_id"))
#         if kwargs.get("file_name"):
#             query = query.filter(cls.file_name == kwargs.get("file_name"))
#         if kwargs.get("activity_id"):
#             query = query.filter(cls.activity_id == kwargs.get("activity_id"))

#         with db.session.no_autoflush:
#             return query.all()

#     @classmethod
#     def delete(cls, guest_activity):
#         """Delete guest activity.

#         @param guest_activity:
#         @return:
#         """
#         with db.session.begin_nested():
#             db.session.delete(guest_activity)

#     @classmethod
#     def get_expired_activities(cls) -> list:
#         """Get expired activities.

#         @rtype: object
#         """
#         query = db.session.query(cls).with_entities(cls.activity_id)
#         current_date = datetime.utcnow().date()
#         query = query.filter(
#             db.cast(
#                 cls.created + func.make_interval(0, 0, 0, cls.expiration_date),
#                 db.DATE) < current_date
#         ).filter(
#             cls.is_usage_report.is_(True)
#         )

#         return query.all()

#     @classmethod
#     def get_usage_report_activities(cls) -> list:
#         """Get usage report activities.

#         Returns:
#             list: Activities identifier list.

#         """
#         query = db.session.query(cls).with_entities(cls.activity_id)
#         current_date = datetime.utcnow().date()
#         query = query.filter(
#             db.cast(
#                 cls.created + func.make_interval(0, 0, 0, cls.expiration_date),
#                 db.DATE) >= current_date
#         ).filter(
#             cls.is_usage_report.is_(True)
#         )

#         return query.all()

# class ActivityCount(db.Model, TimestampMixin):
#     """today Activity count."""

#     __tablename__ = 'workflow_activity_count'

#     date = db.Column(db.Date(), nullable=False,
#                    primary_key=True)
#     """Activity_id date"""

#     activity_count = db.Column(
#         db.Integer(), default=1,
#         nullable=False, unique=False)
#     """today count"""
