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

"""Tests for the open_restricted permission / onetime-download quota fix.

These tests cover:
  * weko_records_ui.utils.get_valid_onetime_download
  * weko_records_ui.models.FileOnetimeDownload.consume_one
  * weko_records_ui.permissions.is_privileged_file_access
  * weko_records_ui.permissions.check_open_restricted_permission
  * weko_records_ui.permissions.check_file_download_permission

They use real DB-backed fixtures (see conftest.py: full_app/db/users/
super_user/community_user) rather than mocks, since InvenioAccounts gives
us a real flask_login-compatible current_user cheaply. A fresh
``full_app.test_request_context()`` plus ``flask_login.utils.login_user``
is used to control the authenticated user for each assertion, mirroring
the pattern already used in modules/invenio-files-rest/tests (see its
testutils.login_user, which does the same thing via a session transaction
on a test client instead of a bare request context).
"""

from datetime import datetime, timedelta

from flask_login import current_user
from flask_login.utils import login_user

from weko_records_ui.models import FileOnetimeDownload
from weko_records_ui.permissions import check_file_download_permission, \
    check_open_restricted_permission, is_privileged_file_access
from weko_records_ui.utils import get_valid_onetime_download


# ---------------------------------------------------------------------------
# get_valid_onetime_download()
# ---------------------------------------------------------------------------

def test_get_valid_onetime_download_no_row(db, users):
    """No FileOnetimeDownload row at all for the tuple => None."""
    assert get_valid_onetime_download(
        'f.pdf', '1', users['other'].email) is None


def test_get_valid_onetime_download_usable(db, users):
    """download_count > 0 and not expired => the grant is returned."""
    grant = FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=3, expiration_date=30)
    found = get_valid_onetime_download('f.pdf', '1', users['other'].email)
    assert found is not None
    assert found.id == grant.id


def test_get_valid_onetime_download_exhausted(db, users):
    """download_count == 0 => None, even though not expired."""
    FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=0, expiration_date=30)
    assert get_valid_onetime_download(
        'f.pdf', '1', users['other'].email) is None


def test_get_valid_onetime_download_expired(db, users):
    """Expired grant (created + expiration_date days < now) => None,
    even though download_count > 0.
    """
    grant = FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=5, expiration_date=1)
    # Force it into the past: expiration_date=1 day, backdate `created`
    # by 2 days so `now >= created + timedelta(days=1)`.
    grant.created = datetime.utcnow() - timedelta(days=2)
    db.session.merge(grant)
    db.session.commit()
    assert get_valid_onetime_download(
        'f.pdf', '1', users['other'].email) is None


def test_get_valid_onetime_download_skips_unusable_newer_grant(db, users):
    """Multiple grants for the same tuple: find() returns newest-first
    (desc(id)); the loop in get_valid_onetime_download must skip an
    exhausted/expired *newer* row and fall through to an older, still
    usable one.
    """
    older_usable = FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=2, expiration_date=30)
    newer_exhausted = FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=0, expiration_date=30)
    assert newer_exhausted.id > older_usable.id

    found = get_valid_onetime_download('f.pdf', '1', users['other'].email)
    assert found is not None
    assert found.id == older_usable.id


# ---------------------------------------------------------------------------
# FileOnetimeDownload.consume_one()
# ---------------------------------------------------------------------------

def test_consume_one_decrements_when_quota_remains(db, users):
    grant = FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=2, expiration_date=30)
    assert FileOnetimeDownload.consume_one(grant.id) is True
    db.session.refresh(grant)
    assert grant.download_count == 1


def test_consume_one_returns_false_when_exhausted(db, users):
    grant = FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=0, expiration_date=30)
    assert FileOnetimeDownload.consume_one(grant.id) is False
    db.session.refresh(grant)
    # Must not go negative.
    assert grant.download_count == 0


def test_consume_one_returns_false_for_missing_id(db, users):
    assert FileOnetimeDownload.consume_one(999999) is False


# ---------------------------------------------------------------------------
# is_privileged_file_access()
# ---------------------------------------------------------------------------

def test_is_privileged_file_access_owner(full_app, users):
    record = {'owner': str(users['owner'].id)}
    with full_app.test_request_context():
        login_user(users['owner'])
        assert is_privileged_file_access(record) is True


def test_is_privileged_file_access_shared_user(full_app, users):
    # Note: unlike 'owner', 'weko_shared_id' is compared without casting to
    # int in permissions.py, so it must match current_user.id's type (int).
    record = {'weko_shared_id': users['shared'].id}
    with full_app.test_request_context():
        login_user(users['shared'])
        assert is_privileged_file_access(record) is True


def test_is_privileged_file_access_super_role(full_app, super_user):
    record = {}
    with full_app.test_request_context():
        login_user(super_user)
        assert is_privileged_file_access(record) is True


def test_is_privileged_file_access_community_role(full_app, community_user):
    record = {}
    with full_app.test_request_context():
        login_user(community_user)
        assert is_privileged_file_access(record) is True


def test_is_privileged_file_access_plain_user(full_app, users):
    # 'other' is neither owner nor shared user nor holds a super/community
    # role for this record.
    record = {'owner': str(users['owner'].id)}
    with full_app.test_request_context():
        login_user(users['other'])
        assert is_privileged_file_access(record) is False


def test_is_privileged_file_access_not_authenticated(full_app, users):
    record = {'owner': str(users['owner'].id)}
    with full_app.test_request_context():
        assert current_user.is_authenticated is False
        assert is_privileged_file_access(record) is False


# ---------------------------------------------------------------------------
# check_open_restricted_permission()
# ---------------------------------------------------------------------------

def test_check_open_restricted_permission_not_authenticated(full_app):
    record = {'recid': '1'}
    fjson = {'filename': 'f.pdf'}
    with full_app.test_request_context():
        assert check_open_restricted_permission(record, fjson) is False


def test_check_open_restricted_permission_no_grant(full_app, users):
    record = {'recid': '1'}
    fjson = {'filename': 'f.pdf'}
    with full_app.test_request_context():
        login_user(users['other'])
        assert check_open_restricted_permission(record, fjson) is False


def test_check_open_restricted_permission_usable_grant(full_app, db, users):
    FileOnetimeDownload.create(
        file_name='f.pdf', user_mail=users['other'].email, record_id='1',
        download_count=1, expiration_date=30)
    record = {'recid': '1'}
    fjson = {'filename': 'f.pdf'}
    with full_app.test_request_context():
        login_user(users['other'])
        assert check_open_restricted_permission(record, fjson) is True


# ---------------------------------------------------------------------------
# check_file_download_permission()
# ---------------------------------------------------------------------------

def test_check_file_download_permission_privileged_owner_bypasses_quota(
        full_app, users):
    """An owner gets True regardless of accessrole/quota: this exercises
    the refactored early-return that now goes through
    is_privileged_file_access() instead of the inline owner/super-role
    checks that used to live directly in check_file_download_permission.
    """
    record = {'owner': str(users['owner'].id)}
    fjson = {'accessrole': 'open_restricted', 'filename': 'f.pdf'}
    with full_app.test_request_context():
        login_user(users['owner'])
        assert check_file_download_permission(record, fjson) is True


def test_check_file_download_permission_open_restricted_no_grant(
        full_app, users):
    """A non-privileged user with an open_restricted file and no onetime
    grant is correctly delegated to check_open_restricted_permission(),
    which denies access.
    """
    record = {'owner': str(users['owner'].id), 'recid': '1'}
    fjson = {'accessrole': 'open_restricted', 'filename': 'f.pdf'}
    with full_app.test_request_context():
        login_user(users['other'])
        assert check_file_download_permission(record, fjson) is False
