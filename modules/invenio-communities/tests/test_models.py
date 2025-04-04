# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Model functions tests."""

from __future__ import absolute_import, print_function

import os
import pytest
from datetime import datetime, timedelta
from invenio_records.api import Record
from mock import patch
from invenio_oaiserver.models import OAISet

from invenio_communities.models import Community,InclusionRequest
from invenio_communities.errors import InclusionRequestExistsError,InclusionRequestObsoleteError,InclusionRequestExpiryTimeError


@pytest.mark.parametrize('case_modifier', [
    (lambda x: x),
    (lambda x: x.upper()),
    (lambda x: x[0].upper() + x[1:]),
])
def test_filter_community(app, db, communities_for_filtering, user,
                          case_modifier):
    """Test the community filter task."""
    (comm0, comm1, comm2) = communities_for_filtering

    # Case insensitive
    results = Community.filter_communities(
                p=case_modifier('beautiful'),
                so='title').all()
    assert len(results) == 1
    assert {c.id for c in results} == {comm0.id}

    # Keyword search
    results = Community.filter_communities(
                p=case_modifier('errors'),
                so='title').all()
    assert len(results) == 1
    assert {c.id for c in results} == {comm2.id}

    # Partial keyword present
    results = Community.filter_communities(
                p=case_modifier('test'),
                so='title').all()
    assert len(results) == 3
    assert {c.id for c in results} == {comm0.id,
                                       comm1.id, comm2.id}

    # Order matter
    results = Community.filter_communities(
                p=case_modifier('explicit implicit'),
                so='title').all()
    assert len(results) == 1
    assert {c.id for c in results} == {comm0.id}

    results = Community.filter_communities(
                p=case_modifier('implicit explicit'),
                so='title').all()
    assert len(results) == 0
    assert {c.id for c in results} == set()

def test_get_by_root_node_id(app, db, communities):
    root_node_id = communities[0].root_node_id
    assert (Community.get_by_root_node_id(root_node_id) != None)
    assert (Community.get_by_root_node_id(root_node_id, True) != None)

# class InclusionRequest(db.Model, Timestamp):
class TestInclusionRequest:
#     def get_record(self):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestInclusionRequest::test_get_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_record(self,db,db_records,communities,users):
        record = db_records[2]
        record_id = record.id
        comm = communities[0]
        increq = InclusionRequest(
            id_community=comm.id,
            id_record=record.id,
            user=users[2]["obj"]
        )
        db.session.add(increq)
        db.session.commit()

        result = increq.get_record()
        assert result.id == record_id
#     def delete(self):
#     def create(cls, community, record, user=None, expires_at=None,
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestInclusionRequest::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_create(self,db,db_records,communities,users,mocker):
        mocker.patch("invenio_records.api.before_record_update.send")
        mocker.patch("invenio_records.api.after_record_update.send")
        record = db_records[2]
        comm = communities[0]
        increq = InclusionRequest.create(
            community=comm,
            record=record,
            user=users[2]["obj"]
        )
        assert increq

        # raise IntegrityError

        with pytest.raises(InclusionRequestExistsError) as e:
            increq = InclusionRequest.create(
                community=comm,
                record=record,
                user=users[2]["obj"],
                #expires_at=expires_at
            )
        assert e.value.community==comm
        assert e.value.record == record

        # commnity.has_record is true
        rec = Record.get_record(record.id)
        rec.setdefault("communities", [])
        rec["communities"].append(comm.id)
        rec["communities"] = sorted(rec["communities"])
        rec.commit()
        db.session.commit()
        record = Record.get_record(record.id)
        with pytest.raises(InclusionRequestObsoleteError) as e:
            increq = InclusionRequest.create(
                community=comm,
                record=record,
                user=users[2]["obj"],
            )
        assert e.value.community==comm
        assert e.value.record == record

        # expires_at < datetime.utcnow
        expires_at = datetime.utcnow() + timedelta(days=-10)
        comm = communities[1]
        with pytest.raises(InclusionRequestExpiryTimeError) as e:
            increq = InclusionRequest.create(
                community=comm,
                record=record,
                user=users[2]["obj"],
                expires_at=expires_at
            )
        assert e.value.community==comm
        assert e.value.record == record


#     @classmethod
#     def get(cls, community_id, record_uuid):
#     @classmethod
#     def get_by_record(cls, record_uuid):

# class Community(db.Model, Timestamp):
class TestCommunity:
#     def __repr__(self):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_repr -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_repr(self,communities):
        for comm in communities:
            assert str(comm) == "<Community, ID: {}>".format(comm.id)

#     def create(cls, community_id, role_id, root_node_id, **data):
#     def save_logo(self, stream, filename):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_save_logo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_save_logo(self,communities):
        comm = communities[0]
        logo_filename = "weko-logo.png"
        logo = open(os.path.join(os.path.dirname(__file__),'data/weko-logo.png'),"rb")

        # success save logo
        with patch("invenio_communities.models.save_and_validate_logo",return_value=None):
            result = comm.save_logo(logo,logo_filename)
            assert result == False

        # failed save logo
        with patch("invenio_communities.models.save_and_validate_logo",return_value="png"):
            result = comm.save_logo(logo,logo_filename)
            assert result == True
            assert comm.logo_ext == "png"

#     def get(cls, community_id, with_deleted=False):
#     def get_by_user(cls, role_ids, with_deleted=False):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_get_by_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_by_user(self,communities):
        # with_deleted is false
        result = Community.get_by_user([1])
        assert "communities_community.deleted_at IS NULL" in str(result)

        # with_deleted is true
        result = Community.get_by_user([1],with_deleted=True)
        assert "communities_community.deleted_at IS NULL" not in str(result)

#     def filter_communities(cls, p, so, with_deleted=False):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_get_repositories_by_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_get_repositories_by_user(self, db, communities, users):
        user = users[0]["obj"]
        comm = communities[0]

        # matching group_id
        comm.group_id = user.roles[0].id
        db.session.commit()
        result = Community.get_repositories_by_user(user)
        assert len(result) == 1
        assert result[0].id == comm.id

        # non matching group_id
        comm.group_id = user.roles[0].id + 1
        db.session.commit()
        result = Community.get_repositories_by_user(user)
        assert len(result) == 0

        # user has no roles
        user.roles = []
        db.session.commit()
        result = Community.get_repositories_by_user(user)
        assert len(result) == 0

#     def add_record(self, record):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_add_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_add_record(self, app, db, db_records,communities,mocker):
        mocker.patch("invenio_records.api.before_record_update.send")
        mocker.patch("invenio_records.api.after_record_update.send")

        record = db_records[2]
        comm = communities[0]
        rec = Record.get_record(record.id)
        comm.add_record(rec)
        rec.commit()
        from invenio_records.models import RecordMetadata
        metadata =RecordMetadata.query.filter_by(id=record.id).one().json
        assert metadata["communities"] == ["comm1"]
        db.session.commit()

        # has_record is true, oaiset.has_record is true
        rec = Record.get_record(record.id)
        comm.add_record(rec)

        # COMMUNITIES_OAI_ENABLED is false
        app.config.update(
            COMMUNITIES_OAI_ENABLED=False
        )
        comm.add_record(rec)


#     def remove_record(self, record):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_remove_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_remove_record(self, app, db, db_records, communities, mocker):
        mocker.patch("invenio_records.api.before_record_update.send")
        mocker.patch("invenio_records.api.after_record_update.send")
        record = db_records[2]
        comm = communities[0]
        rec = Record.get_record(record.id)
        rec.setdefault("communities", [])
        rec["communities"].append(comm.id)
        rec["communities"] = sorted(rec["communities"])
        comm.oaiset.add_record(rec)
        rec.commit()
        db.session.commit()

        rec = Record.get_record(record.id)
        comm.remove_record(rec)

        # has_record is false, oaiset.has_record is false
        comm.remove_record(rec)

        # COMMUNITIES_OAI_ENABLED is false
        app.config.update(
            COMMUNITIES_OAI_ENABLED=False
        )
        comm.remove_record(rec)

#     def has_record(self, record):
#     def accept_record(self, record):
#     def reject_record(self, record):
#     def delete(self):
#     def undelete(self):

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_to_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_to_dict(self,communities):
        comm = communities[0]
        result = comm.to_dict()
        assert result["id"] == comm.id
        assert result["id_role"] == comm.id_role
        assert result["id_user"] == comm.id_user
        assert result["title"] == comm.title
        assert result["description"] == comm.description
        assert result["root_node_id"] == comm.root_node_id
        assert result["group_id"] == comm.group_id

#     def is_deleted(self):
#     def logo_url(self):
#     def community_url(self):
# # .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_community_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
#     @pytest.mark.skip(reason="")
#     def test_community_url(self, app,communities):
#         # TODO:views.ui.detailがコメントアウトされている
#         comm = communities[0]
#         result = comm.community_url
#         assert result == "http://test_server/c/comm1/detail/"

# #     def community_provisional_url(self):
# # .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_community_provisional_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
#     @pytest.mark.skip(reason="")
#     def test_community_provisional_url(self, app, communities):
#          # TODO:views.ui.curateがコメントアウトされている
#         comm = communities[0]
#         result = comm.community_provisional_url
#         assert result == "http://test_server/c/comm1/curate/"

#     def upload_url(self):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_upload_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    #@pytest.mark.skip(reason="")
    def test_upload_url(self, app, communities):
        comm = communities[0]
        result = comm.upload_url
        assert result == "http://test_server/deposit/new?c=comm1"

#     def oaiset_spec(self):
#     def oaiset(self):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_oaiset -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_oaiset(self,app, db,communities):
        comm = communities[0]
        result = comm.oaiset
        assert result.id == 1

        app.config.update(
            COMMUNITIES_OAI_ENABLED=False
        )
        result = comm.oaiset
        assert result == None

#     def oaiset_url(self):
# .tox/c1/bin/pytest --cov=invenio_communities tests/test_models.py::TestCommunity::test_oaiset_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
    def test_oaiset_url(self, app, communities):
        from invenio_oaiserver.views.server import blueprint
        app.register_blueprint(blueprint)
        comm = communities[0]
        result = comm.oaiset_url
        assert result == "http://test_server/oai?verb=ListRecords&metadataPrefix=oai_dc&set=user-comm1"
#     def version_id(self):
# class FeaturedCommunity(db.Model, Timestamp):
#         db.DateTime, nullable=False, default=datetime.utcnow)
#     @classmethod
#     def get_featured_or_none(cls, start_date=None):
