# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import hashlib
import os
import pytest
import shutil
import tempfile
from flask import Flask, json, url_for
from flask_babelex import Babel
from flask_celeryext import FlaskCeleryExt
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers, Role
from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_db.utils import drop_alembic_version_table
from six import BytesIO
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DropConstraint, DropSequence, DropTable
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_previewer import InvenioPreviewer
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, MultipartObject, \
    ObjectVersion, Part
from invenio_files_rest.permissions import bucket_listmultiparts_all, \
    bucket_read_all, bucket_read_versions_all, bucket_update_all, \
    location_update_all, multipart_delete_all, multipart_read_all, \
    object_delete_all, object_delete_version_all, object_read_all, \
    object_read_version_all
from invenio_files_rest.storage import PyFSFileStorage
from invenio_files_rest.views import blueprint


@compiles(DropTable, 'postgresql')
def _compile_drop_table(element, compiler, **kwargs):
    return compiler.visit_drop_table(element) + ' CASCADE'


@compiles(DropConstraint, 'postgresql')
def _compile_drop_constraint(element, compiler, **kwargs):
    return compiler.visit_drop_constraint(element) + ' CASCADE'


@compiles(DropSequence, 'postgresql')
def _compile_drop_sequence(element, compiler, **kwargs):
    return compiler.visit_drop_sequence(element) + ' CASCADE'


@pytest.fixture()
def base_app():
    """Flask application fixture."""
    app_ = Flask('testapp')
    app_.config.update(
        TESTING=True,
        # Celery 3
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        # Celery 4
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI',
        #     'sqlite:///:memory:'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),       
        WTF_CSRF_ENABLED=False,
        SERVER_NAME='invenio.org',
        SECURITY_PASSWORD_SALT='TEST_SECURITY_PASSWORD_SALT',
        SECRET_KEY='TEST_SECRET_KEY',
        FILES_REST_MULTIPART_CHUNKSIZE_MIN=2,
        FILES_REST_MULTIPART_CHUNKSIZE_MAX=20,
        FILES_REST_MULTIPART_MAX_PARTS=100,
        FILES_REST_TASK_WAIT_INTERVAL=0.1,
        FILES_REST_TASK_WAIT_MAX_SECONDS=1,
    )

    FlaskCeleryExt(app_)
    InvenioDB(app_)
    Babel(app_)
    Menu(app_)
    InvenioPreviewer(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    InvenioAccounts(base_app)
    InvenioAccess(base_app)
    base_app.register_blueprint(accounts_blueprint)
    InvenioFilesREST(base_app)
    base_app.register_blueprint(blueprint)

    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def db(app):
    """Get setup database."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
    drop_alembic_version_table()


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def dummy_location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(
        name='testloc',
        uri=tmppath,
        default=True
    )
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)

@pytest.yield_fixture()
def dummy_s3_location(db):
    tmppath = tempfile.mkdtemp()
    loc = Location(
        name="s3",
        uri=tmppath,
        access_key="test_access_key",
        secret_key="test_secret_key",
        s3_endpoint_url="http://test.s3.com",
        s3_send_file_directly=True
    )
    db.session.add(loc)
    db.session.commit()
    yield loc
    
    shutil.rmtree(tmppath)


@pytest.fixture()
def pyfs_testpath(dummy_location):
    """Temporary path for PyFS."""
    return os.path.join(dummy_location.uri, 'subpath/data')


@pytest.fixture()
def pyfs(dummy_location, pyfs_testpath):
    """Instance of PyFSFileStorage."""
    return PyFSFileStorage(pyfs_testpath)


@pytest.yield_fixture()
def extra_location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(
        name='extra',
        uri=tmppath,
        default=False
    )
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def bucket(db, dummy_location):
    """File system location."""
    b1 = Bucket.create()
    db.session.commit()
    return b1


@pytest.fixture()
def multipart(db, bucket):
    """Multipart object."""
    mp = MultipartObject.create(bucket, 'mykey', 110, 20)
    db.session.commit()
    return mp


@pytest.fixture()
def multipart_url(multipart):
    """File system location."""
    return url_for(
        'invenio_files_rest.object_api',
        bucket_id=str(multipart.bucket_id),
        key=multipart.key,
        uploadId=multipart.upload_id
    )


@pytest.fixture()
def parts(db, multipart):
    """All parts for a multipart object."""
    items = []
    for i in range(multipart.last_part_number + 1):
        chunk_size = multipart.chunk_size \
            if not i == multipart.last_part_number \
            else multipart.last_part_size
        p = Part.create(
            multipart,
            i,
            stream=BytesIO(u'{0}'.format(i).encode('ascii') * chunk_size)
        )
        items.append(p)

    db.session.commit()
    return items


@pytest.yield_fixture()
def objects(db, bucket):
    """File system location."""
    # Create older versions first
    for key, content in [
            ('LICENSE', b'old license'),
            ('README.rst', b'old readme')]:
        ObjectVersion.create(
            bucket, key, stream=BytesIO(content), size=len(content)
        )

    # Create new versions
    objs = []
    for key, content in [
            ('LICENSE', b'license file'),
            ('README.rst', b'readme file')]:
        objs.append(
            ObjectVersion.create(
                bucket, key, stream=BytesIO(content), size=len(content)
            )
        )
    db.session.commit()

    yield objs


@pytest.yield_fixture()
def versions(objects):
    """Get objects with all their versions."""
    versions = []
    for obj in objects:
        versions.extend(ObjectVersion.get_versions(obj.bucket, obj.key))

    yield versions


@pytest.fixture()
def users_data(db):
    """User data fixture."""
    return [
        dict(email='user1@inveniosoftware.org', password='pass1'),
        dict(email='user2@inveniosoftware.org', password='pass1'),
    ]


@pytest.fixture()
def users(db, users_data):
    """Create test users."""
    return [
        create_test_user(active=True, **users_data[0]),
        create_test_user(active=True, **users_data[1]),
    ]


@pytest.fixture()
def headers():
    """Get standard Invenio REST API headers."""
    return {
        'Content-Type': 'application/json',
        'Accept': '*/*',
    }


@pytest.yield_fixture()
def permissions(db, bucket):
    """Permission for users."""
    users = {
        None: None,
    }

    for user in [
            'auth', 'location', 'bucket',
            'objects', 'objects-read-version']:
        users[user] = create_test_user(
            email='{0}@invenio-software.org'.format(user),
            password='pass1',
            active=True
        )

    location_perms = [
        location_update_all,
        bucket_read_all,
        bucket_read_versions_all,
        bucket_update_all,
        bucket_listmultiparts_all,
        object_read_all,
        object_read_version_all,
        object_delete_all,
        object_delete_version_all,
        multipart_read_all,
        multipart_delete_all,
    ]

    bucket_perms = [
        bucket_read_all,
        object_read_all,
        bucket_update_all,
        object_delete_all,
        multipart_read_all,
    ]

    objects_perms = [
        object_read_all,
    ]

    for perm in location_perms:
        db.session.add(ActionUsers(
            action=perm.value,
            user=users['location']))
    for perm in bucket_perms:
        db.session.add(ActionUsers(
            action=perm.value,
            argument=str(bucket.id),
            user=users['bucket']))
    for perm in objects_perms:
        db.session.add(ActionUsers(
            action=perm.value,
            argument=str(bucket.id),
            user=users['objects']))
    db.session.commit()

    yield users


@pytest.yield_fixture()
def admin_user(db):
    """Permission for admin users."""
    perms = [
        location_update_all,
        bucket_read_all,
        bucket_read_versions_all,
        bucket_update_all,
        bucket_listmultiparts_all,
        object_read_all,
        object_read_version_all,
        object_delete_all,
        object_delete_version_all,
        multipart_read_all,
        multipart_delete_all,
        bucket_read_all,
        object_read_all,
        bucket_update_all,
        object_delete_all,
        multipart_read_all,
        object_read_all,
    ]

    admin = Role(name='admin')

    for perm in perms:
        db.session.add(ActionRoles.allow(perm, role=admin))

    admin_user = create_test_user(email='admin@invenio-software.org',
                                  password='pass1',
                                  active=True)
    admin.users.append(admin_user)

    db.session.commit()

    yield admin_user


@pytest.fixture()
def get_md5():
    """Get MD5 of data."""
    def inner(data, prefix=True):
        m = hashlib.md5()
        m.update(data)
        return "md5:{0}".format(m.hexdigest()) if prefix else m.hexdigest()
    return inner


@pytest.fixture()
def get_sha256():
    """Get sha256 of data."""
    def inner(data, prefix=True):
        m = hashlib.sha256()
        m.update(data)
        return "sha256:{0}".format(m.hexdigest()) if prefix else m.hexdigest()
    return inner


@pytest.fixture()
def get_json():
    """Get JSON from response."""
    def inner(resp, code=None):
        if code is not None:
            assert resp.status_code == code
        return json.loads(resp.get_data(as_text=True))
    return inner
