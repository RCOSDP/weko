# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Utility functions tests."""

from __future__ import absolute_import, print_function

import pytest
import os
from mock import patch
from PIL import Image, ImageFilter
from invenio_records.api import Record
from invenio_files_rest.models import Location, Bucket, ObjectVersion

from invenio_files_rest.errors import FilesException

from invenio_communities.models import InclusionRequest
from invenio_communities.utils import render_template_to_string,Pagination,save_and_validate_logo,\
    initialize_communities_bucket,format_request_email_templ,send_community_request_email,get_user_role_ids

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
