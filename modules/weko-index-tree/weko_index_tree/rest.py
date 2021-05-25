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

"""Blueprint for Weko index tree rest."""

import os
from datetime import date, datetime
from functools import wraps

from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request
from flask_babelex import gettext as _
from invenio_communities.models import Community
from invenio_records_rest.utils import obj_or_import_string
from invenio_rest import ContentNegotiatedMethodView

from .api import Indexes
from .errors import IndexAddedRESTError, IndexBaseRESTError, \
    IndexDeletedRESTError, IndexMovedRESTError, IndexNotFoundRESTError, \
    IndexUpdatedRESTError, InvalidDataRESTError
from .models import Index
from .utils import check_doi_in_index, check_has_any_item_in_index_is_locked


def need_record_permission(factory_name):
    """Decorator checking that the user has the required permissions on record.

    :param factory_name: name of the factory to retrieve.
    """
    def need_record_permission_builder(f):
        @wraps(f)
        def need_record_permission_decorator(self, *args,
                                             **kwargs):
            permission_factory = (getattr(self, factory_name))

            if permission_factory:
                if not permission_factory.can():
                    from flask_login import current_user
                    if not current_user.is_authenticated:
                        abort(401)
                    abort(403)

            return f(self, *args, **kwargs)
        return need_record_permission_decorator
    return need_record_permission_builder


def create_blueprint(app, endpoints):
    """Create Weko-Index-Tree-REST blueprint.

    See: :data:`weko_index_tree.config.WEKO_INDEX_TREE_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_index_tree_rest',
        __name__,
        url_prefix='',
    )

    for endpoint, options in (endpoints or {}).items():
        if 'record_serializers' in options:
            record_serializers = options.get('record_serializers')
            record_serializers = {mime: obj_or_import_string(func)
                                  for mime, func in record_serializers.items()}
        else:
            record_serializers = {}

        record_class = obj_or_import_string(
            options.get('record_class'), default=Indexes)

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
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
        )

        iar = IndexActionResource.as_view(
            IndexActionResource.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        ita = IndexTreeActionResource.as_view(
            IndexTreeActionResource.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        blueprint.add_url_rule(
            options.pop('index_route'),
            view_func=iar,
            methods=['GET', 'PUT', 'POST', 'DELETE'],
        )

        blueprint.add_url_rule(
            options.pop('tree_route'),
            view_func=ita,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.pop('item_tree_route'),
            view_func=ita,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.pop('index_move_route'),
            view_func=ita,
            methods=['PUT'],
        )
    return blueprint


class IndexActionResource(ContentNegotiatedMethodView):
    """Index create update delete view."""

    view_name = '{0}_index_action'

    def __init__(self, ctx, record_serializers=None,
                 default_media_type=None, **kwargs):
        """Constructor."""
        super(IndexActionResource, self).__init__(
            method_serializers={
                'GET': record_serializers,
                'PUT': record_serializers,
                'POST': record_serializers,
                'DELETE': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'POST': default_media_type,
                'DELETE': record_serializers,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_record_permission('read_permission_factory')
    def get(self, index_id):
        """Get a tree index record."""
        try:
            index = self.record_class.get_index_with_role(index_id)
            have_children = Index.have_children(index_id)
            index['have_children'] = have_children
            if not have_children:
                index['more_check'] = False

            return make_response(jsonify(index), 200)
        except Exception:
            raise InvalidDataRESTError()

    # @pass_record
    @need_record_permission('create_permission_factory')
    def post(self, index_id, **kwargs):
        """Create a index."""
        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()
        if not self.record_class.create(index_id, data):
            raise IndexAddedRESTError()

        status = 201
        msg = 'Index created successfully.'
        return make_response(
            jsonify({'status': status, 'message': msg}), status)

    @need_record_permission('update_permission_factory')
    def put(self, index_id, **kwargs):
        """Update a new index."""
        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()
        msg = ''
        delete_flag = False
        errors = []
        public_state = data.get('public_state') and data.get(
            'harvest_public_state')
        if public_state and data.get('public_date'):
            public_date = datetime.strptime(data['public_date'], '%Y%m%d')
            public_state = date.today() >= public_date.date()

        if not public_state and check_doi_in_index(index_id):
            status = 200
            if not data.get('public_state'):
                errors.append(_('The index cannot be kept private because '
                                'there are links from items that have a DOI.'))
            elif not data.get('harvest_public_state'):
                errors.append(_('Index harvests cannot be kept private because'
                                ' there are links from items that have a DOI.'
                                ))
            elif data.get('public_date'):
                errors.append(_(
                    'The index cannot be kept publication date to a'
                    ' future date because there are links '
                    'from items that have a DOI.'
                ))
        else:
            if data.get('thumbnail_delete_flag'):
                delete_flag = True
                filename = os.path.join(
                    current_app.instance_path,
                    current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
                    'indextree',
                    data.get('image_name').split('/')[-1])
                if os.path.isfile(filename):
                    os.remove(filename)
                data['image_name'] = ""

            if data.get('thumbnail_delete_flag') is not None:
                del data['thumbnail_delete_flag']
            if not self.record_class.update(index_id, **data):
                raise IndexUpdatedRESTError()
            status = 200
            msg = 'Index updated successfully.'

        return make_response(jsonify(
            {'status': status, 'message': msg, 'errors': errors,
             'delete_flag': delete_flag}), status)

    @need_record_permission('delete_permission_factory')
    def delete(self, index_id, **kwargs):
        """Delete a index."""
        if not index_id or index_id <= 0:
            raise IndexNotFoundRESTError()

        msg = ''
        errors = []
        if check_doi_in_index(index_id):
            errors.append(_('The index cannot be deleted because there is'
                            ' a link from an item that has a DOI.'))
        elif check_has_any_item_in_index_is_locked(index_id):
            errors.append(_('This index cannot be deleted because '
                            'the item belonging to this index is '
                            'being edited by the import function.'))
        else:
            action = request.values.get('action', 'all')
            res = self.record_class.get_self_path(index_id)
            if not res:
                raise IndexDeletedRESTError()
            if action in ('move', 'all'):
                result = self.record_class. \
                    delete_by_action(action, index_id, res.path)
                if result is None:
                    raise IndexBaseRESTError(
                        description='Could not delete data.')
            else:
                raise InvalidDataRESTError()

            msg = 'Index deleted successfully.'
        return make_response(jsonify(
            {'status': 200, 'message': msg, 'errors': errors}), 200)


class IndexTreeActionResource(ContentNegotiatedMethodView):
    """Tree get move action view."""

    view_name = '{0}_tree_action'

    def __init__(self, ctx, record_serializers=None,
                 default_media_type=None, **kwargs):
        """Constructor."""
        super(IndexTreeActionResource, self).__init__(
            method_serializers={
                'GET': record_serializers,
                'PUT': record_serializers,
                'POST': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'POST': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_record_permission('read_permission_factory')
    def get(self, **kwargs):
        """Get tree json."""
        try:
            action = request.values.get('action')
            comm_id = request.values.get('community')

            more_id_list = request.values.get('more_ids')
            more_ids = []
            if more_id_list is not None:
                more_ids = more_id_list.split('/')

            pid = kwargs.get('pid_value')

            if pid:
                if comm_id:
                    comm = Community.get(comm_id)
                    tree = self.record_class.get_contribute_tree(
                        pid, int(comm.root_node_id))
                else:
                    tree = self.record_class.get_contribute_tree(pid)
            elif action and 'browsing' in action and comm_id is None:
                if more_id_list is None:
                    tree = self.record_class.get_browsing_tree()
                else:
                    tree = self.record_class.get_more_browsing_tree(
                        more_ids=more_ids)

            elif action and 'browsing' in action and comm_id is not None:
                comm = Community.get(comm_id)

                if comm is not None:
                    if more_id_list is None:
                        tree = self.record_class.get_browsing_tree(
                            int(comm.root_node_id))
                    else:
                        tree = self.record_class.get_more_browsing_tree(
                            pid=int(comm.root_node_id), more_ids=more_ids)

            else:
                tree = self.record_class.get_index_tree()
            return make_response(jsonify(tree), 200)
        except Exception as ex:
            current_app.logger.error('IndexTree Action Exception: ', ex)
            raise InvalidDataRESTError()

    @need_record_permission('update_permission_factory')
    def put(self, index_id, **kwargs):
        """Move a index."""
        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()
        if not self.record_class.move(index_id, **data):
            raise IndexMovedRESTError()

        status = 201
        msg = 'Index moved successfully.'
        return make_response(
            jsonify({'status': status, 'message': msg}), status)
