# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
# Copyright (C)      2021 TU Wien.
# Copyright (C) 2022 KTH Royal Institute of Technology
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Default configuration for ACCOUNTS."""

from datetime import timedelta

from invenio_i18n import lazy_gettext as _

from .profiles import UserPreferencesSchema, UserProfileSchema
from .views import login

ACCOUNTS = True
"""Tells if the templates should use the accounts module.

If False, you won't be able to login via the web UI.
"""

ACCOUNTS_RETENTION_PERIOD = timedelta(days=30)

ACCOUNTS_SESSION_STORE_FACTORY = (
    "invenio_accounts.sessions:default_session_store_factory"
)
"""Import path or function of factory used to generate the session store
object.

When  ``ACCOUNTS_SESSION_REDIS_URL`` will use redis as cache system otherwise
otherwise it will use the in-memory backend :class:`simplekv.memory.DictStore`.
"""

ACCOUNTS_SESSION_REDIS_URL = None
"""Redis URL used by the module as a cache system for sessions."""

ACCOUNTS_REGISTER_BLUEPRINT = None
"""Register the Security blueprint or not.

It can be used to override the ``register_blueprint`` option.

.. note:: If the value is ``None``, then the blueprint is not registered.
"""

ACCOUNTS_USE_CELERY = None
"""Tells if the module should use Celery or not.

By default, it uses Celery if it can find it.
"""

ACCOUNTS_SESSION_ACTIVITY_ENABLED = True
"""Enable session activity tracking."""

ACCOUNTS_SETTINGS_SECURITY_TEMPLATE = "invenio_accounts/settings/security.html"
"""Template for the account security page."""

ACCOUNTS_CONFIRM_EMAIL_ENDPOINT = None
"""Value to be used for the confirmation email link in the UI application."""

ACCOUNTS_DEFAULT_EMAIL_VISIBILITY = "restricted"
"""Default Email visibility value can be set to either 'restricted' or 'public'."""

ACCOUNTS_REST_CONFIRM_EMAIL_ENDPOINT = "/confirm/{token}"
"""Value to be used for the confirmation email link in the API application.

Can be a Flask endpoint (e.g. "invenio_accounts_rest_auth.confirm_email"), or
a URL part (e.g. "https://ui.example.com/confirm-email", "/confirm-email").

This will be used to build an absolute URL, thus if e.g. a hostname isn't
included, the one from the current request's context will be used.
"""

ACCOUNTS_RESET_PASSWORD_ENDPOINT = None
"""Value to be used for the confirmation email link in the UI application."""

ACCOUNTS_REST_RESET_PASSWORD_ENDPOINT = "/lost-password/{token}"
"""Value to be used for the reset password link in the API application.

Can be a Flask endpoint (e.g. "invenio_accounts_rest_auth.reset_password"), or
a URL part (e.g. "https://ui.example.com/reset-password", "/reset-password").

This will be used to build an absolute URL, thus if e.g. a hostname isn't
included, the one from the current request's context will be used.
"""

ACCOUNTS_REST_AUTH_VIEWS = {
    "login": "invenio_accounts.views.rest:LoginView",
    "logout": "invenio_accounts.views.rest:LogoutView",
    "user_info": "invenio_accounts.views.rest:UserInfoView",
    "register": "invenio_accounts.views.rest:RegisterView",
    "forgot_password": "invenio_accounts.views.rest:ForgotPasswordView",
    "reset_password": "invenio_accounts.views.rest:ResetPasswordView",
    "change_password": "invenio_accounts.views.rest:ChangePasswordView",
    "send_confirmation": "invenio_accounts.views.rest:SendConfirmationEmailView",
    "confirm_email": "invenio_accounts.views.rest:ConfirmEmailView",
    "sessions_list": "invenio_accounts.views.rest:SessionsListView",
    "sessions_item": "invenio_accounts.views.rest:SessionsItemView",
}
"""List of REST API authentication views."""

# Change Flask-Security defaults
SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
"""Default password hashing algorithm for new passwords."""

SECURITY_PASSWORD_SCHEMES = ["pbkdf2_sha512", "invenio_aes_encrypted_email"]
"""Supported password hashing algorithms (for passwords already stored).

You should include both the default, supported and any deprecated schemes.
"""

SECURITY_DEPRECATED_PASSWORD_SCHEMES = ["invenio_aes_encrypted_email"]
"""Deprecated password hashing algorithms.

Password hashes in a deprecated scheme are automatically migrated to the
new default algorithm the next time the user login.
"""

SECURITY_PASSWORD_SINGLE_HASH = ["invenio_aes_encrypted_email"]
"""Password hashing algorithms requiring single hasing only."""

SECURITY_DEFAULT_REMEMBER_ME = False
""""Remember me" default value in login form.

This is only the default value in the login form. A user can always choose to
change it when they login.
"""

SECURITY_CHANGEABLE = True
"""Allow password change by users."""

SECURITY_CONFIRMABLE = True
"""Allow user to confirm their email address."""

SECURITY_RECOVERABLE = True
"""Allow password recovery by users."""

SECURITY_REGISTERABLE = True
"""Allow users to register."""

SECURITY_CONFIRM_EMAIL_WITHIN = "30 minutes"
"""Amount of time the email confirmation link is active.

Note, since the confirmation link will also login the associated user we expire
the link fast.
"""

SECURITY_RESET_PASSWORD_WITHIN = "30 minutes"
"""Amount of time the password reset link is active.

Note, since the confirmation link will also login the associated user we expire
the link fast.
"""

SECURITY_TRACKABLE = True
"""Enable user tracking on login."""

SECURITY_LOGIN_WITHOUT_CONFIRMATION = True
"""Allow users to login without first confirming their email address."""

SECURITY_PASSWORD_SALT = None
"""Salt for storing passwords."""

# Change default templates
SECURITY_FORGOT_PASSWORD_TEMPLATE = "invenio_accounts/forgot_password.html"
"""Default template for password recovery (asking for email)."""

SECURITY_LOGIN_USER_TEMPLATE = "invenio_accounts/login_user.html"
"""Default template for login."""

SECURITY_REGISTER_USER_TEMPLATE = "invenio_accounts/register_user.html"
"""Default template for user registration."""

SECURITY_RESET_PASSWORD_TEMPLATE = "invenio_accounts/reset_password.html"
"""Default template for password recovery (reset of the password)."""

SECURITY_CHANGE_PASSWORD_TEMPLATE = "invenio_accounts/change_password.html"
"""Default template for change password."""

SECURITY_SEND_CONFIRMATION_TEMPLATE = "invenio_accounts/send_confirmation.html"
"""Default template for email confirmation."""

SECURITY_SEND_LOGIN_TEMPLATE = "invenio_accounts/send_login.html"
"""Default template for email confirmation."""

SECURITY_REGISTER_URL = "/signup/"
"""URL endpoint for user registation."""

SECURITY_RESET_URL = "/lost-password/"
"""URL endpoint for password recovery."""

SECURITY_LOGIN_URL = "/login/"
"""URL endpoint for login."""

SECURITY_LOGOUT_URL = "/logout/"
"""URL endpoint for logout."""

SECURITY_CHANGE_URL = "/account/settings/password/"
"""URL endpoint for password change."""

SECURITY_MSG_LOCAL_LOGIN_DISABLED = ("Local login is disabled.", "error")
"""The error to be displayed in REST login when local login is disabled."""

SECURITY_MSG_REGISTRATION_DISABLED = ("Registration is disabled.", "error")
"""The error to be displayed in REST registration when it is disabled."""

SECURITY_MSG_PASSWORD_CHANGE_DISABLED = ("Password change is disabled.", "error")
"""The error to be displayed in REST password change when it is disabled."""

SECURITY_MSG_PASSWORD_RECOVERY_DISABLED = ("Password recovery is disabled.", "error")
"""The error to be displayed in REST password recovery when it is disabled."""

SECURITY_MSG_PASSWORD_RESET_DISABLED = ("Password reset is disabled.", "error")
"""The error to be displayed in REST password reset when it is disabled."""

REMEMBER_COOKIE_DURATION = timedelta(days=90)
"""Remember me cookie life time changed to 90 days instead of 365 days."""

# JWT related config
ACCOUNTS_JWT_ENABLE = True
"""Enable JWT support.

.. note::

    More details about `JWT <https://jwt.io>`_
"""

ACCOUNTS_JWT_DOM_TOKEN = True
"""Register JWT context processor.

.. code-block:: html

    {% if current_user.is_authenticated %}
        {{ jwt() }}
    {% endif %}

This will generate a ``hidden`` field as follows:

.. code-block:: html

    <input type="hidden" name="authorized_token" value="xxx">

On your API call you can use it with simple javascript, an example using
``jQuery`` is the following:

.. code-block:: javascript

    $.ajax({
        url: '/example',
        method: 'POST',
        beforeSend: function(request) {
            request.setRequestHeader(
                'Authorization',
                'Bearer ' + $('[name=authorized_token]').val()
            );
        },
    });
"""

ACCOUNTS_JWT_DOM_TOKEN_TEMPLATE = "invenio_accounts/jwt.html"
"""Template for the context processor."""

ACCOUNTS_JWT_SECRET_KEY = None
"""Secret key for JWT.

.. note::

    If is set to ``None`` it will use the ``SECRET_KEY``.
"""

ACCOUNTS_JWT_EXPIRATION_DELTA = timedelta(days=1)
"""Token expiration period for JWT."""

ACCOUNTS_JWT_ALOGORITHM = "HS256"
"""Set JWT encryption alogirthm.

.. note::

   `Available aglorithms
   <https://pyjwt.readthedocs.io/en/latest/algorithms.html>`_
"""

ACCOUNTS_JWT_DECODE_FACTORY = "invenio_accounts.utils:jwt_decode_token"
"""Import path of factory used to decode JWT."""

ACCOUNTS_JWT_CREATION_FACTORY = "invenio_accounts.utils:jwt_create_token"
"""Import path of factory used to generate JWT."""

RECAPTCHA_PUBLIC_KEY = None
"""reCAPTCHA public key."""

RECAPTCHA_PRIVATE_KEY = None
"""reCAPTCHA private key."""

ACCOUNTS_USERINFO_HEADERS = False
"""If True, add X-Session-ID and X-User-ID to the HTTP response."""

ACCOUNTS_LOGIN_VIEW_FUNCTION = login
"""The view function to use for the login endpoint.

This can be either an import string, or the view function itself.
If set to None, the default login view function from Flask-Security will be
left as is.
"""

ACCOUNTS_LOCAL_LOGIN_ENABLED = True
"""Whether or not login with local account credentials should be enabled."""

ACCOUNTS_USER_PREFERENCES_SCHEMA = UserPreferencesSchema()
"""The schema to use for validation of the user preferences."""

ACCOUNTS_USER_PROFILE_SCHEMA = UserProfileSchema()
"""The schema to use for validation of the user profile."""

ACCOUNTS_DEFAULT_USER_VISIBILITY = "restricted"
"""Default User visibility value can be set to either 'restricted' or 'public'."""

ACCOUNTS_USERNAME_REGEX = r"^[a-zA-Z][a-zA-Z0-9-_]{2,255}$"
"""The regular expression used for validating usernames.

.. note:: When this configuration value is overridden, the value for
          ``ACCOUNTS_USERNAME_RULES_TEXT`` should be updated as well,
          to reflect the changes.
"""

ACCOUNTS_USERNAME_RULES_TEXT = _(
    "Username must start with a letter, be at least three characters long and"
    " only contain alphanumeric characters, dashes and underscores."
)
"""Description of username validation rules.

.. note:: Used for both form help text and for form validation error.
"""

ACCOUNTS_DEFAULT_USERS_VERIFIED = False
"""Default verified status: if set to 'True', users are verified by default."""
