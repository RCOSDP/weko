# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Blueprint for schema rest."""

import json, uuid, shutil
import os.path

# from copy import deepcopy
# from functools import partial

from flask import Blueprint, abort, current_app, jsonify, request, \
    url_for, redirect
from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidstore.errors import PIDInvalidAction
from invenio_pidstore import current_pidstore
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_records_rest.views import \
    create_url_rules
from invenio_records_rest.views import need_record_permission, pass_record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from webargs import fields
from webargs.flaskparser import use_kwargs
from werkzeug.utils import secure_filename
from invenio_records_rest.errors import InvalidDataRESTError, UnsupportedMediaRESTError
from invenio_files_rest.storage import PyFSFileStorage
from .schema import SchemaConverter


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
        'weko_schema_rest',
        __name__,
        url_prefix='',
    )

    create_error_handlers(blueprint)

    for endpoint, options in (endpoints or {}).items():

        if 'record_serializers' in options:
            serializers = options.get('record_serializers')
            serializers = {mime: obj_or_import_string(func)
                           for mime, func in serializers.items()}
        else:
            serializers = {}

        record_class = obj_or_import_string(options['record_class'])

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
            links_factory=obj_or_import_string(
                options.get('links_factory_imp'), default=default_links_factory
            ),
            pid_type=options.get('pid_type'),
            pid_minter=options.get('pid_minter'),
            pid_fetcher=options.get('pid_fetcher'),
            loaders={options.get('default_media_type'): lambda: request.get_json()},
            default_media_type=options.get('default_media_type'),
        )

        schema_xsd_files = SchemaFilesResource.as_view(
            SchemaFilesResource.view_name.format(endpoint),
            serializers=serializers,
            pid_type=options['pid_type'],
            ctx=ctx,
        )

        # schema_formats_edit = SchemaFormatEditResource.as_view(
        #     SchemaFormatEditResource.view_name.format(endpoint),
        #     ctx=ctx,
        # )
        #
        # blueprint.add_url_rule(
        #     options.pop('schemas_formats_route'),
        #     view_func=schema_formats_edit,
        #     methods=['POST'],
        # )

        blueprint.add_url_rule(
            options.pop('schemas_route'),
            view_func=schema_xsd_files,
            methods=['POST'],
        )

        blueprint.add_url_rule(
            options.pop('schema_route'),
            view_func=schema_xsd_files,
            methods=['POST'],
        )

        blueprint.add_url_rule(
            options.pop('schemas_put_route'),
            view_func=schema_xsd_files,
            methods=['PUT'],
        )

        # blueprint.add_url_rule(
        #     options.pop('schema_del_route'),
        #     view_func=schema_xsd_files,
        #     methods=['DELETE'],
        # )

    return blueprint


class SchemaFilesResource(ContentNegotiatedMethodView):
    """Schema files resource."""

    view_name = '{0}_files'

    def __init__(self, serializers, pid_type, ctx, *args, **kwargs):
        """Constructor."""
        super(SchemaFilesResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

        self.pid_minter = current_pidstore.minters[self.pid_minter]
        self.pid_fetcher = current_pidstore.minters[self.pid_fetcher]
        self.xsd_location_folder = current_app.config['WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER'].\
            format(current_app.instance_path)


    # @pass_record
    # @need_record_permission('read_permission_factory')
    def get(self, pid, record):
        pass

    # @need_record_permission('create_permission_factory')
    def post(self, **kwargs):
        """Create a uuid and return a links dict.
        file upload step is below
        ①create a uuuid
        :returns: Json Response have a links dict.
        """

        if request.mimetype not in self.loaders:
            raise UnsupportedMediaRESTError(request.mimetype)

        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()

        pid = request.view_args.get('pid_value')
        # the second post
        if pid:
            furl = self.xsd_location_folder + "tmp/" + pid + "/"
            dst = self.xsd_location_folder + pid + "/"
            data.pop('$schema')
            sn = data.get('name')

            if not os.path.exists(furl):
                return jsonify({'status': 'Please upload file first.'})

            fn = data.get('file_name')
            fn = furl + (fn if "." in fn else fn + ".xsd")

            xsd = SchemaConverter(fn, data.get('root_name'))
            try:
                self.record_class.create(pid, sn+"_mapping", data, xsd.to_dict(), data.get('xsd_file'),
                                         xsd.namespaces)
                db.session.commit()
            except:
                abort(400, 'Schema of the same name already exists.')

            #set the schema to be vaild
            # for k, v in current_app.config["RECORDS_UI_EXPORT_FORMATS"].items():
            #     if isinstance(v, dict):
            #         for k1, v1 in v.items():
            #             if isinstance(v1, dict):
            #                 v1 = v1.copy()
            #                 v1["title"] = sn.upper()
            #                 v1["order"] = len(v)
            #                 v.update({sn: v1})
            #                 break

            # update oai metadata formats
            oad = current_app.config.get('OAISERVER_METADATA_FORMATS', {})
            sel = list(oad.values())[0].get('serializer')
            scm = dict()
            if isinstance(xsd.namespaces, dict):
                ns = xsd.namespaces.get('') or xsd.namespaces.get(sn)
            scm.update({'namespace': ns})
            scm.update({'schema': data.get('xsd_file')})
            scm.update({'serializer': (sel[0], {'schema_type': sn})})
            oad.update({sn: scm})

            # move out those files from tmp folder
            shutil.move(furl, dst)

            return jsonify({'status': 'uploaded successfully.'})
        else:
            # the first post

            # Create uuid for record
            record_uuid = uuid.uuid4()
            # Create persistent identifier
            pid = self.pid_minter(record_uuid, data=data)

            db.session.commit()
            url = request.base_url + str(pid.object_uuid)
            links = dict(self=url)
            links['bucket'] = request.base_url + "put/" + str(pid.object_uuid)

            response = current_app.response_class(json.dumps({"links": links}), mimetype=request.mimetype)
            response.status_code = 201
            return response

    # @need_record_permission('create_permission_factory')
    def put(self, **kwargs):
        """Create a uuid and return a links dict.
        file upload step is below
        ② upload file to server
        :returns: Json Response have a links dict.
        """
        fn = request.view_args['key']

        # if ".xsd" not in fn:
        #     abort(405, "Xsd File only !!")

        pid = request.view_args['pid_value']
        furl = self.xsd_location_folder + "tmp/" + pid + "/" + fn
        # size = len(request.data)

        try:
            fs = PyFSFileStorage(furl)
            fileurl, bytes_written, checksum = fs.save(request.stream)
        except Exception:
            raise InvalidDataRESTError()
        else:
            pass

        jd = {"key": fn, "mimetype": request.mimetype, "links": {},
              "size": bytes_written}
        data = dict(key=fn, mimetype='text/plain')
        response = current_app.response_class(json.dumps(jd),
                                              mimetype='application/json')
        response.status_code = 200
        return response


class SchemaFormatEditResource(ContentNegotiatedMethodView):
    """
    Edit metadata formats for OAI ListMetadataFormats
    """
    view_name = '{0}_formats_edit'

    def __init__(self, ctx, *args, **kwargs):
        """Constructor."""
        super(SchemaFormatEditResource, self).__init__(
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    def post(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        if request.mimetype not in self.loaders:
            raise UnsupportedMediaRESTError(request.mimetype)

        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()
