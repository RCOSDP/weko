# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile
from datetime import datetime

import pytest
from flask import Blueprint, Flask
from flask_admin import Admin
from flask_celeryext import FlaskCeleryExt
from invenio_db import InvenioDB
from invenio_db import db as db_
from six import StringIO
from flask_babelex import Babel

from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from weko_admin.config import WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS
from weko_admin.models import AdminSettings
from weko_index_tree.models import Index
from invenio_communities.models import Community
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user

from invenio_mail import InvenioMail, config
from invenio_mail.admin import mail_adminview, mail_templates_adminview
from invenio_mail.models import MailConfig, MailTemplates, MailTemplateGenres, MailTemplateUsers, MailType


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)
    
@pytest.fixture()
def base_app(instance_path):
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SERVER_NAME='app',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #      'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                         'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        WEKO_RECORDS_UI_MAIL_TEMPLATE_SECRET_GENRE_ID=1,
        WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS = {
            "secret_URL_file_download": {
                "secret_expiration_date": 30,
                "secret_expiration_date_unlimited_chk": False,
                "secret_download_limit": 10,
                "secret_download_limit_unlimited_chk": False,
            },
            "content_file_download": {
                "expiration_date": 30,
                "expiration_date_unlimited_chk": False,
                "download_limit": 10,
                "download_limit_unlimited_chk": False,
            },
            "usage_report_workflow_access": {
                "expiration_date_access": 500,
                "expiration_date_access_unlimited_chk": False,
            },
            "terms_and_conditions": [],
            "error_msg": {
                "key" : "",
                "content" : {
                    "ja" : {
                        "content" : "このデータは利用できません（権限がないため）。"
                    },
                    "en":{
                        "content" : "This data is not available for this user"
                    }
                }
            }
        }
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioMail(app_)
    
    app_.jinja_loader.searchpath.append('tests/templates')
    admin = Admin(app_)
    view_class = mail_adminview['view_class']
    view_class_template = mail_templates_adminview['view_class']
    admin.add_view(view_class(**mail_adminview['kwargs']))
    admin.add_view(view_class_template(**mail_templates_adminview['kwargs']))
    
    
    return app_

@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client
        
@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user_count = User.query.filter_by(email='user@test.org').count()
    if user_count != 1:
        user = create_test_user(email='user@test.org')
        contributor = create_test_user(email='contributor@test.org')
        comadmin = create_test_user(email='comadmin@test.org')
        repoadmin = create_test_user(email='repoadmin@test.org')
        sysadmin = create_test_user(email='sysadmin@test.org')
        generaluser = create_test_user(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = create_test_user(email='student@test.org')
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = User.query.filter_by(email='student@test.org').first()
        
    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        repoadmin_role = ds.create_role(name='Repository Administrator')
        contributor_role = ds.create_role(name='Contributor')
        comadmin_role = ds.create_role(name='Community Administrator')
        general_role = ds.create_role(name='General')
        originalrole = ds.create_role(name='Original Role')
        studentrole = ds.create_role(name='Student')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
        contributor_role = Role.query.filter_by(name='Contributor').first()
        comadmin_role = Role.query.filter_by(name='Community Administrator').first()
        general_role = Role.query.filter_by(name='General').first()
        originalrole = Role.query.filter_by(name='Original Role').first()
        studentrole = Role.query.filter_by(name='Student').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)
    ds.add_role_to_user(student,studentrole)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action='superuser-access', role=sysadmin_role),
            ActionRoles(action='admin-access', role=repoadmin_role),
            ActionRoles(action='schema-access', role=repoadmin_role),
            ActionRoles(action='index-tree-access', role=repoadmin_role),
            ActionRoles(action='indextree-journal-access', role=repoadmin_role),
            ActionRoles(action='item-type-access', role=repoadmin_role),
            ActionRoles(action='item-access', role=repoadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=repoadmin_role),
            ActionRoles(action='files-rest-object-read', role=repoadmin_role),
            ActionRoles(action='search-access', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),
            ActionRoles(action='download-original-pdf-access', role=repoadmin_role),
            ActionRoles(action='author-access', role=repoadmin_role),
            ActionRoles(action='items-autofill', role=repoadmin_role),
            ActionRoles(action='stats-api-access', role=repoadmin_role),
            ActionRoles(action='read-style-action', role=repoadmin_role),
            ActionRoles(action='update-style-action', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),

            ActionRoles(action='admin-access', role=comadmin_role),
            ActionRoles(action='index-tree-access', role=comadmin_role),
            ActionRoles(action='indextree-journal-access', role=comadmin_role),
            ActionRoles(action='item-access', role=comadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=comadmin_role),
            ActionRoles(action='files-rest-object-read', role=comadmin_role),
            ActionRoles(action='search-access', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='download-original-pdf-access', role=comadmin_role),
            ActionRoles(action='author-access', role=comadmin_role),
            ActionRoles(action='items-autofill', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),

            ActionRoles(action='item-access', role=contributor_role),
            ActionRoles(action='files-rest-bucket-update', role=contributor_role),
            ActionRoles(action='files-rest-object-delete', role=contributor_role),
            ActionRoles(action='files-rest-object-delete-version', role=contributor_role),
            ActionRoles(action='files-rest-object-read', role=contributor_role),
            ActionRoles(action='search-access', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='download-original-pdf-access', role=contributor_role),
            ActionRoles(action='author-access', role=contributor_role),
            ActionRoles(action='items-autofill', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
        ]
        db.session.add_all(action_roles)
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
    db.session.commit()

    return [
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': generaluser},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
        {'email': student.email,'id': student.id, 'obj': student}
    ]


@pytest.fixture()
def mail_configs(db):
    config = MailConfig(
        id=1,
        mail_server="localhost",
        mail_port=25,
        
    )
    db.session.add(config)
    db.session.commit()
    return config

@pytest.fixture()
def mail_templates(db):
    """Create mail templates."""
    from invenio_mail.models import MailTemplates
    from invenio_mail.models import MailTemplateGenres
    genres = []
    genre1 = MailTemplateGenres(
        id=1,
        name="Notification of secret URL provision"
    )
    genres.append(genre1)
    genre2 = MailTemplateGenres(
        id=2,
        name="Guidance to the application form"
    )
    genres.append(genre2)
    genre3 = MailTemplateGenres(
        id=3,
        name="Others"
    )
    genres.append(genre3)
    db.session.add_all(genres)
    db.session.commit()
    template = MailTemplates(
        id=1,
        mail_subject="test subject",
        mail_body="test body",
        default_mail=True,
        mail_genre_id=genre1.id,
    )
    db.session.add(template)
    db.session.commit()
    return template

@pytest.yield_fixture()
def email_admin_app():
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    base_app = Flask(__name__, instance_path=instance_path)
    base_app.config.update(
        SECRET_KEY='SECRET KEY',
        SESSION_TYPE='memcached',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite://'),
    )
    InvenioDB(base_app)
    InvenioMail(base_app)
    base_app.jinja_loader.searchpath.append('tests/templates')
    admin = Admin(base_app)
    view_class = mail_adminview['view_class']
    admin.add_view(view_class(**mail_adminview['kwargs']))
    with base_app.app_context():
        if str(db.engine.url) != "sqlite://" and \
                not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.metadata.create_all(db.engine, tables=[MailConfig.__table__])

    yield base_app

    with base_app.app_context():
        drop_database(str(db.engine.url))
    shutil.rmtree(instance_path)


@pytest.fixture(scope='session')
def email_task_app(request):
    """Flask application fixture."""
    app = Flask('testapp')
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        CELERY_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND='cache',
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        MAIL_SUPPRESS_SEND=True
    )
    FlaskCeleryExt(app)
    InvenioMail(app, StringIO())

    return app


@pytest.fixture(scope='session')
def email_api_app(email_task_app):
    """Flask application fixture."""
    email_task_app.register_blueprint(
        Blueprint('invenio_mail_test', __name__, template_folder='templates')
    )

    return email_task_app


@pytest.fixture
def email_params():
    """Email parameters fixture."""
    return {
        'subject': 'subject',
        'recipients': ['recipient@inveniosoftware.com'],
        'sender': 'sender@inveniosoftware.com',
        'cc': 'cc@inveniosoftware.com',
        'bcc': 'bcc@inveniosoftware.com',
        'reply_to': 'reply_to@inveniosoftware.com',
        'date': datetime.now(),
        'attachments': [],
        'charset': None,
        'extra_headers': None,
        'mail_options': [],
        'rcpt_options': [],
    }


@pytest.fixture
def email_ctx():
    """Email context fixture."""
    return {
        'user': 'User',
        'content': 'This a content.',
        'sender': 'sender',
    }

@pytest.fixture
def admin_settings(db):
    restricted_access = AdminSettings(
        name='restricted_access',
        settings=WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS
    )
    db.session.add(restricted_access)
    db.session.commit()


@pytest.fixture
def mail_template_fixture(db):
    genre1 = MailTemplateGenres(id=1, name='Test Genre1')
    genre2 = MailTemplateGenres(id=2, name='Test Genre2')
    genre3 = MailTemplateGenres(id=3, name='Test Genre3')
    db.session.add(genre1)
    db.session.add(genre2)
    db.session.add(genre3)

    mail_template = MailTemplates(
        id = 1,
        mail_subject = 'Test Subject',
        mail_body = 'Test Body',
        default_mail = True,
        mail_genre_id = 1
    )
    db.session.add(mail_template)
    return mail_template


@pytest.fixture
def mail_template_users_fixture(db, mail_template_fixture):
    user1 = User(id=1, email='user1@example.com')
    user2 = User(id=2, email='user2@example.com')

    mail_template = mail_template_fixture

    mail_template_user1_recipient = MailTemplateUsers(
        template=mail_template,
        user=user1,
        mail_type=MailType.RECIPIENT
    )
    mail_template_user1_cc = MailTemplateUsers(
        template=mail_template,
        user=user1,
        mail_type=MailType.CC
    )
    mail_template_user1_bcc = MailTemplateUsers(
        template=mail_template,
        user=user1,
        mail_type=MailType.BCC
    )
    mail_template_user2_recipient = MailTemplateUsers(
        template=mail_template,
        user=user2,
        mail_type=MailType.RECIPIENT
    )
    mail_template_user2_cc = MailTemplateUsers(
        template=mail_template,
        user=user2,
        mail_type=MailType.CC
    )
    mail_template_user2_bcc = MailTemplateUsers(
        template=mail_template,
        user=user2,
        mail_type=MailType.BCC
    )
    db.session.add(mail_template_user1_recipient)
    db.session.add(mail_template_user1_cc)
    db.session.add(mail_template_user1_bcc)
    db.session.add(mail_template_user2_recipient)
    db.session.add(mail_template_user2_cc)
    db.session.add(mail_template_user2_bcc)
    db.session.commit()

    users = [user1, user2]
    mail_template_users = [
        mail_template_user1_recipient,
        mail_template_user1_cc,
        mail_template_user1_bcc,
        mail_template_user2_recipient,
        mail_template_user2_cc,
        mail_template_user2_bcc
    ]

    return mail_template, users, mail_template_users
