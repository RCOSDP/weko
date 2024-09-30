# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Deposit actions."""

from __future__ import absolute_import, print_function

import json
from copy import deepcopy
from functools import partial

from flask import Blueprint, abort, current_app, make_response, request, \
    url_for
from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_records_rest.views import \
    create_url_rules as records_rest_url_rules
from invenio_records_rest.views import need_record_permission, pass_record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from webargs import fields
from webargs.flaskparser import use_kwargs
from werkzeug.utils import secure_filename

from ..api import Deposit
from ..errors import FileAlreadyExists, WrongFile
from ..scopes import write_scope
from ..search import DepositSearch
from ..signals import post_action
from ..utils import extract_actions_from_class


def create_error_handlers(blueprint):
    """Create error handlers on blueprint."""
    blueprint.errorhandler(PIDInvalidAction)(create_api_errorhandler(
        status=403, message='Invalid action'
    ))
    records_rest_error_handlers(blueprint)


def create_blueprint(endpoints):
    """Create Invenio-Deposit-REST blueprint.

    See: :data:`invenio_deposit.config.DEPOSIT_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'invenio_deposit_rest',
        __name__,
        url_prefix='',
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("invenio_deposit dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    create_error_handlers(blueprint)

    for endpoint, options in (endpoints or {}).items():
        options = deepcopy(options)

        if 'files_serializers' in options:
            files_serializers = options.get('files_serializers')
            files_serializers = {mime: obj_or_import_string(func)
                                 for mime, func in files_serializers.items()}
            del options['files_serializers']
        else:
            files_serializers = {}

        if 'record_serializers' in options:
            serializers = options.get('record_serializers')
            serializers = {mime: obj_or_import_string(func)
                           for mime, func in serializers.items()}
        else:
            serializers = {}

        file_list_route = options.pop(
            'file_list_route',
            '{0}/files'.format(options['item_route'])
        )
        file_item_route = options.pop(
            'file_item_route',
            '{0}/files/<path:key>'.format(options['item_route'])
        )

        options.setdefault('search_class', DepositSearch)
        search_class = obj_or_import_string(options['search_class'])

        # records rest endpoints will use the deposit class as record class
        options.setdefault('record_class', Deposit)
        record_class = obj_or_import_string(options['record_class'])

        # backward compatibility for indexer class
        options.setdefault('indexer_class', None)

        for rule in records_rest_url_rules(endpoint, **options):
            blueprint.add_url_rule(**rule)

        search_class_kwargs = {}
        if options.get('search_index'):
            search_class_kwargs['index'] = options['search_index']

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            create_permission_factory=obj_or_import_string(
                options.get('create_permission_factory_imp')
            ),
            update_permission_factory=obj_or_import_string(
                options.get('update_permission_factory_imp')
            ),
            delete_permission_factory=obj_or_import_string(
                options.get('delete_permission_factory_imp')
            ),
            record_class=record_class,
            search_class=partial(search_class, **search_class_kwargs),
            default_media_type=options.get('default_media_type'),
        )

        deposit_actions = DepositActionResource.as_view(
            DepositActionResource.view_name.format(endpoint),
            serializers=serializers,
            pid_type=options['pid_type'],
            ctx=ctx,
        )

        blueprint.add_url_rule(
            '{0}/actions/<any({1}):action>'.format(
                options['item_route'],
                ','.join(extract_actions_from_class(record_class)),
            ),
            view_func=deposit_actions,
            methods=['POST'],
        )

        deposit_files = DepositFilesResource.as_view(
            DepositFilesResource.view_name.format(endpoint),
            serializers=files_serializers,
            pid_type=options['pid_type'],
            ctx=ctx,
        )

        blueprint.add_url_rule(
            file_list_route,
            view_func=deposit_files,
            methods=['GET', 'POST', 'PUT'],
        )

        deposit_file = DepositFileResource.as_view(
            DepositFileResource.view_name.format(endpoint),
            serializers=files_serializers,
            pid_type=options['pid_type'],
            ctx=ctx,
        )

        blueprint.add_url_rule(
            file_item_route,
            view_func=deposit_file,
            methods=['GET', 'PUT', 'DELETE'],
        )
    return blueprint


class DepositActionResource(ContentNegotiatedMethodView):
    """Deposit action resource."""

    view_name = '{0}_actions'

    def __init__(self, serializers, pid_type, ctx, *args, **kwargs):
        """Constructor."""
        super(DepositActionResource, self).__init__(
            serializers,
            default_media_type=ctx.get('default_media_type'),
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @pass_record
    @need_record_permission('update_permission_factory')
    def post(self, pid, record, action):
        """Handle deposit action.

        After the action is executed, a
        :class:`invenio_deposit.signals.post_action` signal is sent.

        Permission required: `update_permission_factory`.

        :param pid: Pid object (from url).
        :param record: Record object resolved from the pid.
        :param action: The action to execute.
        """
        record = getattr(record, action)(pid=pid)

        db.session.commit()
        # Refresh the PID and record metadata
        db.session.refresh(pid)
        db.session.refresh(record.model)
        post_action.send(current_app._get_current_object(), action=action,
                         pid=pid, deposit=record)
        response = self.make_response(pid, record,
                                      202 if action == 'publish' else 201)
        endpoint = '.{0}_item'.format(pid.pid_type)
        location = url_for(endpoint, pid_value=pid.pid_value, _external=True)
        response.headers.extend(dict(Location=location))
        return response


class DepositFilesResource(ContentNegotiatedMethodView):
    """Deposit files resource."""

    view_name = '{0}_files'

    def __init__(self, serializers, pid_type, ctx, *args, **kwargs):
        """Constructor."""
        super(DepositFilesResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @pass_record
    @need_record_permission('read_permission_factory')
    def get(self, pid, record):
        """Get files.

        Permission required: `read_permission_factory`.

        :param pid: Pid object (from url).
        :param record: Record object resolved from the pid.
        :returns: The files.
        """
        return self.make_response(obj=record.files, pid=pid, record=record)

    @require_api_auth()
    @require_oauth_scopes(write_scope.id)
    @pass_record
    @need_record_permission('update_permission_factory')
    def post(self, pid, record):
        """Handle POST deposit files.

        Permission required: `update_permission_factory`.

        :param pid: Pid object (from url).
        :param record: Record object resolved from the pid.
        """
        try:
            # load the file
            uploaded_file = request.files['file']
            # file name
            key = secure_filename(
                request.form.get('name') or uploaded_file.filename
            )
            # check if already exists a file with this name
            if key in record.files:
                raise FileAlreadyExists()
            # add it to the deposit
            record.files[key] = uploaded_file.stream
            record.commit()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            raise WrongFile()

        return self.make_response(
            obj=record.files[key].obj, pid=pid, record=record, status=201)

    @require_api_auth()
    @require_oauth_scopes(write_scope.id)
    @pass_record
    @need_record_permission('update_permission_factory')
    def put(self, pid, record):
        """Handle the sort of the files through the PUT deposit files.

        Expected input in body PUT:

        .. code-block:: javascript

            [
                {
                    "id": 1
                },
                {
                    "id": 2
                },
                ...
            }

        Permission required: `update_permission_factory`.

        :param pid: Pid object (from url).
        :param record: Record object resolved from the pid.
        :returns: The files.
        """
        try:
            ids = [data['id'] for data in json.loads(
                request.data.decode('utf-8'))]
        except KeyError:
            raise WrongFile()

        try:
            record.files.sort_by(*ids)
            record.commit()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            raise WrongFile()

        return self.make_response(obj=record.files, pid=pid, record=record)


class DepositFileResource(ContentNegotiatedMethodView):
    """Deposit files resource."""

    view_name = '{0}_file'

    get_args = dict(
        version_id=fields.UUID(
            location='headers',
            load_from='version_id',
        ),
    )
    """GET query arguments."""

    def __init__(self, serializers, pid_type, ctx, *args, **kwargs):
        """Constructor."""
        super(DepositFileResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @use_kwargs(get_args)
    @pass_record
    @need_record_permission('read_permission_factory')
    def get(self, pid, record, key, version_id=None, **kwargs):
        """Get file.

        Permission required: `read_permission_factory`.

        :param pid: Pid object (from url).
        :param record: Record object resolved from the pid.
        :param key: Unique identifier for the file in the deposit.
        :param version_id: File version. Optional. If no version is provided,
            the last version is retrieved.
        :returns: the file content.
        """
        try:
            obj = record.files[str(key)].get_version(version_id=version_id)
            return self.make_response(
                obj=obj or abort(404), pid=pid, record=record)
        except KeyError:
            abort(404)

    @require_api_auth()
    @require_oauth_scopes(write_scope.id)
    @pass_record
    @need_record_permission('update_permission_factory')
    def put(self, pid, record, key):
        """Handle the file rename through the PUT deposit file.

        Permission required: `update_permission_factory`.

        :param pid: Pid object (from url).
        :param record: Record object resolved from the pid.
        :param key: Unique identifier for the file in the deposit.
        """
        try:
            data = json.loads(request.data.decode('utf-8'))
            new_key = data['filename']
        except KeyError:
            raise WrongFile()
        new_key_secure = secure_filename(new_key)
        if not new_key_secure or new_key != new_key_secure:
            raise WrongFile()
        try:
            obj = record.files.rename(str(key), new_key_secure)
        except KeyError:
            abort(404)
        try:
            record.commit()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            raise WrongFile()
        return self.make_response(obj=obj, pid=pid, record=record)

    @require_api_auth()
    @require_oauth_scopes(write_scope.id)
    @pass_record
    @need_record_permission('update_permission_factory')
    def delete(self, pid, record, key):
        """Handle DELETE deposit file.

        Permission required: `update_permission_factory`.

        :param pid: Pid object (from url).
        :param record: Record object resolved from the pid.
        :param key: Unique identifier for the file in the deposit.
        """
        try:
            del record.files[str(key)]
            record.commit()
            db.session.commit()
            return make_response('', 204)
        except KeyError:
            db.session.rollback()
            abort(404, 'The specified object does not exist or has already '
                  'been deleted.')
        except Exception as e:
            db.session.rollback()
            abort(404, 'Delete fail.')
