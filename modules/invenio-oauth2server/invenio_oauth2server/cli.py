# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI commands for managing the OAuth server."""

from functools import wraps

import click
from flask.cli import with_appcontext
from invenio_accounts.models import User
from invenio_db import db
from werkzeug.local import LocalProxy

from .models import Client, Token
from .validators import validate_scopes


def lazy_result(f):
    """Decorate function to return LazyProxy."""

    @wraps(f)
    def decorated(ctx, param, value):
        return LocalProxy(lambda: f(ctx, param, value))

    return decorated


@lazy_result
def process_user(ctx, param, value):
    """Return a user if exists."""
    if value:
        if value.isdigit():
            user = User.query.get(str(value))
        else:
            user = User.query.filter(User.email == value).one_or_none()
        return user


@lazy_result
def process_scopes(ctx, param, values):
    """Return a user if exists."""
    validate_scopes(values)
    return values


@click.group()
def tokens():
    """OAuth2 server token commands."""


@tokens.command("create")
@click.option("-n", "--name", required=True)
@click.option(
    "-u", "--user", required=True, callback=process_user, help="User ID or email."
)
@click.option("-s", "--scope", "scopes", multiple=True, callback=process_scopes)
@click.option("-i", "--internal", is_flag=True)
@with_appcontext
def tokens_create(name, user, scopes, internal):
    """Create a personal OAuth token."""
    token = Token.create_personal(name, user.id, scopes=scopes, is_internal=internal)
    db.session.commit()
    click.secho(token.access_token, fg="blue")


@tokens.command("delete")
@click.option("-n", "--name")
@click.option("-u", "--user", callback=process_user, help="User ID or email.")
@click.option("--token", "read_access_token", is_flag=True)
@click.option("--force", is_flag=True)
@with_appcontext
def tokens_delete(name=None, user=None, read_access_token=None, force=False):
    """Delete a personal OAuth token."""
    if not (name or user) and not read_access_token:
        click.get_current_context().fail(
            'You have to pass either a "name" and "user" or the "token"'
        )
    if name and user:
        client = Client.query.filter(
            Client.user_id == user.id, Client.name == name, Client.is_internal.is_(True)
        ).one()
        token = Token.query.filter(
            Token.user_id == user.id,
            Token.is_personal.is_(True),
            Token.client_id == client.client_id,
        ).one()
    elif read_access_token:
        access_token = click.prompt("Token", hide_input=True)
        token = Token.query.filter(Token.access_token == access_token).one()
    else:
        click.get_current_context().fail("No token was found with provided")
    if force or click.confirm("Are you sure you want to delete the token?"):
        db.session.delete(token)
        db.session.commit()
        click.secho('Token "{}" deleted.'.format(token.access_token), fg="yellow")
