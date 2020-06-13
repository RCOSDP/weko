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


"""Module tests."""

from __future__ import absolute_import, print_function

import json
from datetime import datetime, timedelta

import pytest
from flask import Flask
from invenio_oaiserver.models import OAISet
from invenio_records.api import Record

from invenio_communities import InvenioCommunities
from invenio_communities.errors import CommunitiesError, \
    InclusionRequestExistsError, InclusionRequestMissingError, \
    InclusionRequestObsoleteError
from invenio_communities.models import Community, FeaturedCommunity, \
    InclusionRequest

try:
    from werkzeug.urls import url_parse
except ImportError:
    from urlparse import urlsplit as url_parse


def get_json(res, code=None):
    """Transform a JSON response into a dictionary."""
    if code:
        assert res.status_code == code
    return json.loads(res.get_data(as_text=True))


def assert_community_serialization(community, **kwargs):
    """Check the values of a community."""
    for key in kwargs.keys():
        assert community[key] == kwargs[key]


def test_version():
    """Test version import."""
    from invenio_communities import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioCommunities(app)
    assert 'invenio-communities' in app.extensions

    app = Flask('testapp')
    ext = InvenioCommunities()
    assert 'invenio-communities' not in app.extensions
    ext.init_app(app)
    assert 'invenio-communities' in app.extensions


def test_alembic(app, db):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    if db.engine.name == 'sqlite':
        raise pytest.skip('Upgrades are not supported on SQLite.')

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.stamp()
    ext.alembic.downgrade(target='96e796392533')
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()


def test_model_init(app, db, communities):
    """Test basic model initialization and actions."""
    (comm1, comm2, comm3) = communities
    communities_key = app.config["COMMUNITIES_RECORD_KEY"]
    # Create a record and accept it into the community by creating an
    # InclusionRequest and then calling the accept action
    rec1 = Record.create({'title': 'Foobar'})
    InclusionRequest.create(community=comm1, record=rec1)
    assert InclusionRequest.query.count() == 1
    comm1.accept_record(rec1)
    assert 'comm1' in rec1[communities_key]
    assert InclusionRequest.query.count() == 0

    # Likewise, reject a record from the community
    rec2 = Record.create({'title': 'Bazbar'})
    InclusionRequest.create(community=comm1, record=rec2)
    assert InclusionRequest.query.count() == 1
    comm1.reject_record(rec2)
    assert communities_key not in rec2  # dict key should not be created
    assert InclusionRequest.query.count() == 0

    # Add record to another community
    InclusionRequest.create(community=comm2, record=rec1)
    comm2.accept_record(rec1)
    assert communities_key in rec1
    assert len(rec1[communities_key]) == 2
    assert comm1.id in rec1[communities_key]
    assert comm2.id in rec1[communities_key]

    # Accept/reject a record to/from a community without inclusion request
    rec3 = Record.create({'title': 'Spam'})
    pytest.raises(InclusionRequestMissingError, comm1.accept_record, rec3)
    pytest.raises(InclusionRequestMissingError, comm1.reject_record, rec3)

    # Create two inclusion requests
    InclusionRequest.create(community=comm3, record=rec1)
    db.session.commit()
    db.session.flush()
    pytest.raises(InclusionRequestExistsError, InclusionRequest.create,
                  community=comm3, record=rec1)

    # Try to accept a record to a community twice (should raise)
    # (comm1 is already in rec1)
    pytest.raises(InclusionRequestObsoleteError, InclusionRequest.create,
                  community=comm1, record=rec1)


def test_email_notification(app, db, communities, user):
    """Test mail notification sending for community request."""
    app.config['COMMUNITIES_MAIL_ENABLED'] = True
    # Mock the send method of the Flask-Mail extension
    with app.extensions['mail'].record_messages() as outbox:
        (comm1, comm2, comm3) = communities
        # Create a record and accept it into the community by creating an
        # InclusionRequest and then calling the accept action
        rec1 = Record.create({
            'title': 'Foobar', 'description': 'Baz bar.'})
        InclusionRequest.create(community=comm1, record=rec1, user=user)
        assert len(outbox) == 1


def test_model_featured_community(app, db, communities):
    """Test the featured community model and actions."""
    (comm1, comm2, comm3) = communities
    t1 = datetime.now()

    # Create two community featurings starting at different times
    fc1 = FeaturedCommunity(id_community=comm1.id,
                            start_date=t1 + timedelta(days=1))
    fc2 = FeaturedCommunity(id_community=comm2.id,
                            start_date=t1 + timedelta(days=3))
    db.session.add(fc1)
    db.session.add(fc2)
    # Check the featured community at three different points in time
    assert FeaturedCommunity.get_featured_or_none(start_date=t1) is None
    assert FeaturedCommunity.get_featured_or_none(
        start_date=t1 + timedelta(days=2)) is comm1
    assert FeaturedCommunity.get_featured_or_none(
        start_date=t1 + timedelta(days=4)) is comm2


def test_oaipmh_sets(app, db, communities):
    """Test the OAI-PMH Sets creation."""
    (comm1, comm2, comm3) = communities

    assert OAISet.query.count() == 3
    oai_set1 = OAISet.query.first()
    assert oai_set1.spec == 'user-comm1'
    assert oai_set1.name == 'Title1'
    assert oai_set1.description == 'Description1'

    # Delete the community and make sure the set is also deleted
    db.session.delete(comm1)
    db.session.commit()
    assert Community.query.count() == 2
    assert OAISet.query.count() == 2


def test_communities_rest_all_communities(app, db, communities):
    """Test the OAI-PMH Sets creation."""
    with app.test_client() as client:
        response = client.get('/api/communities/')
        response_data = get_json(response)
        assert response_data['hits']['total'] == 3
        assert len(response_data['hits']['hits']) == 3

        assert set(comm.id for comm in communities) == set(
            comm['id'] for comm in response_data['hits']['hits']
        )


def test_community_delete(app, db, communities):
    """Test deletion of communities."""
    (comm1, comm2, comm3) = communities
    comm1.delete()
    assert comm1.is_deleted is True
    comm1.undelete()
    assert comm1.is_deleted is False

    # Try to undelete a community that was not marked for deletion
    pytest.raises(CommunitiesError, comm1.undelete)

    # Try to delete community twice
    comm2.delete()
    pytest.raises(CommunitiesError, comm2.delete)


def test_communities_rest_all_communities_query_and_sort(app, db, communities):
    """Test the OAI-PMH Sets creation."""
    with app.test_client() as client:
        response = client.get('/api/communities/?q=comm&sort=title')
        response_data = get_json(response)

        assert response_data['hits']['total'] == 2
        assert response_data['hits']['hits'][0]['id'] == 'comm2'
        assert response_data['hits']['hits'][1]['id'] == 'comm1'


def test_communities_rest_pagination(app, db, communities):
    """Test the OAI-PMH Sets creation."""
    def parse_path(app, path):
        """Split the path in base and real relative url.

        Needed because in Flask 0.10.1 the client doesn't take into account the
        query string in an external URL.
        """
        http_host = app.config.get('SERVER_NAME')
        app_root = app.config.get('APPLICATION_ROOT')
        url = url_parse(path)
        base_url = 'http://{0}/'.format(url.netloc or http_host or 'localhost')
        if app_root:
            base_url += app_root.lstrip('/')
        if url.netloc:
            path = url.path
            if url.query:
                path += '?' + url.query
        return dict(path=path, base_url=base_url)

    def assert_header_links(response, ref, page, size):
        """Check if there is a pagination in one of the headers."""
        assert any(all(item in h[1] for item in [
            'ref="{0}"'.format(ref),
            'page={0}'.format(page),
            'size={0}'.format(size)]) for h in response.headers)

    with app.test_client() as client:
        response = client.get('/api/communities/?size=1')
        assert_header_links(response, 'self', 1, 1)
        assert_header_links(response, 'next', 2, 1)

        data = get_json(response)
        assert 'self' in data['links']
        assert len(data['hits']['hits']) == 1

        # Assert that self gives back the same result
        response = client.get(**parse_path(app, data['links']['self']))
        assert data == get_json(response)
        assert 'prev' not in data['links']
        assert 'next' in data['links']

        # Second page
        response = client.get(**parse_path(app, data['links']['next']))
        assert_header_links(response, 'next', 3, 1)
        assert_header_links(response, 'self', 2, 1)
        assert_header_links(response, 'prev', 1, 1)

        data = get_json(response)
        assert len(data['hits']['hits']) == 1
        assert 'prev' in data['links']
        assert 'next' in data['links']

        # Third page
        response = client.get(**parse_path(app, data['links']['next']))
        assert_header_links(response, 'self', 3, 1)
        assert_header_links(response, 'prev', 2, 1)

        data = get_json(response)
        assert 'prev' in data['links']
        assert 'next' not in data['links']


def test_communities_rest_get_details(app, db, communities):
    """Test the OAI-PMH Sets creation."""
    with app.test_client() as client:
        response = client.get('/api/communities/comm1')
        assert_community_serialization(
                get_json(response),
                description='Description1',
                title='Title1',
                id='comm1',
                page='',
                curation_policy='',
                logo_url=None,
                last_record_accepted='2000-01-01T00:00:00+00:00',
                links={
                    'self': 'http://inveniosoftware.org/api/communities/comm1',
                    'html': 'http://inveniosoftware.org/communities/comm1/',
                },
        )


def test_communities_rest_etag(app, communities):
    """Test the OAI-PMH Sets creation."""
    with app.test_client() as client:
        # The first response should return the data with result code 200
        response = client.get('/api/communities/comm1')
        assert response.status_code == 200
        assert response.get_data(as_text=True) != ''

        # The second response is empty and the result code is 304
        response = client.get('/api/communities/comm1', headers=(
            ('If-None-Match', response.headers.get('ETag')),))
        assert response.status_code == 304
        assert response.get_data(as_text=True) == ''


def test_add_remove_corner_cases(app, db, communities, disable_request_email):
    """Test corner cases for community adding and removal."""
    (comm1, comm2, comm3) = communities
    communities_key = app.config["COMMUNITIES_RECORD_KEY"]
    # Create a record and create an inclusion request,
    # meanwhile adding a record manually outside the workflow
    rec1 = Record.create({'title': 'Foobar'})
    InclusionRequest.create(community=comm1, record=rec1)
    rec1[communities_key] = ['comm1', ]  # Add community manually
    assert InclusionRequest.query.count() == 1

    # Accepting record which was added manually outside the normal workflow
    comm1.accept_record(rec1)  # Should still work
    assert rec1[communities_key] == ['comm1', ]
    assert InclusionRequest.query.count() == 0
    assert comm1.oaiset.has_record(rec1)

    # Removing record which was removed manually outside the normal workflow
    rec1[communities_key] = []  # Remove community manually
    comm1.remove_record(rec1)  # Should still work
    assert communities_key in rec1
    assert len(rec1[communities_key]) == 0
    assert not comm1.oaiset.has_record(rec1)
