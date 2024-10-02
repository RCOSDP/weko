# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2024 CERN.
# Copyright (C)      2021 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API user management and authentication."""

from functools import wraps

from flask import Blueprint, after_this_request, current_app, jsonify
from flask.views import MethodView
from flask_login import login_required
from flask_security import current_user
from flask_security.confirmable import (
    confirm_email_token_status,
    confirm_user,
    requires_confirmation,
)
from flask_security.recoverable import reset_password_token_status, update_password
from flask_security.signals import reset_password_instructions_sent
from flask_security.utils import (
    config_value,
    get_message,
    login_user,
    logout_user,
    send_mail,
    verify_and_update_password,
)
from flask_security.views import logout
from invenio_db import db
from invenio_i18n import gettext as _
from invenio_rest.errors import FieldError, RESTValidationError
from webargs import ValidationError, fields, validate
from webargs.flaskparser import FlaskParser as FlaskParserBase

from invenio_accounts.models import SessionActivity
from invenio_accounts.sessions import delete_session

from ..proxies import current_datastore, current_security
from ..utils import (
    change_user_password,
    default_confirmation_link_func,
    default_reset_password_link_func,
    obj_or_import_string,
    register_user,
    validate_domain,
)


def user_already_authenticated(f):
    """Return user if already authenticated."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return jsonify(default_user_payload(current_user))
        return f(*args, **kwargs)

    return wrapper


def role_to_dict(role):
    """Serialize a new role to dict.

    :param role: a new role to serialize into dict.
    :return: dict from role.
    :rtype: dict.
    """
    return dict(
        id=role.id,
        name=role.name,
        description=role.description,
    )


def create_rest_blueprint(app):
    """Conditionally creates the blueprint."""
    blueprint = Blueprint("invenio_accounts_rest_auth", __name__)

    security_state = app.extensions["security"]

    if app.config["ACCOUNTS_REST_AUTH_VIEWS"]:
        # Resolve the view classes
        authentication_views = {
            k: obj_or_import_string(v)
            for k, v in app.config.get("ACCOUNTS_REST_AUTH_VIEWS", {}).items()
        }

        blueprint.add_url_rule(
            "/login", view_func=authentication_views["login"].as_view("login")
        )
        blueprint.add_url_rule(
            "/logout", view_func=authentication_views["logout"].as_view("logout")
        )
        blueprint.add_url_rule(
            "/me", view_func=authentication_views["user_info"].as_view("user_info")
        )

        if security_state.registerable:
            blueprint.add_url_rule(
                "/register",
                view_func=authentication_views["register"].as_view("register"),
            )

        if security_state.changeable:
            blueprint.add_url_rule(
                "/change-password",
                view_func=authentication_views["change_password"].as_view(
                    "change_password"
                ),
            )

        if security_state.recoverable:
            blueprint.add_url_rule(
                "/forgot-password",
                view_func=authentication_views["forgot_password"].as_view(
                    "forgot_password"
                ),
            )
            blueprint.add_url_rule(
                "/reset-password",
                view_func=authentication_views["reset_password"].as_view(
                    "reset_password"
                ),
            )

        if security_state.confirmable:
            blueprint.add_url_rule(
                "/send-confirmation-email",
                view_func=authentication_views["send_confirmation"].as_view(
                    "send_confirmation"
                ),
            )

            blueprint.add_url_rule(
                "/confirm-email",
                view_func=authentication_views["confirm_email"].as_view(
                    "confirm_email"
                ),
            )

        if app.config["ACCOUNTS_SESSION_ACTIVITY_ENABLED"]:
            blueprint.add_url_rule(
                "/sessions",
                view_func=authentication_views["sessions_list"].as_view(
                    "sessions_list"
                ),
            )

            blueprint.add_url_rule(
                "/sessions/<sid_s>",
                view_func=authentication_views["sessions_item"].as_view(
                    "sessions_item"
                ),
            )
    return blueprint


class FlaskParser(FlaskParserBase):
    """Parser to add FieldError to validation errors."""

    def handle_error(self, error, *args, **kwargs):
        """Handle errors during parsing."""
        if isinstance(error, ValidationError):
            _errors = []
            for field, messages in error.messages.items():
                _errors.extend([FieldError(field, msg) for msg in messages])
            raise RESTValidationError(errors=_errors)
        super(FlaskParser, self).handle_error(error, *args, **kwargs)


webargs_parser = FlaskParser()
use_args = webargs_parser.use_args
use_kwargs = webargs_parser.use_kwargs


#
# Field validators
#
def user_exists(email):
    """Validate that a user exists."""
    with db.session.no_autoflush:
        if not current_datastore.get_user(email):
            raise ValidationError(get_message("USER_DOES_NOT_EXIST")[0])


def unique_user_email(email):
    """Validate unique user email."""
    with db.session.no_autoflush:
        if current_datastore.get_user(email) is not None:
            raise ValidationError(
                get_message("EMAIL_ALREADY_ASSOCIATED", email=email)[0]
            )


def default_user_payload(user):
    """Parse user payload."""
    fmt_last_login_at = None
    if user.login_info and user.login_info.last_login_at:
        fmt_last_login_at = user.login_info.last_login_at.isoformat()

    return {
        "id": user.id,
        "email": user.email,
        "confirmed_at": user.confirmed_at.isoformat() if user.confirmed_at else None,
        "last_login_at": fmt_last_login_at,
        "roles": [role_to_dict(role) for role in user.roles],
    }


def validate_domain_rest(email):
    """Validator for use with WTForm."""
    if not validate_domain(email):
        raise ValidationError(_("The email domain is blocked."))


def _abort(message, field=None, status=None):
    if field:
        raise RESTValidationError([FieldError(field, message)])
    raise RESTValidationError(description=message)


def _commit(response=None):
    current_datastore.commit()
    return response


class UserViewMixin(object):
    """Mixin class for get user operations."""

    def get_user(self, email=None, **kwargs):
        """Retrieve a user by the provided arguments."""
        with db.session.no_autoflush:
            return current_datastore.get_user(email)


class LoginView(MethodView, UserViewMixin):
    """View to login a user."""

    decorators = [user_already_authenticated]

    post_args = {
        "email": fields.Email(required=True, validate=[user_exists]),
        "password": fields.String(required=True),
    }

    def success_response(self, user):
        """Return a successful login response."""
        return jsonify(default_user_payload(user))

    def verify_login(self, user, password=None, **kwargs):
        """Verify the login via password."""
        if not user.password:
            _abort(get_message("PASSWORD_NOT_SET")[0], "password")
        if not verify_and_update_password(password, user):
            _abort(get_message("INVALID_PASSWORD")[0], "password")
        if requires_confirmation(user):
            _abort(get_message("CONFIRMATION_REQUIRED")[0])
        if not user.is_active:
            _abort(get_message("DISABLED_ACCOUNT")[0])

    def login_user(self, user):
        """Perform any login actions."""
        return login_user(user)

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Verify and login a user."""
        if not current_app.config.get("ACCOUNTS_LOCAL_LOGIN_ENABLED"):
            _abort(get_message("LOCAL_LOGIN_DISABLED")[0])

        user = self.get_user(**kwargs)
        self.verify_login(user, **kwargs)
        self.login_user(user)
        return self.success_response(user)


class UserInfoView(MethodView):
    """View to fetch info from current user."""

    decorators = [login_required]

    def success_response(self, user):
        """Return a successful user info response."""
        return jsonify(default_user_payload(user))

    def get(self):
        """Return user info."""
        return self.success_response(current_user)


class LogoutView(MethodView):
    """View to logout a user."""

    def logout_user_without_post_redirect(self):
        """Perform any logout actions."""
        if current_user.is_authenticated:
            logout_user()

    def success_response(self):
        """Return a successful logout response."""
        return jsonify({"message": "User logged out."})

    def post(self):
        """Logout a user."""
        self.logout_user_without_post_redirect()
        return self.success_response()

    def get(self):
        """Logout user."""
        return logout()


class RegisterView(MethodView):
    """View to register a new user."""

    decorators = [user_already_authenticated]

    post_args = {
        "email": fields.Email(
            required=True, validate=[unique_user_email, validate_domain_rest]
        ),
        "password": fields.String(
            required=True, validate=[validate.Length(min=6, max=128)]
        ),
    }

    def login_user(self, user):
        """Perform any login actions."""
        if (
            not current_security.confirmable
            or current_security.login_without_confirmation
        ):
            after_this_request(_commit)
            login_user(user)

    def success_response(self, user):
        """Return a successful register response."""
        return jsonify(default_user_payload(user))

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Register a user."""
        if not current_security.registerable:
            _abort(get_message("REGISTRATION_DISABLED")[0])

        user = register_user(**kwargs)
        self.login_user(user)
        return self.success_response(user)


class ForgotPasswordView(MethodView, UserViewMixin):
    """View to get a link to reset the user password."""

    decorators = [user_already_authenticated]

    reset_password_link_func = default_reset_password_link_func

    post_args = {
        "email": fields.Email(required=True, validate=[user_exists]),
    }

    @classmethod
    def send_reset_password_instructions(cls, user):
        """Send email containing instructions to reset password."""
        token, reset_link = cls.reset_password_link_func(user)
        if config_value("SEND_PASSWORD_RESET_EMAIL"):
            send_mail(
                config_value("EMAIL_SUBJECT_PASSWORD_RESET"),
                user.email,
                "reset_instructions",
                user=user,
                reset_link=reset_link,
            )
            reset_password_instructions_sent.send(
                current_app._get_current_object(), user=user, token=token
            )

    def success_response(self, user):
        """Return a response containing reset password instructions."""
        return jsonify(
            {"message": get_message("PASSWORD_RESET_REQUEST", email=user.email)[0]}
        )

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Send reset password instructions."""
        if not current_security.recoverable:
            _abort(get_message("PASSWORD_RECOVERY_DISABLED")[0])

        user = self.get_user(**kwargs)
        self.send_reset_password_instructions(user)
        return self.success_response(user)


class ResetPasswordView(MethodView):
    """View to reset the user password."""

    decorators = [user_already_authenticated]

    post_args = {
        "token": fields.String(required=True),
        "password": fields.String(
            required=True, validate=[validate.Length(min=6, max=128)]
        ),
    }

    def get_user(self, token=None, **kwargs):
        """Retrieve a user by the provided arguments."""
        # Verify the token
        expired, invalid, user = reset_password_token_status(token)
        if invalid:
            _abort(get_message("INVALID_RESET_PASSWORD_TOKEN")[0])
        if expired:
            _abort(
                get_message(
                    "PASSWORD_RESET_EXPIRED",
                    email=user.email,
                    within=current_security.reset_password_within,
                )[0]
            )
        return user

    def success_response(self, user):
        """Return a successful reset password response."""
        return jsonify({"message": get_message("PASSWORD_RESET")[0]})

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Reset user password."""
        # TODO there doesn't seem to be a `.resettable` or similar?
        if not current_security.recoverable:
            _abort(get_message("PASSWORD_RESET_DISABLED")[0])

        user = self.get_user(**kwargs)
        after_this_request(_commit)
        update_password(user, kwargs["password"])
        login_user(user)
        return self.success_response(user)


class ChangePasswordView(MethodView):
    """View to change the user password."""

    decorators = [login_required]

    post_args = {
        "password": fields.String(
            required=True, validate=[validate.Length(min=6, max=128)]
        ),
        "new_password": fields.String(
            required=True, validate=[validate.Length(min=6, max=128)]
        ),
    }

    def verify_password(self, password=None, new_password=None, **kwargs):
        """Verify password is not invalid."""
        if not verify_and_update_password(password, current_user):
            _abort(get_message("INVALID_PASSWORD")[0], "password")
        if password == new_password:
            _abort(get_message("PASSWORD_IS_THE_SAME")[0], "password")

    def change_password(self, new_password=None, **kwargs):
        """Perform any change password actions."""
        after_this_request(_commit)
        change_user_password(
            user=current_user._get_current_object(), password=new_password
        )

    def success_response(self):
        """Return a successful change password response."""
        return jsonify({"message": get_message("PASSWORD_CHANGE")[0]})

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Change user password."""
        if not current_security.changeable:
            _abort(get_message("PASSWORD_CHANGE_DISABLED")[0])

        self.verify_password(**kwargs)
        self.change_password(**kwargs)
        return self.success_response()


class SendConfirmationEmailView(MethodView, UserViewMixin):
    """View function which sends confirmation instructions."""

    decorators = [login_required]

    confirmation_link_func = default_confirmation_link_func

    post_args = {
        "email": fields.Email(required=True, validate=[user_exists]),
    }

    def verify(self, user):
        """Verify that user is not confirmed."""
        if user.confirmed_at is not None:
            _abort(get_message("ALREADY_CONFIRMED")[0])

    @classmethod
    def send_confirmation_link(cls, user):
        """Send confirmation link."""
        send_email_enabled = current_security.confirmable and config_value(
            "SEND_REGISTER_EMAIL"
        )
        if send_email_enabled:
            token, confirmation_link = cls.confirmation_link_func(user)
            send_mail(
                config_value("EMAIL_SUBJECT_REGISTER"),
                user.email,
                "confirmation_instructions",
                user=user,
                confirmation_link=confirmation_link,
            )
            return token

    def success_response(self, user):
        """Return a successful confirmation email sent response."""
        return jsonify(
            {"message": get_message("CONFIRMATION_REQUEST", email=user.email)[0]}
        )

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Send confirmation email."""
        user = self.get_user(**kwargs)
        self.verify(user)
        self.send_confirmation_link(user)
        return self.success_response(user)


class ConfirmEmailView(MethodView):
    """View that handles a email confirmation request."""

    post_args = {
        "token": fields.String(required=True),
    }

    def get_user(self, token=None, **kwargs):
        """Retrieve a user by the provided arguments."""
        expired, invalid, user = confirm_email_token_status(token)

        if not user or invalid:
            _abort(get_message("INVALID_CONFIRMATION_TOKEN"))

        already_confirmed = user is not None and user.confirmed_at is not None
        if expired and not already_confirmed:
            _abort(
                get_message(
                    "CONFIRMATION_EXPIRED",
                    email=user.email,
                    within=current_security.confirm_email_within,
                )
            )
        return user

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Confirm user email."""
        user = self.get_user(**kwargs)

        if user != current_user:
            logout_user()

        if confirm_user(user):
            after_this_request(_commit)
            return jsonify({"message": get_message("EMAIL_CONFIRMED")[0]})
        else:
            return jsonify({"message": get_message("ALREADY_CONFIRMED")[0]})


class SessionsListView(MethodView):
    """View that returns the list of user sessions."""

    decorators = [login_required]

    def get(self, **kwargs):
        """Return user sessions info."""
        sessions = SessionActivity.query_by_user(user_id=current_user.get_id())
        results = [
            {
                "created": s.created,
                "current": SessionActivity.is_current(s.sid_s),
                "browser": s.browser,
                "browser_version": s.browser_version,
                "os": s.os,
                "device": s.device,
                "country": s.country,
            }
            for s in sessions
        ]

        return jsonify({"total": sessions.count(), "results": results})


class SessionsItemView(MethodView):
    """View for operations related to user session."""

    decorators = [login_required]

    def delete(self, sid_s=None, **kwargs):
        """Revoke the given user session."""
        if (
            SessionActivity.query_by_user(current_user.get_id())
            .filter_by(sid_s=sid_s)
            .count()
            == 1
        ):
            delete_session(sid_s=sid_s)
            db.session.commit()
            message = "Session {0} successfully removed. {1}."
            if SessionActivity.is_current(sid_s=sid_s):
                message = message.format(sid_s, "Logged out")
            else:
                message = message.format(sid_s, "Revoked")
            return jsonify({"message": message})
        else:
            return (
                jsonify({"message": "Unable to remove session {0}.".format(sid_s)}),
                400,
            )
