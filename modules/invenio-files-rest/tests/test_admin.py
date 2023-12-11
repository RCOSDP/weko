# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin tests."""

from __future__ import absolute_import, print_function
from unittest.mock import MagicMock, Mock, PropertyMock, patch
import uuid
from flask_security import login_user

import pytest
from invenio_admin import InvenioAdmin
from wtforms.validators import ValidationError
from flask import url_for

from invenio_files_rest.admin import MultipartObjectModelView, UnboundFilter, link_ver2, require_slug
from invenio_files_rest.models import Bucket, FileInstance, MultipartObject, ObjectVersion


def test_require_slug():
    """Test admin views."""
    class TestField(object):
        def __init__(self, data):
            self.data = data

    assert require_slug(None, TestField('aslug')) is None
    pytest.raises(ValidationError, require_slug, None, TestField('Not A Slug'))


def test_admin_views(app, db, dummy_location):
    """Test admin views."""
    app.config['SECRET_KEY'] = 'CHANGEME'
    InvenioAdmin(app, permission_factory=None, view_class_factory=lambda x: x)

    b1 = Bucket.create(location=dummy_location)
    obj = ObjectVersion.create(b1, 'test').set_location('placeuri', 1, 'chk')
    db.session.commit()

    with app.test_client() as client:
        res = client.get('/admin/bucket/')
        assert res.status_code == 200
        assert str(b1.id) in res.get_data(as_text=True)

        res = client.get('/admin/fileinstance/')
        assert res.status_code == 200
        assert str(obj.file_id) in res.get_data(as_text=True)

        res = client.get('/admin/location/')
        assert res.status_code == 200
        assert str(b1.location.name) in res.get_data(as_text=True)

        res = client.get('/admin/objectversion/')
        assert res.status_code == 200
        assert str(obj.version_id) in res.get_data(as_text=True)

def test_link_ver2(app, client, db, dummy_location, admin_user):
    with app.test_request_context():
        l = link_ver2('File','File'
                ,Mock(return_value = "link")
                ,Mock(return_value = "link")
                ,lambda o: o == "sample")
        
        with patch("invenio_files_rest.admin.current_user") as c:
            type(c).roles = ["System Administrator"]
            assert l(None, None, "sample", None) == '<a href="link">File</a>'
            
            type(c).roles = []
            assert l(None, None, "sample", None) == "File"
            
            assert l(None, None, "dummy", None) == "File"
            
def test_UnboundFilter___init__():
    assert type(UnboundFilter(column='bucket_id',name='Item Bucket')) == UnboundFilter
    
def test_UnboundFilter_apply():
    q = MagicMock()
    q.filter = MagicMock(return_value = True)
    
    u = UnboundFilter(column='bucket_id',name='Item Bucket')
    
    assert u.apply(q, None) == True
    
def test_UnboundFilter_operation():
    u = UnboundFilter(column='bucket_id',name='Item Bucket')
    assert u.operation() == "is Unbind"
    
def test_MultipartObjectModelView_delete_model(app, db, users, bucket, dummy_location, redis_connect):
    with db.session.begin_nested():
        fileinstance = FileInstance.create()
        file_id = str(fileinstance.id)
        fileinstance.uri = dummy_location.uri + "/" + file_id[0:2] + "/" + file_id[2:4] + "/" + file_id[4:] + "/data"
        fileinstance.storage_class = app.config['FILES_REST_DEFAULT_STORAGE_CLASS']
        fileinstance.size = 1024
        fileinstance.readable = False
        fileinstance.writable = True
        db.session.add(fileinstance)

    db.session.commit()
    
    upload_id = str(uuid.uuid4())
    
    with db.session.begin_nested():
        multipartObject = MultipartObject()
        multipartObject.upload_id = upload_id
        multipartObject.file_id = file_id
        multipartObject.key = "sample"
        multipartObject.size = 1024
        multipartObject.chunk_size = 512
        multipartObject.completed = True
        multipartObject.created_by_id = 1
        multipartObject.bucket_id = bucket.id
        db.session.add(multipartObject)
        
    db.session.commit()
    
    redis_connect.put(
                "upload_id" + upload_id,
                b"lock"
                )
    with patch("invenio_files_rest.admin.RedisConnection.connection", return_value = redis_connect):
        with patch("invenio_files_rest.admin.flash", side_effect = lambda s1, s2: s1):
            # error "Cannot be deleted because it is being uploaded."
            assert MultipartObjectModelView.delete_model(MagicMock(), multipartObject) == "Cannot be deleted because it is being uploaded."
        
            redis_connect.delete("upload_id" + upload_id)
            
            # error "Record that bound item must not be deleted."
            assert MultipartObjectModelView.delete_model(MagicMock(), multipartObject) == "Record that bound item must not be deleted."
            
            with db.session.begin_nested():
                multipartObject.bucket_id = None
                db.session.add(multipartObject)
                
            db.session.commit()
            
            # normal
            assert MultipartObjectModelView.delete_model(MagicMock(), multipartObject) == True
    