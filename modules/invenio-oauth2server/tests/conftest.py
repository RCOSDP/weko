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

import pytest
from flask import Flask, url_for
from flask.views import MethodView
from flask_babelex import Babel
from flask_breadcrumbs import Breadcrumbs
from flask_mail import Mail
from flask_menu import Menu
from .helpers import create_oauth_client, patch_request
from invenio_accounts import InvenioAccountsREST, InvenioAccountsUI
from invenio_accounts.models import User
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import InvenioDB, db
from mock import MagicMock
from six import get_method_self
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from werkzeug.wsgi import DispatcherMiddleware

from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.decorators import require_api_auth, \
    require_oauth_scopes
from invenio_oauth2server.models import Client, Scope, Token
from invenio_oauth2server.views import server_blueprint, settings_blueprint


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()

    def init_app(app):
        app.config.update(
            LOGIN_DISABLED=False,
            MAIL_SUPPRESS_SEND=True,
            OAUTH2_CACHE_TYPE='simple',
            OAUTHLIB_INSECURE_TRANSPORT=True,
            SECRET_KEY='CHANGE_ME',
            SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
            SECURITY_PASSWORD_HASH='plaintext',
            SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
            SECURITY_PASSWORD_SCHEMES=['plaintext'],
            # SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
            #                                   'sqlite:///test.db'),
            SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
            SQLALCHEMY_TRACK_MODIFICATIONS=True,
            TESTING=True,
            WTF_CSRF_ENABLED=False,
        )
        Babel(app)
        Mail(app)
        Menu(app)
        Breadcrumbs(app)
        InvenioDB(app)
        InvenioOAuth2Server(app)

    api_app = Flask('testapiapp', instance_path=instance_path)
    api_app.config.update(
        APPLICATION_ROOT='/api',
        ACCOUNTS_REGISTER_BLUEPRINT=True
    )
    init_app(api_app)
    InvenioAccountsREST(api_app)
    InvenioOAuth2ServerREST(api_app)

    app = Flask('testapp', instance_path=instance_path)
    init_app(app)
    InvenioAccountsUI(app)
    app.register_blueprint(accounts_blueprint)
    app.register_blueprint(server_blueprint)
    app.register_blueprint(settings_blueprint)

    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/api': api_app.wsgi_app
    })

    with app.app_context():
        if str(db.engine.url) != 'sqlite://' and \
           not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            if str(db.engine.url) != 'sqlite://':
                drop_database(str(db.engine.url))
            shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.fixture()
def api_app(app):
    """Retrieve the REST API application."""
    return get_method_self(app.wsgi_app.mounts['/api'])


@pytest.fixture()
def api_app_with_test_view(api_app):
    api_app.add_url_rule('/test', 'test', view_func=lambda: 'OK')
    return api_app


@pytest.fixture
def settings_fixture(app):
    """Fixture for testing settings views."""
    from invenio_oauth2server.proxies import current_oauth2server
    with app.app_context():
        with db.session.begin_nested():
            datastore = app.extensions['security'].datastore
            datastore.create_user(email='info@inveniosoftware.org',
                                  password='tester')
        db.session.commit()
        current_oauth2server.register_scope(Scope('test:scope'))
        current_oauth2server.register_scope(Scope('test:scope2'))
    return app


@pytest.fixture
def developer_app_fixture(settings_fixture):
    """Fixture for testing developer application use cases."""
    settings_app = settings_fixture
    with settings_app.app_context():
        with db.session.begin_nested():
            datastore = settings_app.extensions['security'].datastore
            dev_user = datastore.create_user(
                email='dev@inveniosoftware.org', password='dev', active=True
            )

            dev_client = Client(client_id='dev',
                                client_secret='dev',
                                name='Test name',
                                description='Test description',
                                is_confidential=False,
                                user=dev_user,
                                website='http://inveniosoftware.org',
                                _redirect_uris='',
                                _default_scopes='test:scope')

            user = datastore.get_user('info@inveniosoftware.org')
            user_token = Token(client=dev_client,
                               user=user,
                               token_type='bearer',
                               access_token='dev_access_1',
                               refresh_token='dev_refresh_1',
                               expires=None,
                               is_personal=False,
                               is_internal=False,
                               _scopes='test:scope')

            db.session.add(dev_client)
            db.session.add(user_token)
        db.session.commit()
    return settings_app


@pytest.fixture
def models_fixture(app):
    """Fixture that contains the test data for models tests."""
    from invenio_oauth2server.proxies import current_oauth2server
    with app.app_context():
        # Register a test scope
        current_oauth2server.register_scope(Scope('test:scope1'))
        current_oauth2server.register_scope(Scope('test:scope2',
                                                  internal=True))
        datastore = app.extensions['security'].datastore
        with db.session.begin_nested():
            test_user = datastore.create_user(
                email='info@inveniosoftware.org', password='tester',
            )
            resource_owner = datastore.create_user(
                email='resource_owner@inveniosoftware.org', password='test'
            )
            consumer = datastore.create_user(
                email='consumer@inveniosoftware.org', password='test'
            )

            # create resource_owner -> client_1
            u1c1 = Client(client_id='client_test_u1c1',
                          client_secret='client_test_u1c1',
                          name='client_test_u1c1',
                          description='',
                          is_confidential=False,
                          user=resource_owner,
                          _redirect_uris='',
                          _default_scopes=""
                          )
            # create resource_owner -> client_1 / resource_owner -> token_1

            u1c1u1t1 = Token(client=u1c1,
                             user=resource_owner,
                             token_type='u',
                             access_token='dev_access_1',
                             refresh_token='dev_refresh_1',
                             expires=None,
                             is_personal=False,
                             is_internal=False,
                             _scopes='',
                             )

            # create consumer -> client_1 / resource_owner -> token_2

            u1c1u2t2 = Token(client=u1c1,
                             user=consumer,
                             token_type='u',
                             access_token='dev_access_2',
                             refresh_token='dev_refresh_2',
                             expires=None,
                             is_personal=False,
                             is_internal=False,
                             _scopes='',
                             )
            db.session.add(u1c1)
            db.session.add(u1c1u1t1)
            db.session.add(u1c1u2t2)
        db.session.commit()
        test_user_id = test_user.get_id()
        app.test_user = lambda: User.query.get(test_user_id)
        app.resource_owner_id = resource_owner.get_id()
        app.consumer_id = consumer.get_id()
        app.u1c1_id = u1c1.client_id
        app.u1c1u1t1_id = u1c1u1t1.id
        app.u1c1u2t2_id = u1c1u2t2.id
    return app


@pytest.fixture
def provider_fixture(app):
    """Fixture that contains test data for provider tests."""
    from invenio_oauth2server.proxies import current_oauth2server

    # Mock the oauth client calls to prevent them from going online.
    oauth_client = create_oauth_client(app, 'oauth2test')
    oauth_client.http_request = MagicMock(
        side_effect=patch_request(app)
    )
    datastore = app.extensions['security'].datastore
    with app.test_request_context():
        with db.session.begin_nested():
            current_oauth2server.register_scope(Scope('test:scope'))

            user1 = datastore.create_user(
                email='info@inveniosoftware.org', password='tester',
                active=True,
            )
            datastore.create_user(
                email='abuse@inveniosoftware.org', password='tester2',
                active=True
            )
            user3 = datastore.create_user(
                email='inactive@inveniosoftware.org', password='tester3',
                active=False
            )

            c1 = Client(client_id='dev',
                        client_secret='dev',
                        name='dev',
                        description='',
                        is_confidential=False,
                        user=user1,
                        _redirect_uris=url_for(
                            'oauth2test.authorized', _external=True
                        ),
                        _default_scopes='test:scope'
                        )
            c2 = Client(client_id='confidential',
                        client_secret='confidential',
                        name='confidential',
                        description='',
                        is_confidential=True,
                        user=user1,
                        _redirect_uris=url_for(
                            'oauth2test.authorized', _external=True
                        ),
                        _default_scopes='test:scope'
                        )
            # Same as 'c2' but user belonging to a user that's inactive
            c3 = Client(client_id='confidential-user-inactive',
                        client_secret='confidential-user-inactive',
                        name='confidential-user-inactive',
                        description='',
                        is_confidential=True,
                        user=user3,
                        _redirect_uris=url_for(
                            'oauth2test.authorized', _external=True
                        ),
                        _default_scopes='test:scope'
                        )
            c4 = Client(client_id='confidential-email',
                        client_secret='confidential-email',
                        name='confidential-email',
                        description='',
                        is_confidential=True,
                        user=user1,
                        _redirect_uris=url_for(
                            'oauth2test.authorized', _external=True
                        ),
                        _default_scopes='email')
            c5 = Client(client_id='no-scopes',
                        client_secret='no-scopes',
                        name='no-scopes',
                        description='',
                        is_confidential=False,
                        user=user1,
                        _redirect_uris=url_for(
                            'oauth2test.authorized', _external=True
                        ))
            db.session.add(c1)
            db.session.add(c2)
            db.session.add(c3)
            db.session.add(c4)
            db.session.add(c5)
        personal_token = Token.create_personal('test-personal',
                                               user1.id,
                                               scopes=[],
                                               is_internal=True)

        personal_token3 = Token.create_personal('test-personal',
                                                user3.id,
                                                scopes=[],
                                                is_internal=True)
        db.session.commit()

        app.user1_id = user1.id
        app.user3_id = user3.id
        app.personal_token = personal_token.access_token
        app.personal_token3 = personal_token3.access_token
    return app


@pytest.fixture
def expiration_fixture(provider_fixture):
    """Fixture for testing expiration."""
    provider_fixture.config.update(
        OAUTH2_PROVIDER_TOKEN_EXPIRES_IN=1,
    )
    return provider_fixture


@pytest.fixture
def resource_fixture(app, api_app):
    """Fixture that contains the test data for models tests."""
    from flask import g, request

    from invenio_oauth2server.proxies import current_oauth2server

    # Setup API resources
    class Test0Resource(MethodView):

        def get(self):
            app.identity = g.identity
            return "success", 200

    class Test1Resource(MethodView):
        # NOTE: Method decorators are applied in reverse order
        decorators = [
            require_oauth_scopes('test:testscope'),
            require_api_auth(),
        ]

        def get(self):
            assert request.oauth.access_token
            app.identity = g.identity
            return "success", 200

        def post(self):
            assert request.oauth.access_token
            return "success", 200

    class Test2Resource(MethodView):

        @require_api_auth()
        @require_oauth_scopes('test:testscope')
        def get(self):
            assert request.oauth.access_token
            return "success", 200

        @require_api_auth()
        @require_oauth_scopes('test:testscope')
        def post(self):
            assert request.oauth.access_token
            return "success", 200

    class Test3Resource(MethodView):

        @require_api_auth()
        def post(self):
            return "success", 200

    class Test4Resource(MethodView):

        @require_api_auth(allow_anonymous=True)
        def get(self):
            from flask_login import current_user
            return str(current_user.get_id()), 200

        def post(self):
            from flask_login import current_user
            return str(current_user.get_id()), 200

    # Register API resources
    api_app.add_url_rule(
        '/test0/identitytestcase/',
        view_func=Test0Resource.as_view('test0resource'),
    )
    api_app.add_url_rule(
        '/test1/decoratorstestcase/',
        view_func=Test1Resource.as_view('test1resource'),
    )
    api_app.add_url_rule(
        '/test2/decoratorstestcase/',
        view_func=Test2Resource.as_view('test2resource'),
    )
    # This one is a UI resource using login_required
    api_app.add_url_rule(
        '/test3/loginrequiredstestcase/',
        view_func=Test3Resource.as_view('test3resource'),
    )
    api_app.add_url_rule(
        '/test4/allowanonymous/',
        view_func=Test4Resource.as_view('test4resource'),
    )

    datastore = app.extensions['security'].datastore
    with app.app_context():
        # Register a test scope
        current_oauth2server.register_scope(Scope(
            'test:testscope',
            group='Test',
            help_text='Test scope'
        ))
        with db.session.begin_nested():
            app.user = datastore.create_user(
                email='info@inveniosoftware.org', password='tester',
                active=True,
            )

        # Create tokens
        app.user_id = app.user.id
        app.token = Token.create_personal(
            'test-', app.user.id, scopes=['test:testscope'], is_internal=True
        ).access_token
        app.token_noscope = Token.create_personal(
            'test-', app.user.id, scopes=[], is_internal=True).access_token
        db.session.commit()

    with api_app.test_request_context():
        app.url_for_test3resource = url_for('test3resource')

    with api_app.test_request_context():
        app.url_for_test0resource = url_for('test0resource')
        app.url_for_test1resource = url_for('test1resource')
        app.url_for_test2resource = url_for('test2resource')
        app.url_for_test4resource = url_for('test4resource')
        app.url_for_test0resource_token = url_for(
            'test0resource', access_token=app.token
        )
        app.url_for_test1resource_token = url_for(
            'test1resource', access_token=app.token
        )
        app.url_for_test2resource_token = url_for(
            'test2resource', access_token=app.token
        )
        app.url_for_test1resource_token_noscope = url_for(
            'test1resource', access_token=app.token_noscope
        )
        app.url_for_test2resource_token_noscope = url_for(
            'test2resource', access_token=app.token_noscope
        )
        app.url_for_test4resource_token = url_for(
            'test4resource', access_token=app.token
        )

    return app
