# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Minimal OAuth2 consumer implementation to demonstrate OAuth2 protocol

SPHINX-START

This example OAuth2 consumer application is used to fetch an OAuth2 access
token from example application.

| For more information about OAuth2 protocol see
| https://invenio-oauthclient.readthedocs.io/en/latest/overview.html

.. note:: Before continuing make sure example application is running.

|

Open settings page of example app to register a new OAuth2 application:

.. code-block:: console

   $ open http://127.0.0.1:5000/account/settings/applications

Login using:

    | **username:** admin\@inveniosoftware.org
    | **password:** 123456

Click on "New application" and compile registration form with following data:
    | **Name:**           foobar-app
    | **Description:**    An example OAuth2 consumer application
    | **Website URL:**    \http://127.0.0.1:5100/
    | **Redirect URIs:**  \http://127.0.0.1:5100/authorized
    | **Client Type:**    Confidential


Click register and example application will generate and show you
a Client ID and Client Secret.

Open another terminal and move to examples-folder.

Export these values using following environment variables before starting
the example consumer or change values of corresponding keys
in *examples/consumer.py* to match.

.. code-block:: console

    $ export CONSUMER_CLIENT_ID=<generated_client_id>
    $ export CONSUMER_CLIENT_SECRET=<generated_client_secret>

|

**LOGOUT admin\@inveniosoftware.org from example application:**

.. code-block:: console

    $ open http://127.0.0.1:5000/logout

|

Run the example consumer

.. code-block:: console

    $ FLASK_APP=consumer.py flask run -p 5100

Start OAuth authorization flow and you will be redirected to example
application for authentication and to authorize example consumer to
access your account details on example application.

Login to example application with:

    | **username:** reader\@inveniosoftware.org
    | **password:** 123456

Review the authorization request presented to you and authorize
the example consumer.

You will be redirected back to example consumer where you can see details
of the authorization token that example application generated to
example consumer.

.. note::

    In case the authorization flow ends in an error, you can usually see
    the error in query-part of the URL.

|

Using example consumer's UI you can request a new access token from example
application either by using a refresh token or by completing
the authorization flow again.

To manage settings of OAuth2 consumer at invenio-oauth2server
settings page, login with the account that registered the consumer,
admin\@inveniosoftware.org.

To review and possibly revoke permissions of OAuth2 consumer that has
been authorized to access resources login with the account that authorized
the consumer, reader\@inveniosoftware.org.


|


This example consumer is inspired by example presented in
requests-oauthlib documentation
(http://requests-oauthlib.rtfd.io/en/latest/examples/real_world_example_with_refresh.html)
and is based on example application(s) of flask-oauthlib:
(https://github.com/lepture/flask-oauthlib/tree/master/example)
(https://github.com/lepture/flask-oauthlib/tree/master/example/contrib/experiment-client/douban.py)

Note that to support automatic refreshing of access tokens this consumer uses
flask-oauthlib.contrib.client which is considered experimental.

SPHINX-END
"""

from __future__ import print_function

import os
from functools import wraps
from pprint import pformat
from time import time

from flask import Flask, redirect, request, session, url_for
from flask_oauthlib.contrib.client import OAuth
from requests_oauthlib import OAuth2Session

# OAuth2 consumer configuration of this example consumer application
# You get the _CONSUMER_CLIENT_ID and _CONSUMER_CLIENT_SECRET when
# registering the consumer application to provider.
_CONSUMER_CLIENT_ID = 'insert_generated_client_id_here'
_CONSUMER_CLIENT_SECRET = 'insert_generated_client_secret_here'

CONSUMER_CREDENTIALS = dict(
    INVENIO_EXAMPLE_CONSUMER_CLIENT_ID=os.environ.get(
        'CONSUMER_CLIENT_ID', _CONSUMER_CLIENT_ID),
    INVENIO_EXAMPLE_CONSUMER_CLIENT_SECRET=os.environ.get(
        'CONSUMER_CLIENT_SECRET', _CONSUMER_CLIENT_SECRET),
    INVENIO_EXAMPLE_CONSUMER_SCOPE=[
        'test:scope',
        # 'email',
    ]
)


def create_app():
    # OAUTHLIB_INSECURE_TRANSPORT needed in order to use HTTP-endpoints
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

    app = Flask(__name__)
    app.config.update(CONSUMER_CREDENTIALS)
    app.secret_key = 'development'

    oauth = OAuth(app)

    # OAuth2 Provider configuration of invenio-oauth2server example app.
    remote = oauth.remote_app(
        name='invenio_example_consumer',
        # client_id='',
        # client_secret='',
        # scope=['test:scope', 'email'],
        version='2',
        endpoint_url='http://127.0.0.1:5000/',
        access_token_url='http://127.0.0.1:5000/oauth/token',
        refresh_token_url='http://127.0.0.1:5000/oauth/token',
        authorization_url='http://127.0.0.1:5000/oauth/authorize'
    )

    def oauth_token_required(f):
        """ Decorator that checks if consumer already has access_token

        Only checks the availability, not validity of the token.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if get_oauth_token() is None:
                # return redirect(url_for('.index'))
                return '<br>' \
                       '<h2>T_T You don\'t have a token yet</h2>' \
                       '<a href="{}"> Get one from here</a>' \
                       .format(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function

    @app.before_first_request
    def _run_on_start():
        print("Client_ID is {}".format(remote.client_id))
        print("Client_Secret is {}".format(remote.client_secret))
        print("Redirect url is {}".format(url_for('authorized',
                                                  _external=True)))
        print("Requested scopes: {}".format(remote.scope))

    @app.route('/', methods=['GET'])
    def index():
        """ Mainpage. Display info about token and an action menu.
        """
        if get_oauth_token():
            return """
            <h1>^_^ Congratulations, you (already?) have an OAuth 2 token!</h1>
            <h2>What would you like to do next?</h2>
            <ul>
              <li><a href="/auto_refresh"> Implicitly refresh access token</a></li>
              <li><a href="/manual_refresh"> Explicitly refresh access token</a></li>
              <li><a href="/validate"> Validate the current token</a></li>
              <li><a href="/login"> Authorize the consumer again</a></li>
              <li><a href="/logout"> Delete current token, i.e Logout</a></li>
            </ul>
            <br> Current token information: <br> <pre>{}</pre>
            """.format(pformat(get_oauth_token(), indent=4))  # noqa

        return """
            <h1>OAuth2 consumer application</h1>
            <h2>Please click the link to start OAuth authorization flow</h2>
            <ul>
              <li><a href="/login"> Start authorization flow</a></li>
            </ul>
            """

    @app.route('/login', methods=['GET'])
    def login():
        """ Prepare an authorization request and redirect client to Provider

        Prepare an authorization request and redirect client / browser to
        Provider for authentication and to answer the authorization request.

        Example of key-values sent to Provider in query part URI
        - response_type: 'code' for authz flow, 'token' for implicit flow
        - client_id: 'identifier of consumer generated by provider'
        - redirect_uri: 'where client should be redirected after authorization'
        - scope: [list of scopes consumer requesting authorization for]
        - state: used to protect against CSRF

        """
        return remote.authorize(callback_uri=url_for('authorized',
                                                     _external=True))

    @app.route('/authorized', methods=['GET', 'POST'])
    def authorized():
        """Endpoint where client is redirected after an authorization attempt.

        OAuth2 Provider will redirect client / browser to this endpoint
        after an authorization attempt has been made.

        If authorization was granted redirect request contains
        'code'-parameter in querystring.
        Consumer automatically requests an access token using this
        'code'-parameter form Provider's access_token_url

        Example of key values sent in access token request:
        - code: 'value of code parameter obtained previously'
        - client_id: 'identifier of consumer generated by provider'
        - client_secret: 'secret of consumer generated by provider'
        - grant_type: 'authorization code' as code
        - redirect_url: used only to verify client is

        Example of response received from Provider
        - access_token: 2YotnFZFEjr1zCsicMWpAA
        - token_type: Bearer
        - expires_in: 3600
        - refresh_token: tGzv3JOkF0XG5Qx2TlKWIA
        - scopes: [list of scopes consumer is authorized to]

        Possible errors in authorization process are returned in querystring.

        """
        response = remote.authorized_response()
        if response is None:
            return '<br>' \
                   '<h2>T_T Access denied</h2>' \
                   '<br>' \
                   '<pre>error={error}</pre>'\
                   '<br><a href="{link}"> Try again</a>' \
                    .format(link=url_for('index'), error=request.args['error'])
        if isinstance(response, dict) and 'access_token' in response:
            store_oauth_token(response)
            return redirect(url_for('.index'))
        return str(response)

    @app.route("/auto_refresh", methods=['GET'])
    @oauth_token_required
    def auto_refresh():
        """Obtaining a new access token automatically using a refresh token.

        By making a call to this endpoint the consumer set token to expired
        state and upon making a new request for protected resource, consumer
        first request a new access token using refresh token.

        Note that all requests and updates related to tokens happen
        behind the scenes.
        """

        # We force expiration of the token by setting expired_at value
        # of the token to a past moment.
        # This will trigger an automatic refresh next time we interact with
        # Invenio API.
        token = get_oauth_token()
        token['expires_at'] = time() - 10

        resp = remote.get('oauth/info')  # prefixed with remote.endpoint_url
        return redirect(url_for('.index'))

    @app.route("/manual_refresh", methods=['GET'])
    @oauth_token_required
    def manual_refresh():
        """Obtaining a new access token manually using a refresh token.

        Request for new access token can be sent even if the old
        access token has not yet expired.

        Unfortunately flask-oauthlib OAuthApplication doesn't provide
        manual refreshing of tokens out-of-the-box, so internal
        OAuth2Session needs to be used.

        When using OAuth2Session to refresh, client_id and client_secret
        must be provided as extra arguments.
        When doing implicit / automatic refresh with flask-oauthlib
        these values are automatically included in the request.

        Note that obtained new access token must be stored manually.
        """

        extra = {
            'client_id': remote.client_id,
            'client_secret': remote.client_secret,
        }

        oauthsession = OAuth2Session(remote.client_id, token=get_oauth_token())

        resp = oauthsession.refresh_token(remote.refresh_token_url, **extra)

        store_oauth_token(resp)

        # Alternative way
        # # Build OAuth2Session
        # oauthsession = remote.make_oauth_session(token=get_oauth_token())
        #
        # # Use the built OAuth2Session to execute refresh token request
        # # even though authorization token is still valid.
        # store_oauth_token(oauthsession.refresh_token(
        #     remote.refresh_token_url))

        return redirect(url_for('.index'))

    @app.route("/validate", methods=['GET'])
    @oauth_token_required
    def validate():
        """ Endpoint used to check validity of access token.

        Basically consumer tries to access a resource in Provider and
        if the request succeeds the token is considered to be valid.
        """
        resp = remote.get('oauth/info')  # prefixed with remote.endpoint_url
        return """Endpoint '/oauth/info' returned following information:
            <pre>{}</pre>
            <br>
            <a href="/"> Return</a>
            """.format(pformat(resp.json(), indent=4))

    @app.route('/logout', methods=['GET'])
    def logout():
        """ Endpoint to logout from the consumer.

        Consumer will delete access and refresh tokens it has stored, losing
        access to resources at Provider.
        """

        session.pop('oauth_token', None)
        return redirect(url_for('index'))

    @remote.tokengetter
    def get_oauth_token():
        """ Returns the saved OAuth token object.

        Returned object contains all the information Provider sent
        regarding to access token.

        Example of OAuth token object:
          { "access_token": "6J3JyHLoP0K9HzL21V8y3Pj73zQDVf",
          "token_type": "Bearer",
          "expires_in": 3600,
          "refresh_token": "RxFZ1CSkjJF9PeFqDCaKTWYB6V5N4w",
          "scope": "test:scope" }
        """
        return session.get('oauth_token')

    @remote.tokensaver
    def store_oauth_token(resp):
        """ Saves the OAuth token and it's metadata obtained from Provider
        """
        # request-oauthlib expects a dictionary containing at least
        # access_token and token_type values. Successful access token response
        # must always contain those values, so we can store the whole response.
        session['oauth_token'] = resp

    return app

app = create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5100)
