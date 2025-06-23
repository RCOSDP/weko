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


"""Utility functions tests."""

from __future__ import absolute_import, print_function

import pytest
import os
from mock import patch
from PIL import Image, ImageFilter
from invenio_records.api import Record
from invenio_files_rest.models import Location, Bucket, ObjectVersion

from invenio_files_rest.errors import FilesException
from sqlalchemy.orm.exc import NoResultFound
from weko_index_tree.models import Index

from invenio_communities.models import InclusionRequest, Community
from invenio_communities.utils import render_template_to_string,Pagination,save_and_validate_logo,\
    initialize_communities_bucket,format_request_email_templ,send_community_request_email,get_user_role_ids,delete_empty,get_repository_id_by_item_id

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_Pagination -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_Pagination():
    pagination = Pagination(page=2,per_page=5,total_count=50)
    assert pagination.page == 2
    assert pagination.per_page == 5
    assert pagination.total_count == 50

    assert pagination.pages == 10
    assert pagination.has_prev == True
    assert pagination.has_next == True

    iter = pagination.iter_pages()
    result = [i for i in iter]
    assert result == [1,2,3,4,None,10]

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_template_formatting_from_string -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_template_formatting_from_string(app):
    """Test formatting of string-based template to string."""
    with app.app_context():
        out = render_template_to_string("foobar: {{ baz }}", _from_string=True,
                                        **{'baz': 'spam'})
        assert out == 'foobar: spam'

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_save_and_validate_logo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_save_and_validate_logo(app, db,instance_path,communities):
    loc = Location(name='local', uri=instance_path, default=True)
    db.session.add(loc)
    bucket = Bucket(
        id="00000000-0000-0000-0000-000000000000",
        default_location=1,
        default_storage_class="S",
        size=111,
    )
    db.session.add(bucket)
    db.session.commit()
    logo_filename = "weko-logo.png"
    logo = open(os.path.join(os.path.dirname(__file__),'data/weko-logo.png'),"rb")
    result = save_and_validate_logo(logo, logo_filename,"comm1")
    assert result == "png"
    obj = ObjectVersion.query.first()
    assert obj.key == "comm1/logo.png"

    # extentions not in png, jpg, jpeg, svg
    logo_filename = "weko-logo.txt"
    logo = open(os.path.join(os.path.dirname(__file__),'data/weko-logo.txt'),"rb")
    result = save_and_validate_logo(logo, logo_filename,"comm1")
    assert result == None

    app.config.update(
        COMMUNITIES_LOGO_MAX_SIZE=10
    )
    logo_filename = "weko-logo.png"
    logo = open(os.path.join(os.path.dirname(__file__),'data/weko-logo.png'),"rb")
    result = save_and_validate_logo(logo, logo_filename,"comm1")
    assert result == None


# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_initialize_communities_bucket -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_initialize_communities_bucket(app,db,instance_path):
    loc = Location(name='local', uri=instance_path, default=True)
    db.session.add(loc)

    bucket = Bucket(
        id="517f7d98-ab2c-4736-91ea-54ba34e7905d",
        default_location=1,
        default_storage_class="S",
        size=111,
    )
    db.session.add(bucket)
    db.session.commit()

    # not exist Bucket
    with patch("invenio_communities.utils.db.session.commit", side_effect=Exception('')):
        initialize_communities_bucket()
        assert Bucket.query.filter_by(id="00000000-0000-0000-0000-000000000000").first()==None

    initialize_communities_bucket()
    bucket = Bucket.query.filter_by(id="00000000-0000-0000-0000-000000000000").first()
    assert bucket.default_storage_class == "S"
    assert bucket.location == loc

    with pytest.raises(FilesException) as e:
        initialize_communities_bucket()

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_format_request_email_templ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_format_request_email_templ(app,db,db_records,communities):
    increq = InclusionRequest(id_community="comm1",id_record=db_records[2].id,id_user=1)
    db.session.add(increq)
    db.session.commit()

    test = "foobar: spam, link: https://inveniosoftware.org/communities/comm1/curate/, user: test_user"
    ctx = { "_from_string":True,'baz': 'spam','requester':'test_user'}
    result = format_request_email_templ(increq,"foobar: {{ baz }}, link: {{curate_link}}, user: {{requester}}",**ctx)

    assert result == test

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_send_community_request_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_send_community_request_email(app,db,db_records,communities,users,mocker):
    increq = InclusionRequest(id_community="comm1",id_record=db_records[2].id,id_user=1)
    db.session.add(increq)
    db.session.commit()

    test = {
        "recipients": ["test@test.org"],
        "subject": "A record was requested to be added to your community (Title1).",
        "sender": "info@inveniosoftware.org",
        "reply_to": None,
        "cc": [],
        "bcc": [],
        "body": "A new upload requests to be added to your community (Title1):\n\n\nRequested by:  (test@test.org)\n\nRecord Title: [&#39;test_title1&#39;]\nRecord Description: \n\nYou can accept or reject this record in your community curation page:\nhttps://inveniosoftware.org/communities/comm1/curate/",
        "html": None,
        "date": None,
        "msgId": "<167897618090.4148.5133223996038127488@63ee5d1d2822>",
        "charset": None,
        "extra_headers": None,
        "mail_options": [],
        "rcpt_options":[],
        "attachments": []
    }
    mock_send = mocker.patch("invenio_mail.tasks.send_email.delay")
    send_community_request_email(increq)
    args, kwargs = mock_send.call_args
    data = args[0]
    assert data["recipients"] == ["sysadmin@test.org"]
    assert data["subject"] == "A record was requested to be added to your community (Title1)."
    assert data["sender"] == "info@inveniosoftware.org"
    assert data["reply_to"] == None
    assert data["cc"] == []
    assert data["bcc"] == []
    assert data["body"] == "A new upload requests to be added to your community (Title1):\n\n\nRequested by:  (user@test.org)\n\nRecord Title: [&#39;test_title1&#39;]\nRecord Description: \n\nYou can accept or reject this record in your community curation page:\nhttps://inveniosoftware.org/communities/comm1/curate/"
    assert data["html"] == None
    assert data["date"] == None
    assert data["charset"] == None
    assert data["extra_headers"] == None
    assert data["mail_options"] == []
    assert data["rcpt_options"] ==[]
    assert data["attachments"] == []


# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_get_user_role_ids -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_get_user_role_ids(app,db, communities,users):
    # without login
    result = get_user_role_ids()
    assert result == []

    # with login
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        result = get_user_role_ids()
        assert result == [1]

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_email_formatting -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_email_formatting(app, db, communities, users):

    """Test formatting of the email message with the default template."""
    user = users[2]["obj"]
    app.config['COMMUNITIES_MAIL_ENABLED'] = True
    with app.extensions['mail'].record_messages() as outbox:
        (comm1, comm2, comm3) = communities
        rec1 = Record.create({
            'title': 'Foobar and Bazbar',
            'description': 'On Foobar, Bazbar and <b>more</b>.'
        })

        # Request
        InclusionRequest.create(community=comm1, record=rec1, user=user)

        # Check emails being sent
        assert len(outbox) == 1
        sent_msg = outbox[0]
        assert sent_msg.recipients == [user.email]
        assert comm1.title in sent_msg.body

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_delete_empty -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_delete_empty():
    data = {'metainfo': {'parentkey': [{'catalog_access_rights': [{'catalog_access_right_access_rights': 'embargoed access', 'catalog_access_right_rdf_resource': 'rdef3'}], 'catalog_contributors': [{'contributor_names': [{'contributor_name': '提供機関名', 'contributor_name_language': 'en'}], 'contributor_type': 'HostingInstitution'}], 'catalog_identifiers': [{'catalog_identifier': 'iden1', 'catalog_identifier_type': 'DOI'}], 'catalog_license': {'catalog_license_language': 'ja-Kana', 'catalog_license_rdf_resource': 'ed', 'catalog_license_type': 'file'}, 'catalog_licenses': [{'catalog_license': 'lic1'}], 'catalog_rights': [{'catalog_right': 'ac1', 'catalog_right_language': 'ja', 'catalog_right_rdf_resource': 'rdf'}], 'catalog_subjects': [{'catalog_subject': 'sub1', 'catalog_subject_language': 'ja', 'catalog_subject_scheme': 'BSH', 'catalog_subject_uri': 'suburl1'}]}]}}
    flg, result = delete_empty(data)
    assert (flg == True and result == {'metainfo': {'parentkey': [{"catalog_rights": [{"catalog_right": "ac1", "catalog_right_language": "ja", "catalog_right_rdf_resource": "rdf"}], "catalog_license": {"catalog_license_type": "file", "catalog_license_language": "ja-Kana", "catalog_license_rdf_resource": "ed"}, "catalog_licenses": [{"catalog_license": "lic1"}], "catalog_subjects": [{"catalog_subject": "sub1", "catalog_subject_uri": "suburl1", "catalog_subject_scheme": "BSH", "catalog_subject_language": "ja"}], "catalog_identifiers": [{"catalog_identifier": "iden1", "catalog_identifier_type": "DOI"}], "catalog_contributors": [{"contributor_type": "HostingInstitution", "contributor_names": [{"contributor_name": "提供機関名", "contributor_name_language": "en"}]}], "catalog_access_rights": [{"catalog_access_right_rdf_resource": "rdef3", "catalog_access_right_access_rights": "embargoed access"}]}]}})
    data = {'metainfo': {'parentkey': [{'catalog_contributors': [{'contributor_names': [{'contributor_name': '提供機関名', 'contributor_name_language': 'ja'}], 'contributor_type': 'HostingInstitution'}], 'catalog_identifiers': [{}], 'catalog_subjects': [{}], 'catalog_licenses': [{}], 'catalog_rights': [{}], 'catalog_access_rights': [{}]}]}}
    flg, result = delete_empty(data)
    assert (flg == True and result == {'metainfo': {'parentkey': [{"catalog_contributors": [{"contributor_type": "HostingInstitution", "contributor_names": [{"contributor_name": "提供機関名", "contributor_name_language": "ja"}]}]}]}})
    data=[]
    flg, result = delete_empty(data)
    assert (flg == False and result == None)
    data=None
    flg, result = delete_empty(data)
    assert (flg == False and result == None)

# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_delete_empty -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_delete_empty():
    data = {'metainfo': {'parentkey': [{'catalog_access_rights': [{'catalog_access_right_access_rights': 'embargoed access', 'catalog_access_right_rdf_resource': 'rdef3'}], 'catalog_contributors': [{'contributor_names': [{'contributor_name': '提供機関名', 'contributor_name_language': 'en'}], 'contributor_type': 'HostingInstitution'}], 'catalog_identifiers': [{'catalog_identifier': 'iden1', 'catalog_identifier_type': 'DOI'}], 'catalog_license': {'catalog_license_language': 'ja-Kana', 'catalog_license_rdf_resource': 'ed', 'catalog_license_type': 'file'}, 'catalog_licenses': [{'catalog_license': 'lic1'}], 'catalog_rights': [{'catalog_right': 'ac1', 'catalog_right_language': 'ja', 'catalog_right_rdf_resource': 'rdf'}], 'catalog_subjects': [{'catalog_subject': 'sub1', 'catalog_subject_language': 'ja', 'catalog_subject_scheme': 'BSH', 'catalog_subject_uri': 'suburl1'}]}]}}
    flg, result = delete_empty(data)
    assert (flg == True and result == {'metainfo': {'parentkey': [{"catalog_rights": [{"catalog_right": "ac1", "catalog_right_language": "ja", "catalog_right_rdf_resource": "rdf"}], "catalog_license": {"catalog_license_type": "file", "catalog_license_language": "ja-Kana", "catalog_license_rdf_resource": "ed"}, "catalog_licenses": [{"catalog_license": "lic1"}], "catalog_subjects": [{"catalog_subject": "sub1", "catalog_subject_uri": "suburl1", "catalog_subject_scheme": "BSH", "catalog_subject_language": "ja"}], "catalog_identifiers": [{"catalog_identifier": "iden1", "catalog_identifier_type": "DOI"}], "catalog_contributors": [{"contributor_type": "HostingInstitution", "contributor_names": [{"contributor_name": "提供機関名", "contributor_name_language": "en"}]}], "catalog_access_rights": [{"catalog_access_right_rdf_resource": "rdef3", "catalog_access_right_access_rights": "embargoed access"}]}]}})
    data = {'metainfo': {'parentkey': [{'catalog_contributors': [{'contributor_names': [{'contributor_name': '提供機関名', 'contributor_name_language': 'ja'}], 'contributor_type': 'HostingInstitution'}], 'catalog_identifiers': [{}], 'catalog_subjects': [{}], 'catalog_licenses': [{}], 'catalog_rights': [{}], 'catalog_access_rights': [{}]}]}}
    flg, result = delete_empty(data)
    assert (flg == True and result == {'metainfo': {'parentkey': [{"catalog_contributors": [{"contributor_type": "HostingInstitution", "contributor_names": [{"contributor_name": "提供機関名", "contributor_name_language": "ja"}]}]}]}})
    data=[]
    flg, result = delete_empty(data)
    assert (flg == False and result == None)
    data=None
    flg, result = delete_empty(data)
    assert (flg == False and result == None)


# .tox/c1/bin/pytest --cov=invenio_communities tests/test_utils.py::test_get_repository_id_by_item_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp
def test_get_repository_id_by_item_id(app, db, users, mocker):
    """Test get_repository_id_by_item_id."""
    index1 = Index(id=1, parent=0, position=0)
    index2 = Index(id=2, parent=1, position=0)
    index3 = Index(id=3, parent=0, position=1)
    db.session.add(index1)
    db.session.add(index2)
    db.session.add(index3)
    db.session.commit()
    comm1 = Community.create(community_id='comm1', role_id=1,
                            id_user=users[2]["obj"].id, title='Title1',
                            description='Description1',
                            root_node_id=index1.id,
                            group_id=1)
    db.session.commit()

    # Setup mock data
    record_data = {1: {"path": [1]}, 2: {"path": [2]}, 3: {"path": [3]},}

    index_data = {1: index1, 2: index2, 3: index3,}

    def mock_get_record(item_id):
        result = record_data.get(item_id, None)
        if result is None:
            raise NoResultFound
        return result

    def mock_get_index_by_id(index_id):
        return index_data.get(index_id, None)

    mocker.patch('invenio_records.api.Record.get_record', side_effect=mock_get_record)
    mocker.patch('weko_index_tree.models.Index.get_index_by_id', side_effect=mock_get_index_by_id)

    # repository_id can be retrieved
    repository_id = get_repository_id_by_item_id(1)
    assert repository_id == comm1.id

    #
    repository_id = get_repository_id_by_item_id(2)
    assert repository_id == comm1.id

    # repository_id cannot be retrieved
    repository_id = get_repository_id_by_item_id(3)
    assert repository_id == "Root Index"

    # item_id does not exist
    with pytest.raises(NoResultFound):
        repository_id = get_repository_id_by_item_id(999)
