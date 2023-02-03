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

import json
import os.path
import shutil
import uuid
import zipfile

from flask import Blueprint, abort, current_app, jsonify, request
from invenio_db import db
from invenio_files_rest.storage import PyFSFileStorage
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records_rest.errors import InvalidDataRESTError, \
    UnsupportedMediaRESTError
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler

from .schema import SchemaConverter, get_oai_metadata_formats

# from copy import deepcopy
# from functools import partial


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
    
    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_schema_ui dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

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
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
            default_media_type=options.get('default_media_type'),
        )

        schema_xsd_files = SchemaFilesResource.as_view(
            SchemaFilesResource.view_name.format(endpoint),
            serializers=serializers,
            pid_type=options['pid_type'],
            ctx=ctx,
        )

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
        self.xsd_location_folder = current_app.config[
            'WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER']. \
            format(current_app.instance_path)

    # @pass_record
    # @need_record_permission('read_permission_factory')
    def get(self, pid, record):
        """Get Method."""
        pass

    # @need_record_permission('create_permission_factory')
    def post(self, **kwargs):
        """Create a uuid and return a links dict. file upload step is below create a uuuid.

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
            # furl = self.xsd_location_folder + 'tmp/' + pid + '/'
            furl = os.path.join(self.xsd_location_folder, 'tmp', pid)
            # dst = self.xsd_location_folder + pid + '/'
            dst = os.path.join(self.xsd_location_folder, pid)
            data.pop('$schema')
            sn = data.get('name') if 'name' in data else None
            root_name = data.get('root_name') if 'root_name' in data else None
            if root_name is None or len(root_name) == 0:
                abort(400, 'Root Name is empty.')
            if sn is None or len(sn) == 0:
                sn = root_name
            if not sn.endswith('_mapping'):
                sn = sn + '_mapping'

            if not os.path.exists(furl):
                abort(400, 'Please upload file first')
            if not data.get('file_name'):
                abort(400, 'File Name is empty.')

            fn = data.get('file_name')
            zip_file = data.get('zip_name') if 'zip_name' in data else None
            fn = os.path.join(furl, (fn if '.' in fn else fn + '.xsd'))

            # if zip file unzip first
            if zip_file is not None and zip_file.endswith('.zip'):
                with zipfile.ZipFile(os.path.join(furl, zip_file)) as fp:
                    fp.extractall(furl)

            xsd = SchemaConverter(fn, root_name)
            try:
                self.record_class.create(pid, sn.lower(), data,
                                         xsd.to_dict(), data.get('xsd_file'),
                                         xsd.namespaces,
                                         target_namespace=xsd.target_namespace)
                db.session.commit()
            except BaseException:
                abort(400, 'Schema of the same name already exists.')

            # update oai metadata formats
            oad = get_oai_metadata_formats(current_app)
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

            return jsonify({'message': 'uploaded successfully.'})
        else:
            # the first post

            # Create uuid for record
            record_uuid = uuid.uuid4()
            # Create persistent identifier
            pid = self.pid_minter(record_uuid, data=data)

            db.session.commit()
            url = request.base_url + str(pid.object_uuid)
            links = dict(self=url)
            links['bucket'] = request.base_url + 'put/' + str(pid.object_uuid)

            response = current_app.response_class(json.dumps({'links': links}),
                                                  mimetype=request.mimetype)
            response.status_code = 201
            return response

    # @need_record_permission('create_permission_factory')
    def put(self, **kwargs):
        """Create a uuid and return a links dict. file upload step is below upload file to server.

        :returns: Json Response have a links dict.

        """
        fn = request.view_args['key']

        # if ".xsd" not in fn:
        #     abort(405, "Xsd File only !!")

        pid = request.view_args['pid_value']
        furl = self.xsd_location_folder + 'tmp/' + pid + '/' + fn
        # size = len(request.data)

        try:
            fs = PyFSFileStorage(furl)
            fileurl, bytes_written, checksum = fs.save(request.stream)
        except Exception:
            raise InvalidDataRESTError()
        else:
            pass

        jd = {'key': fn, 'mimetype': request.mimetype, 'links': {},
              'size': bytes_written}
        data = dict(key=fn, mimetype='text/plain')
        response = current_app.response_class(json.dumps(jd),
                                              mimetype='application/json')
        response.status_code = 200
        return response
