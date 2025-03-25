from datetime import datetime, timezone

from sqlalchemy import Sequence
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy_utils.types import JSONType

from invenio_accounts.models import User
from invenio_db import db

class UserActivityLog(db.Model):
    """User activity log model."""

    __tablename__ = 'user_activity_logs'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Unique identifier for the log entry."""

    date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'),
        nullable=False,
        default=datetime.now(timezone.utc)
    )
    """Date and time of the log entry."""

    user_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            User.id,
            name='fk_active_user_id',
            ondelete='SET NULL'
        ),
        nullable=True
    )
    """User ID of the user who performed the action."""

    repository_path = db.Column(
        db.Text(),
        nullable=False
    )
    """Repository path where the action was performed."""

    parent_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'user_activity_logs.id',
            name='fk_active_parent_id',
            ondelete='SET NULL'
        ),
        nullable=True
    )
    """Parent ID of the log entry."""

    log = db.Column(
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
    """Log entry."""

    remarks = db.Column(
        db.Text(),
        nullable=True
    )
    """Remarks for the log entry."""

    def to_dict(self):
        """Serialize object to dictionary."""
        return {
            'id': self.id,
            'date': self.date,
            'user_id': self.user_id if self.user_id else "",
            'repository_path': self.repository_path,
            'parent_id': self.parent_id if self.parent_id else "",
            'log': self.log,
            'remarks': self.remarks
        }

    @classmethod
    def get_sequence(cls, session):
        """Get author id next sequence.

        :param session: Session
        :return: Next sequence.
        """
        if not session:
            session = db.session
        seq = Sequence('user_activity_logs_id_seq')
        next_id = session.execute(seq)
        return next_id
