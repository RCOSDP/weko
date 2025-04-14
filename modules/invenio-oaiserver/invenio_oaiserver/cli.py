import click
from flask import current_app
from flask.cli import with_appcontext
from .tasks import create_data

@click.group()
def oaipmh_file_create():
    """Event management commands."""


@oaipmh_file_create.command('create_file')
@with_appcontext
def file_create():
    """File create events."""
    create_data()

