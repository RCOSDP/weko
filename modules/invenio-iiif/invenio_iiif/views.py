# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 Esteban J. G. Gabancho.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Factory for creating a blueprint for IIIF Presentatin layer."""

import json
from functools import partial

from flask import Blueprint, abort, current_app, redirect, url_for
from invenio_pidstore.errors import (
    PIDDeletedError,
    PIDDoesNotExistError,
    PIDMissingObjectError,
    PIDRedirectedError,
    PIDUnregistered
)
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_records_files.api import Record
from invenio_db import db
from werkzeug.routing import BuildError
from werkzeug.utils import import_string

from .manifest import IIIFManifest


def create_blueprint_from_app(app):
    """Create Invenio-IIIF blueprint from a Flask application.

    .. note::

        This function assumes that the application has loaded all extensions
        that want to register REST endpoints via the
        ``IIIF_MANIFEST_ENDPOINTS`` configuration variable.

    :params app: A Flask application.
    :returns: Configured blueprint.
    """
    # TODO maybe we can do better?
    endpoints = app.config.get('IIIF_MANIFEST_ENDPOINTS')
    for endpoint in endpoints.values():
        if 'route' in endpoint:
            endpoint['route'] = '/'.join(
                s.strip('/')
                for s in (
                    app.config['IIIF_API_PREFIX'],
                    'v2',
                    endpoint['route'],
                    'manifest.json',
                )
            )

    return create_blueprint(endpoints)


def create_blueprint(endpoints):
    """Create Invenio-Records-REST blueprint.

    :params endpoints: Dictionary representing the endpoints configuration.
    :returns: Configured blueprint.
    """
    blueprint = Blueprint('invenio_iiif_presentation', __name__, url_prefix='')
    
    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("invneio_iiif dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        blueprint.add_url_rule(**create_url_rule(endpoint, **options))

    return blueprint


def create_url_rule(
    endpoint,
    route=None,
    pid_type=None,
    permission_factory_imp=None,
    record_class=None,
    manifest_class=None,
):
    """Create Werkzeug URL rule for a specific endpoint."""
    assert route
    assert pid_type

    permission_factory = (
        import_string(permission_factory_imp)
        if permission_factory_imp
        else None
    )
    record_class = import_string(record_class) if record_class else Record
    manifest_class = (
        import_string(manifest_class) if manifest_class else IIIFManifest
    )


    view_func = partial(
        manifest_view,
        resolver=Resolver(
            pid_type=pid_type,
            object_type='rec',
            getter=record_class.get_record,
        ),
        permission_factory=permission_factory,
        manifest_class=manifest_class,
    )
    # Make view well-behaved for Flask-DebugToolbar
    view_func.__module__ = manifest_view.__module__
    view_func.__name__ = manifest_view.__name__
    return dict(
        endpoint=endpoint, rule=route, view_func=view_func, methods=['GET']
    )


def manifest_view(
    pid_value=None,
    resolver=None,
    permission_factory=None,
    manifest_class=None,
    **kwargs
):
    """IIIF manifest view."""
    try:
        pid, record = resolver.resolve(pid_value)
    except (PIDDoesNotExistError, PIDUnregistered):
        abort(404)
    except PIDMissingObjectError as e:
        current_app.logger.exception(
            "No object assigned to {0}.".format(e.pid), extra={'pid': e.pid}
        )
        abort(500)
    except PIDRedirectedError as e:
        try:
            return redirect(
                url_for(
                    '.{0}'.format(e.destination_pid.pid_type),
                    pid_value=e.destination_pid.pid_value,
                )
            )
        except BuildError:
            current_app.logger.exception(
                "Invalid redirect - pid_type '{0}' endpoint missing.".format(
                    e.destination_pid.pid_type
                ),
                extra={'pid': e.pid, 'destination_pid': e.destination_pid},
            )
            abort(500)

    # TODO Check permissions

    manifest = manifest_class(record)
    data = manifest.dumps()

    if not data:
        response = current_app.response_class(mimetype='application/json')
        response.status_code = 204
    else:
        response = current_app.response_class(
            json.dumps(data), mimetype='application/json'
        )

    return response
