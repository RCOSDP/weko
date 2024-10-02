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
# WEKO3 is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.


"""Test groups data models."""

import pytest
from mock import patch, MagicMock
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError, NoResultFound

from weko_groups.api import Group, Membership, MembershipState, \
    PrivacyPolicy, SubscriptionPolicy


def test_subscription_policy_validate():
    """Test policy validation."""
    from weko_groups.api import SubscriptionPolicy

    assert SubscriptionPolicy.validate(SubscriptionPolicy.OPEN)
    assert SubscriptionPolicy.validate(SubscriptionPolicy.APPROVAL)
    assert SubscriptionPolicy.validate(SubscriptionPolicy.CLOSED)
    assert not SubscriptionPolicy.validate("INVALID")


def test_subscription_policy_describe():
    """Test policy describe."""
    from weko_groups.api import SubscriptionPolicy

    assert SubscriptionPolicy.describe(SubscriptionPolicy.OPEN)
    assert SubscriptionPolicy.describe(SubscriptionPolicy.APPROVAL)
    assert SubscriptionPolicy.describe(SubscriptionPolicy.CLOSED)
    assert SubscriptionPolicy.describe("INVALID") is None


def test_privacy_policy_validate():
    """Test policy validation."""
    from weko_groups.api import PrivacyPolicy

    assert PrivacyPolicy.validate(PrivacyPolicy.PUBLIC)
    assert PrivacyPolicy.validate(PrivacyPolicy.MEMBERS)
    assert PrivacyPolicy.validate(PrivacyPolicy.ADMINS)
    assert not PrivacyPolicy.validate("INVALID")


def test_privacy_policy_describe():
    """Test policy describe."""
    from weko_groups.api import PrivacyPolicy

    assert PrivacyPolicy.describe(PrivacyPolicy.PUBLIC)
    assert PrivacyPolicy.describe(PrivacyPolicy.MEMBERS)
    assert PrivacyPolicy.describe(PrivacyPolicy.ADMINS)
    assert PrivacyPolicy.describe("INVALID") is None


def test_membership_state_validate():
    """Test policy validation."""
    from weko_groups.api import MembershipState
    assert MembershipState.validate(MembershipState.PENDING_ADMIN)
    assert MembershipState.validate(MembershipState.PENDING_USER)
    assert MembershipState.validate(MembershipState.ACTIVE)
    assert not MembershipState.validate("INVALID")


def test_group_creation(app):
    """Test creation of groups."""
    with app.app_context():
        from weko_groups.models import Group, \
            GroupAdmin, Membership, SubscriptionPolicy, PrivacyPolicy

        g = Group.create(name="test")
        assert g.name == 'test'
        assert g.description == ''
        assert g.subscription_policy == SubscriptionPolicy.APPROVAL
        assert g.privacy_policy == PrivacyPolicy.MEMBERS
        assert not g.is_managed
        assert g.created
        assert g.modified
        assert GroupAdmin.query.count() == 0
        assert Membership.query.count() == 0

        g2 = Group.create(
            name="admintest",
            description="desc",
            subscription_policy=SubscriptionPolicy.OPEN,
            privacy_policy=PrivacyPolicy.PUBLIC,
            is_managed=True,
            admins=[g]
        )
        assert g2.name == 'admintest'
        assert g2.description == 'desc'
        assert g2.subscription_policy == SubscriptionPolicy.OPEN
        assert g2.privacy_policy == PrivacyPolicy.PUBLIC
        assert g2.is_managed
        assert g2.created
        assert g2.modified
        assert GroupAdmin.query.count() == 1
        admin = g2.admins[0]
        assert admin.admin_type == 'Group'
        assert admin.admin_id == g.id
        assert Membership.query.count() == 0


def test_group_creation_existing_name(app):
    """
    Test what happens if group with identical name is created.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group

        g = Group.create(name="test", )
        with pytest.raises(IntegrityError):
            Group.create(name="test", admins=[g])


def test_group_creation_signals(app):
    """
    Test signals sent after creation.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group

        Group.called = False

        @event.listens_for(Group, 'after_insert')
        def _receiver(mapper, connection, target):
            Group.called = True
            assert isinstance(target, Group)
            assert target.name == 'signaltest'

        Group.create(name="signaltest")
        assert Group.called

        Group.called = False
        with pytest.raises(IntegrityError):
            Group.create(name="signaltest")
        assert not Group.called

        event.remove(Group, 'after_insert', _receiver)


def test_group_creation_invalid_data(app):
    """
    Test what happens if group with invalid data is created.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group

        with pytest.raises(AssertionError):
            Group.create(name="")
        with pytest.raises(AssertionError):
            Group.create(name="test", privacy_policy='invalid')
        with pytest.raises(AssertionError):
            Group.create(name="test", subscription_policy='invalid')
        assert Group.query.count() == 0


def test_group_delete(app):
    """
    Test deletion of a group.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin, Membership
        from invenio_accounts.models import User

        g1 = Group.create(name="test1")
        g2 = Group.create(name="test2", admins=[g1])
        u = User(email="test@test.test", password="test")
        db.session.add(u)
        db.session.commit()

        g2.add_member(u)

        # Group is admin of another group, which will be left without admins
        g1.delete()
        assert Group.query.count() == 1
        assert GroupAdmin.query.count() == 0
        assert Membership.query.count() == 1

        g2.delete()
        assert Group.query.count() == 0
        assert GroupAdmin.query.count() == 0
        assert Membership.query.count() == 0


def test_group_update(app):
    """
    Test update of a group.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, SubscriptionPolicy, \
            PrivacyPolicy

        g = Group.create(name="test")
        m = g.modified
        g.update(
            name="test-change",
            description="changed",
            subscription_policy=SubscriptionPolicy.OPEN,
            privacy_policy=PrivacyPolicy.MEMBERS,
            is_managed=True,
        )

        assert g.name == 'test-change'
        assert g.description == 'changed'
        assert g.subscription_policy == SubscriptionPolicy.OPEN
        assert g.privacy_policy == PrivacyPolicy.MEMBERS
        assert g.is_managed
        assert m is not g.modified
        assert g.created


def test_group_update_duplicated_names(app):
    """
    Test duplicated name of group update.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group

        g = Group.create(name="test")
        Group.create(name="test-change")
        assert Group.query.count() == 2
        with pytest.raises(IntegrityError):
            g.update(name="test-change")


def test_group_get_by_name(app):
    """
    Test group get bu name..

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group

        Group.create(name="test1")
        Group.create(name="test2")

        assert Group.get_by_name("test1").name == "test1"
        assert Group.get_by_name("invalid") is None


def test_group_query_by_names(app):
    """
    Test query by names.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group

        Group.create(name="test1")
        Group.create(name="test2")
        Group.create(name="test3")

        with pytest.raises(AssertionError):
            Group.query_by_names('test1')

        assert Group.query_by_names(["invalid"]).count() == 0
        assert Group.query_by_names(["test1"]).count() == 1
        assert Group.query_by_names(["test2", "invalid"]).count() == 1
        assert Group.query_by_names(["test1", "test2"]).count() == 2


def test_group_query_by_user(app):
    """
    Test query by user.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            GroupAdmin, MembershipState
        from invenio_accounts.models import User

        u1 = User(email="test1@test1.test1", password="test1")
        u2 = User(email="test2@test2.test2", password="test2")
        u3 = User(email="test3@test3.test3", password="test3")
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()
        g1 = Group.create(name="test1", admins=[u1])
        g2 = Group.create(name="test2", admins=[u1])

        g1.add_member(u2, state=MembershipState.PENDING_ADMIN)
        g1.add_member(u3, state=MembershipState.ACTIVE)
        g2.add_member(u2, state=MembershipState.ACTIVE)

        assert Group.query.count() == 2
        assert GroupAdmin.query.count() == 2
        assert Membership.query.count() == 3
        assert Group.query_by_user(u1).count() == 2
        assert Group.query_by_user(u1, with_pending=True).count() == 2
        assert Group.query_by_user(u2).count() == 1
        assert Group.query_by_user(u2, with_pending=True).count() == 2
        assert Group.query_by_user(u3).count() == 1
        assert Group.query_by_user(u3, with_pending=True).count() == 1
        assert 1 == Group.query_by_user(
            u3, with_pending=True, eager=[Group.members]).count()


def test_group_add_admin(app):
    """
    Test add group admin.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin

        a = Group.create(name="admin")
        g = Group.create(name="test")

        obj = g.add_admin(a)

        assert isinstance(obj, GroupAdmin)
        assert GroupAdmin.query.count() == 1
        with pytest.raises(IntegrityError):
            g.add_admin(a)


def test_group_remove_admin(app):
    """
    Test remove group admin.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin

        a = Group.create(name="admin")
        g = Group.create(name="test", admins=[a])

        assert GroupAdmin.query.count() == 1

        g.remove_admin(a)

        assert GroupAdmin.query.count() == 0
        with pytest.raises(NoResultFound):
            g.remove_admin(a)


def test_group_add_member(app):
    """
    Test add group member.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership
        from invenio_accounts.models import User

        g = Group.create(name="test1")
        u = User(email="test@test.test", password="test")
        db.session.add(u)
        db.session.commit()

        obj = g.add_member(u)

        assert isinstance(obj, Membership)
        assert Group.query.count() == 1
        assert Membership.query.count() == 1
        with pytest.raises(FlushError):
            g.add_member(u)


def test_group_remove_member(app):
    """
    Test remove group member.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership
        from invenio_accounts.models import User

        g = Group.create(name="test1")
        u = User(email="test@test.test", password="test")
        db.session.add(u)
        db.session.commit()

        g.add_member(u)

        assert Membership.query.count() == 1

        g.remove_member(u)

        assert Membership.query.count() == 0
        assert g.remove_member(u) is None


def test_group_invite(app):
    """
    Test group invite.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            MembershipState
        from invenio_accounts.models import User

        g = Group.create(name="test")
        u = User(email="test@inveniosoftware.org", password="123456")
        u2 = User(email="test2@inveniosoftware.org", password="123456")
        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        m = g.invite(u)
        assert Membership.query.count() == 1
        assert m.state == MembershipState.PENDING_USER

        a = Group.create(name="admin")
        g2 = Group.create(name="test2", admins=[a])
        assert g2.invite(u2, admin=g) is None
        m = g2.invite(u2, admin=a)
        assert Membership.query.count() == 2
        assert m.state == MembershipState.PENDING_USER


def test_group_subscribe(app):
    """
    Test group subscribe.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, SubscriptionPolicy, \
            Membership, MembershipState
        from invenio_accounts.models import User

        g_o = Group.create(name="test_open",
                           subscription_policy=SubscriptionPolicy.OPEN)
        g_a = Group.create(name="test_approval",
                           subscription_policy=SubscriptionPolicy.APPROVAL)
        g_c = Group.create(name="test_closed",
                           subscription_policy=SubscriptionPolicy.CLOSED)
        u = User(email="test", password="test")
        db.session.add(u)
        db.session.commit()

        m_o = g_o.subscribe(u)
        m_c = g_c.subscribe(u)
        m_a = g_a.subscribe(u)

        assert m_c is None
        assert m_a.state == MembershipState.PENDING_ADMIN
        assert m_o.state == MembershipState.ACTIVE
        assert Membership.query.count() == 2


def test_group_is_admin(app):
    """
    Test if group is admin.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group
        from invenio_accounts.models import User

        g = Group.create(name="test")
        u = User(email="test", password="test")
        db.session.add(u)
        db.session.commit()

        g.add_admin(u)

        assert g.is_admin(u)

        a = Group.create(name="admin")
        g = Group.create(name="test2", admins=[a])
        assert g.is_admin(a)


def test_group_is_member(app):
    """
    Test if group is member.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group
        from invenio_accounts.models import User

        g = Group.create(name='test_group')
        u = User(email='test@example.com', password='test_password')
        u2 = User(email='test2@example.com', password='test_password')
        u3 = User(email='test3@example.com', password='test_password')
        db.session.add(u)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()

        g.add_member(u)
        g.add_member(u2, state=MembershipState.PENDING_USER)
        g.add_member(u3, state=MembershipState.PENDING_ADMIN)

        assert g.is_member(u)
        assert not g.is_member(u2)
        assert g.is_member(u2, with_pending=True)
        assert not g.is_member(u3)
        assert g.is_member(u3, with_pending=True)


def test_membership_create(app):
    """
    Test membership create.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            MembershipState
        from invenio_accounts.models import User

        g = Group.create(name="test")
        u = User(email="test@test.test", password="test")
        db.session.add(u)
        db.session.commit()

        m = Membership.create(g, u)
        assert m.state == MembershipState.ACTIVE
        assert m.group.name == g.name
        assert m.user.id == u.id
        with pytest.raises(FlushError):
            Membership.create(g, u)


def test_membership_delete(app):
    """
    Test membership delete.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership
        from invenio_accounts.models import User

        g = Group.create(name="test")
        u = User(email="test@test.test", password="test")
        db.session.add(u)
        db.session.commit()

        Membership.create(g, u)
        assert Membership.query.count() == 1
        Membership.delete(g, u)
        assert Membership.query.count() == 0
        assert Membership.delete(g, u) is None


def test_membership_get(app):
    """
    Test membership get.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership
        from invenio_accounts.models import User

        g = Group.create(name="test")
        u = User(email="test@test.test", password="test")
        u2 = User(email="test2@test2.test2", password="test")
        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        Membership.create(g, u)
        m = Membership.get(g, u)
        m2 = Membership.get(g, u2)

        assert m.group.id == g.id
        assert m.user.id == u.id
        assert m2 is None


def test_membership_query_by_user(app):
    """
    Test membership query by user.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            MembershipState
        from invenio_accounts.models import User
        from flask_sqlalchemy import BaseQuery

        g = Group.create(name="test")
        u = User(email="test@test.test", password="test")
        u2 = User(email="test2@test2.test2", password="test2")
        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        Membership.create(g, u, MembershipState.ACTIVE)

        assert isinstance(Membership.query_by_user(u), BaseQuery)
        assert Membership.query_by_user(u).count() == 1
        assert Membership.query_by_user(u2).count() == 0


def test_membership_query_invitations(app):
    """
    Test membership query invitations.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            MembershipState
        from invenio_accounts.models import User
        from flask_sqlalchemy import BaseQuery

        g = Group.create(name="test")
        u1 = User(email="test@test.test", password="test")
        u2 = User(email="test2@test2.test2", password="test2")
        u3 = User(email="test3@test3.test3", password="test3")
        db.session.add_all([u1, u2, u3])
        db.session.commit()
        Membership.create(g, u1, MembershipState.ACTIVE)
        Membership.create(g, u2, MembershipState.PENDING_USER)
        Membership.create(g, u3, MembershipState.PENDING_ADMIN)

        assert isinstance(Membership.query_by_user(u1), BaseQuery)
        assert Membership.query_invitations(u1).count() == 0
        assert Membership.query_invitations(u2).count() == 1
        assert Membership.query_invitations(u3).count() == 0


def test_membership_query_requests(app):
    """
    Test membership query requests.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            MembershipState
        from invenio_accounts.models import User
        from flask_sqlalchemy import BaseQuery

        a = User(email="admin@admin.admin", password="admin")
        u1 = User(email="test@test.test", password="test")
        u2 = User(email="test2@test2.test2", password="test2")
        db.session.add_all([a, u1, u2])
        db.session.commit()
        g = Group.create(name="test", admins=[a])
        Membership.create(g, u1, MembershipState.PENDING_ADMIN)
        Membership.create(g, u2, MembershipState.PENDING_USER)

        assert isinstance(Membership.query_requests(u1), BaseQuery)
        assert Membership.query_requests(a).count() == 1

        ad = Group.create(name="admin")
        g2 = Group.create(name="test2", admins=[ad])
        u3 = User(email="test3@test3.test3", password="test3")
        u4 = User(email="test4@test4.test4", password="test4")
        u5 = User(email="test5@test5g.test5", password="test5")
        db.session.add_all([u3, u4, u5])
        db.session.commit()
        Membership.create(ad, u3, MembershipState.ACTIVE)
        Membership.create(g2, u4, MembershipState.PENDING_ADMIN)
        Membership.create(g2, u5, MembershipState.PENDING_USER)

        assert Membership.query_requests(u3).count() == 1


def test_membership_query_by_group(app):
    """
    Test membership query by group.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            MembershipState
        from invenio_accounts.models import User
        from flask_sqlalchemy import BaseQuery

        g = Group.create(name="test")
        Group.create(name="test2")
        u = User(email="test@test.test", password="test")
        u2 = User(email="test2@test2.test2", password="test2")
        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        Membership.create(g, u, MembershipState.ACTIVE)
        assert isinstance(Membership.query_by_group(g), BaseQuery)
        assert 1 == Membership.query_by_group(g).count()
        assert 0 == Membership.query_by_user(u2).count()


def test_membership_accept(app):
    """
    Test membership accept.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership, \
            MembershipState
        from invenio_accounts.models import User

        g = Group.create(name="test")
        u = User(email="test@test.test", password="test")
        db.session.add(u)
        db.session.commit()

        m = Membership.create(g, u, MembershipState.PENDING_ADMIN)
        m.accept()

        assert m.state == MembershipState.ACTIVE
        assert m.is_active()


def test_membership_reject(app):
    """
    Test membership reject.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, Membership
        from invenio_accounts.models import User

        g = Group.create(name="test")
        u = User(email="test@test.test", password="test")
        db.session.add(u)
        db.session.commit()

        m = Membership.create(g, u)
        m.reject()

        assert Membership.query.count() == 0


def test_group_admin_create(app):
    """
    Test group admin create.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin
        a = Group.create(name="admin")
        g = Group.create(name="test")

        ga = GroupAdmin.create(g, a)

        assert ga.admin_type == 'Group'
        assert ga.admin_id == a.id
        assert ga.group.id == g.id
        assert GroupAdmin.query.count() == 1


def test_group_admin_delete(app):
    """
    Test group admin delete.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin
        a = Group.create(name="admin")
        g = Group.create(name="test")

        ga = GroupAdmin.create(g, a)

        assert ga.admin_type == 'Group'
        assert ga.admin_id == a.id
        assert ga.group.id == g.id
        assert GroupAdmin.query.count() == 1

        GroupAdmin.delete(g, a)
        assert GroupAdmin.query.count() == 0


def test_group_admin_query_by_group(app):
    """
    Test group admin query by group.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin
        from flask_sqlalchemy import BaseQuery

        a = Group.create(name="admin")
        g = Group.create(name="test", admins=[a])
        g2 = Group.create(name="test2")

        assert isinstance(GroupAdmin.query_by_group(g), BaseQuery)
        assert GroupAdmin.query_by_group(g).count() == 1
        assert GroupAdmin.query_by_group(g2).count() == 0


def test_group_admin_query_by_admin(app):
    """
    Test group admin query by admin.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin
        from flask_sqlalchemy import BaseQuery

        a = Group.create(name="admin")
        g = Group.create(name="test", admins=[a])

        assert isinstance(GroupAdmin.query_by_admin(a), BaseQuery)
        assert GroupAdmin.query_by_admin(a).count() == 1
        assert GroupAdmin.query_by_admin(g).count() == 0


def test_group_admin_query_admins_by_group_ids(app):
    """
    Test group admin query admins by group ids.

    :param app: The flask application.
    """
    with app.app_context():
        from weko_groups.models import Group, GroupAdmin
        from sqlalchemy.orm.query import Query

        a = Group.create(name="admin")
        g = Group.create(name="test", admins=[a])

        assert isinstance(GroupAdmin.query_admins_by_group_ids([g.id]), Query)
        assert 1 == GroupAdmin.query_admins_by_group_ids([g.id]).count()
        assert 0 == GroupAdmin.query_admins_by_group_ids([a.id]).count()
        with pytest.raises(AssertionError):
            GroupAdmin.query_admins_by_group_ids('invalid')

    with app.app_context():
        from weko_groups.models import Group, GroupAdmin
        from sqlalchemy.orm.query import Query

        b = Group.create(name="admin2")
        c = Group.create(name="admin3")
        g = Group.create(name="test", admins=[b,c])
        h = Group.create(name="test2", admins=[b,c])
        
        assert 0 == GroupAdmin.query_admins_by_group_ids([b.id]).count()
        assert 0 == GroupAdmin.query_admins_by_group_ids([c.id]).count()
        assert 1 == GroupAdmin.query_admins_by_group_ids([g.id]).count()
        assert 2 == GroupAdmin.query_admins_by_group_ids([g.id, h.id]).count()
        assert 2 == GroupAdmin.query_admins_by_group_ids(None).count()

def test_invite_by_emails(app):
    """
    Test invite by emails.

    :param app: The flask application.
    """
    with app.app_context():
        u1 = User(email='test@example.com', password='test_password')
        u2 = User(email='test2@example.com', password='test_password')
        g = Group.create(name='test_group')

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        result = g.invite_by_emails(
            [
                u1.email,
                u2.email,
                'invalid@example.com'
            ]
        )

        assert result[0].state.code is MembershipState.PENDING_USER
        assert result[1].state.code is MembershipState.PENDING_USER
        assert result[2] is None

        assert g.is_member(u1, with_pending=True)
        assert g.is_member(u2, with_pending=True)
        assert not g.is_member('invalid@example.com', with_pending=True)


def test_can_see_members(example_group):
    """
    Test can see members.

    :param example_group:
    """
    app = example_group
    with app.app_context():
        group = app.get_group()
        admin = app.get_admin()
        member = app.get_member()
        non_member = app.get_non_member()

        assert group.is_member(member)
        assert group.is_admin(admin)
        assert not group.is_member(non_member)

        group.privacy_policy = PrivacyPolicy.ADMINS
        assert group.can_see_members(admin)
        assert not group.can_see_members(member)
        assert not group.can_see_members(non_member)

        group.privacy_policy = PrivacyPolicy.MEMBERS
        assert group.can_see_members(admin)
        assert group.can_see_members(member)
        assert not group.can_see_members(non_member)

        group.privacy_policy = PrivacyPolicy.PUBLIC
        assert group.can_see_members(admin)
        assert group.can_see_members(member)
        assert group.can_see_members(non_member)


def test_can_edit(example_group):
    """
    Test can edit.

    :param example_group:
    """
    app = example_group
    with app.app_context():
        group = app.get_group()
        admin = app.get_admin()
        member = app.get_member()
        non_member = app.get_non_member()

        assert group.can_edit(admin)
        assert not group.can_edit(member)
        assert not group.can_edit(non_member)

        group.is_managed = True
        assert not group.can_edit(admin)
        assert not group.can_edit(member)
        assert not group.can_edit(non_member)


def test_can_invite_others(example_group):
    """
    Test can invite others.

    :param example_group:
    """
    app = example_group
    with app.app_context():
        group = app.get_group()
        admin = app.get_admin()
        member = app.get_member()
        non_member = app.get_non_member()

        group.subscription_policy = SubscriptionPolicy.OPEN
        assert group.can_invite_others(admin)
        assert group.can_invite_others(member)
        assert group.can_invite_others(non_member)

        group.subscription_policy = SubscriptionPolicy.APPROVAL
        assert group.can_invite_others(admin)
        assert group.can_invite_others(member)
        assert group.can_invite_others(non_member)

        group.subscription_policy = SubscriptionPolicy.CLOSED
        assert group.can_invite_others(admin)
        assert not group.can_invite_others(member)
        assert not group.can_invite_others(non_member)

        group.is_managed = True
        assert not group.can_invite_others(admin)
        assert not group.can_invite_others(member)
        assert not group.can_invite_others(non_member)


def test_can_leave(example_group):
    """
    Test can leave.

    :param example_group:
    """
    app = example_group
    with app.app_context():
        group = app.get_group()
        admin = app.get_admin()
        member = app.get_member()
        non_member = app.get_non_member()

        group.is_managed = False
        assert not group.can_leave(admin)
        assert group.can_leave(member)
        assert not group.can_leave(non_member)

        group.is_managed = True
        assert not group.can_leave(admin)
        assert not group.can_leave(member)
        assert not group.can_leave(non_member)


def test_members_count(example_group):
    """
    Test members count.

    :param example_group:
    """
    app = example_group
    with app.app_context():
        non_member = app.get_non_member()
        group = app.get_group()

        assert group.members_count() == 1
        group.add_member(non_member)
        assert group.members_count() == 2


def test_group_search(example_group):
    """
    Test group search.

    :param example_group:
    """
    app = example_group
    with app.app_context():
        group = app.get_group()
        assert group == Group.search(Group.query, 'test_group').one()
        assert group == Group.search(Group.query, '_group').one()
        assert group == Group.search(Group.query, '_group').one()
        assert group == Group.search(Group.query, 'st_gro').one()


def test_membership_search(example_group):
    """
    Test membership search.

    :param example_group:
    """
    app = example_group
    with app.app_context():
        member = app.get_member()

        assert member.get_id() == str(Membership.search(
            Membership.query, 'test2@example.com').one().user_id)
        assert member.get_id() == str(Membership.search(
            Membership.query, '@example.com').one().user_id)
        assert member.get_id() == str(Membership.search(
            Membership.query, 'test2@example').one().user_id)
        assert member.get_id() == str(Membership.search(
            Membership.query, '@example').one().user_id)

# .tox/c1/bin/pytest --cov=weko_groups tests/test_models.py::test_function_issue34801 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-groups/.tox/c1/tmp
def test_function_issue34801(app):
    with app.app_context():
        from weko_groups.models import Group, \
            GroupAdmin, Membership, SubscriptionPolicy, PrivacyPolicy
        from weko_groups.views import get_group_name

        g = Group.create(name="test<script>alert()</script>")
        assert g.name == "test<script>alert()</script>"
        result = get_group_name(g.id)
        assert result == "test&lt;script&gt;alert()&lt;/script&gt;"
        assert g.escape_name == "test&lt;script&gt;alert()&lt;/script&gt;"
        assert g.name == "test<script>alert()</script>"


# class Group(db.Model): 
# def get_group_list(cls):
def test_get_group_list(app):
    from weko_groups.models import Group

    with app.app_context():
        group = Group.create(name="test")
        test = Group()

        assert test.get_group_list() != None


# def _escape_value(self,text): 
def test__escape_value(app):
    with app.app_context():
        test = Group()
        text = {}

        # Exception coverage
        try:
            assert test._escape_value(text=text) != None
        except:
            pass


# def _filter(cls, query, state=MembershipState.ACTIVE, eager=None):
def test__filter(app):
    def filter_by(state="state"):
        filter_by_magicmock = MagicMock()
        filter_by_magicmock.options = MagicMock()
        return filter_by_magicmock

    with app.app_context():
        test = Membership()
        query = MagicMock()
        query.filter_by = filter_by
        eager = [""]

        with patch('weko_groups.models.joinedload', return_value=""):
            assert test._filter(query=query, eager=eager) != None
        

# def query_invitations(cls, user, eager=False):
def test_query_invitations(app):
    def query_by_user(item1, item2, item3):
        return True
    
    def get_id():
        return "id"

    with app.app_context():
        test = Membership()
        test.query_by_user = query_by_user
        user = MagicMock()
        user.get_id = get_id
        eager = True

        assert test.query_invitations(user=user, eager=eager) != None


# def query_requests(cls, admin): 
def test_query_requests(app):
    def is_superadmin():
        return "is_superadmin"

    with app.app_context():
        test = Membership()
        admin = MagicMock()
        admin.is_superadmin = is_superadmin

        assert test.query_requests(admin=admin) != None


# def query_by_group(cls, group_or_id, with_invitations=False, **kwargs): 
def test_query_by_group(app):
    with app.app_context():
        test = Membership()
        group = Group()

        assert test.query_by_group(group_or_id=group, with_invitations=True) != None


# def order(cls, query, field, s): 
def test_order(app):
    def order_by(item):
        return "item"
    
    with app.app_context():
        test = Membership()
        query = MagicMock()
        query.order_by = order_by
        field = "field_test"

        s = "asc"
        assert test.order(query=query, field=field, s=s) != None

        s = "desc"
        assert test.order(query=query, field=field, s=s) != None
