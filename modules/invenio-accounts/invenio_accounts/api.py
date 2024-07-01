# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022-2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""API objects for Invenio Accounts."""


class Session:
    """Session object for DB Users change history."""

    def __init__(self):
        """Constructor."""
        self.updated_users = set()
        self.updated_roles = set()
        self.updated_domains = set()
        self.deleted_users = set()
        self.deleted_roles = set()
        self.deleted_domains = set()


class DBUsersChangeHistory:
    """DB Users change history storage."""

    def __init__(self):
        """Constructor."""
        self.sessions = {}

    def _get_session(self, session_id):
        """Returns or creates a session for a concrete session id."""
        return self.sessions.setdefault(session_id, Session())

    def add_updated_user(self, session_id, user_id):
        """Adds a user to the updated users list."""
        assert user_id is not None
        session = self._get_session(session_id)
        session.updated_users.add(user_id)

    def add_updated_role(self, session_id, role_id):
        """Adds a role to the updated roles list."""
        assert role_id is not None
        session = self._get_session(session_id)
        session.updated_roles.add(role_id)

    def add_updated_domain(self, session_id, domain_id):
        """Adds a user to the updated domains list."""
        assert domain_id is not None
        session = self._get_session(session_id)
        session.updated_domains.add(domain_id)

    def add_deleted_user(self, session_id, user_id):
        """Adds a user to the deleted users list."""
        assert user_id is not None
        session = self._get_session(session_id)
        session.deleted_users.add(user_id)

    def add_deleted_role(self, session_id, role_id):
        """Adds a role to the deleted roles list."""
        assert role_id is not None
        session = self._get_session(session_id)
        session.deleted_roles.add(role_id)

    def add_deleted_domain(self, session_id, domain_id):
        """Adds a role to the deleted domain list."""
        assert domain_id is not None
        session = self._get_session(session_id)
        session.deleted_domains.add(domain_id)

    def clear_dirty_sets(self, session):
        """Removes session object."""
        sid = id(session)
        self.sessions.pop(sid, None)
