# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Session-aware datastore."""

from datetime import datetime

from flask import current_app
from flask_security import SQLAlchemyUserDatastore, user_confirmed
from sqlalchemy.orm import joinedload

from .models import Domain, Role, User
from .proxies import current_db_change_history
from .sessions import delete_user_sessions
from .signals import datastore_post_commit, datastore_pre_commit


class SessionAwareSQLAlchemyUserDatastore(SQLAlchemyUserDatastore):
    """Datastore which deletes active session when a user is deactivated."""

    def verify_user(self, user):
        """Verify a user."""
        now = datetime.utcnow()
        user.blocked_at = None
        user.verified_at = now
        user.active = True
        if user.confirmed_at is None:
            user.confirmed_at = now
        return True

    def block_user(self, user):
        """Verify a user."""
        now = datetime.utcnow()
        user.blocked_at = now
        user.verified_at = None
        user.active = False
        delete_user_sessions(user)
        return True

    def activate_user(self, user):
        """Activate a unconfirmed/deactivated/blocked user."""
        res = super().activate_user(user)
        user.blocked_at = None
        if user.confirmed_at is None:
            user.confirmed_at = datetime.utcnow()
            user_confirmed.send(current_app._get_current_object(), user=user)
        return res

    def deactivate_user(self, user):
        """Deactivate a  user.

        :param user: A :class:`invenio_accounts.models.User` instance.
        :returns: The datastore instance.
        """
        res = super().deactivate_user(user)
        if res:
            user.blocked_at = None
            user.verified_at = None
            delete_user_sessions(user)
        return res

    def commit(self):
        """Commit a user to its session."""
        datastore_pre_commit.send(session=self.db.session)
        super().commit()
        datastore_post_commit.send(session=self.db.session)
        current_db_change_history.clear_dirty_sets(self.db.session)

    def mark_changed(self, sid, uid=None, rid=None, model=None):
        """Save a user to the changed history."""
        if model:
            if isinstance(model, User):
                current_db_change_history.add_updated_user(sid, model.id)
            elif isinstance(model, Role):
                current_db_change_history.add_updated_role(sid, model.id)
        elif uid:
            # Deprecated - use model param instead (still used in e.g.
            # UserFixture pytest-invenio)
            current_db_change_history.add_updated_user(sid, uid)
        elif rid:
            # Deprecated - use model param instead
            current_db_change_history.add_updated_role(sid, rid)

    def update_role(self, role):
        """Updates roles."""
        role = self.db.session.merge(role)
        # This works because role defines it's own id - for users
        # the same doesn't work because id is assigned on commit which
        # hasn't happened yet.
        self.mark_changed(id(self.db.session), model=role)
        return role

    def create_role(self, **kwargs):
        """Creates and returns a new role from the given parameters."""
        role = super().create_role(**kwargs)
        # This works because role defines it's own id - for users
        # the same doesn't work because id is assigned on commit which
        # hasn't happened yet.
        if role.id is None:
            role.id = role.name
        self.mark_changed(id(self.db.session), model=role)
        return role

    def find_role_by_id(self, role_id):
        """Fetches roles searching by id."""
        return self.role_model.query.filter_by(id=role_id).one_or_none()

    def find_domain(self, domain):
        """Find a domain."""
        return (
            Domain.query.filter_by(domain=domain)
            .options(joinedload(Domain.category_name))
            .one_or_none()
        )

    def create_domain(self, domain, **kwargs):
        """Create a new domain."""
        return Domain.create(domain, **kwargs)
