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
from functools import wraps
from wsgiref.util import request_uri

from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_rest.utils import obj_or_import_string
from invenio_rest import ContentNegotiatedMethodView
from invenio_db import db

from weko_admin.models import AdminLangSettings

from .api import Indexes
from .errors import IndexAddedRESTError, IndexNotFoundRESTError, \
    IndexUpdatedRESTError, InvalidDataRESTError
from .models import Index
from .utils import check_doi_in_index, check_index_permissions, \
    is_index_locked, perform_delete_index, save_index_trees_to_redis


def need_record_permission(factory_name):
    """Decorator checking that the user has the required permissions on record.

    :param factory_name: name of the factory to retrieve.
    """
    def need_record_permission_builder(f):
        @wraps(f)
        def need_record_permission_decorator(self, *args,
                                             **kwargs):
            permission_factory = (getattr(self, factory_name))

            if permission_factory is not None:
                if not permission_factory.can():
                    index_id = kwargs.get('index_id')
                    if index_id and factory_name == 'read_permission_factory':
                        if not check_index_permissions(index_id=index_id):
                            abort(403)
                    else:
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
    
    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_index_tree dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

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
            if str(index_id) != '0':
                index = self.record_class.get_index_with_role(index_id)
                have_children = Index.have_children(index_id)
                index['have_children'] = have_children
                if not have_children:
                    index['more_check'] = False
            else:
                index = {}

            can_edit = False
            role_ids = []
            if current_user and current_user.is_authenticated:
                for role in current_user.roles:
                    if role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']:
                        role_ids = []
                        can_edit = True
                        break
                    else:
                        role_ids.append(role.id)
            if not can_edit and role_ids and str(index_id) != '0':
                from invenio_communities.models import Community
                indexes = [i.id for i in Indexes.get_all_parent_indexes(index_id)]
                comm_data = Community.query.filter(
                    Community.root_node_id.in_(indexes),
                    Community.id_role.in_(role_ids)
                ).all()
                if comm_data:
                    can_edit = True
            index["can_edit"] = can_edit

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
        errors = []
        msg = ''
        status = 200
        if is_index_locked(index_id):
            errors.append(_('Index Delete is in progress on another device.'))
        else:
            if not self.record_class.create(index_id, data):
                raise IndexAddedRESTError()
            status = 201
            msg = 'Index created successfully.'

            langs = AdminLangSettings.get_registered_language()
            if "ja" in [lang["lang_code"] for lang in langs]:
                tree_ja = self.record_class.get_index_tree(lang="ja")
            tree = self.record_class.get_index_tree(lang="other_lang")
            
            for lang in langs:
                lang_code = lang["lang_code"]
                if lang_code == "ja":
                    save_index_trees_to_redis(tree_ja, lang=lang_code)
                else:
                    save_index_trees_to_redis(tree, lang=lang_code)
                
        return make_response(
            jsonify({'status': status, 'message': msg, 'errors': errors}),
            status)

    @need_record_permission('update_permission_factory')
    def put(self, index_id, **kwargs):
        """Update a new index."""
        from weko_search_ui.tasks import is_import_running

        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()
        msg = ''
        delete_flag = False
        errors = []
        status = 200
        check = is_import_running()
        
        if check == "is_import_running":
            errors.append(_('The index cannot be updated becase '
                            'import is in progress.'))
        else:
            public_state = data.get('public_state') and data.get(
                'harvest_public_state')
            
            if is_index_locked(index_id):
                errors.append(_('Index Delete is in progress on another device.'))
            elif not public_state and check_doi_in_index(index_id):
                if not data.get('public_state'):
                    errors.append(_('The index cannot be kept private because '
                                    'there are links from items that have a DOI.'))
                elif not data.get('harvest_public_state'):
                    errors.append(_('Index harvests cannot be kept private because'
                                    ' there are links from items that have a DOI.'
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
                msg = 'Index updated successfully.'

            
            #roles = get_account_role()
            #for role in roles:
            langs = AdminLangSettings.get_registered_language()
            if "ja" in [lang["lang_code"] for lang in langs]:
                tree_ja = self.record_class.get_index_tree(lang="ja")
            tree = self.record_class.get_index_tree(lang="other_lang")
            for lang in langs:
                lang_code = lang["lang_code"]
                if lang_code == "ja":
                    save_index_trees_to_redis(tree_ja, lang=lang_code)
                else:
                    save_index_trees_to_redis(tree, lang=lang_code)

        return make_response(jsonify(
            {'status': status, 'message': msg, 'errors': errors,
             'delete_flag': delete_flag}), status)

    @need_record_permission('delete_permission_factory')
    def delete(self, index_id, **kwargs):
        """Delete a index."""
        from weko_search_ui.tasks import is_import_running

        errors = []
        msg = ''
        if not index_id or index_id <= 0:
            raise IndexNotFoundRESTError()

        check = is_import_running()
        if check == "is_import_running":
            errors.append(_('The index cannot be deleted becase '
                            'import is in progress.'))
        else:
            action = request.values.get('action', 'all')
            msg, errors = perform_delete_index(index_id, self.record_class, action)

        langs = AdminLangSettings.get_registered_language()
        if "ja" in [lang["lang_code"] for lang in langs]:
            tree_ja = self.record_class.get_index_tree(lang="ja")
        tree = self.record_class.get_index_tree(lang="other_lang")
        for lang in langs:
            lang_code = lang["lang_code"]
            if lang_code == "ja":
                save_index_trees_to_redis(tree_ja, lang=lang_code)
            else:
                save_index_trees_to_redis(tree, lang=lang_code)

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

    def get(self, **kwargs):
        """Get tree json."""
        def _check_edit_permission(is_admin, tree, can_edit_indexes):
            if is_admin:
                for i in tree:
                    i['settings']['can_edit'] = True
                    if len(i['children']) > 0:
                        _check_edit_permission(is_admin, i['children'], can_edit_indexes)
            else:
                for i in tree:
                    i['settings']['can_edit'] = False
                    if str(i['id']) in can_edit_indexes:
                        i['settings']['can_edit'] = True
                    elif str(i['id']) not in can_edit_indexes and \
                            'settings' in i and i['settings'].get('checked', False):
                        i['settings']['checked'] = False
                    if len(i['children']) > 0:
                        _check_edit_permission(is_admin, i['children'], can_edit_indexes)

        from invenio_communities.models import Community
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
                    tree = []
            else:
                tree = []
                role_ids = []
                if current_user and current_user.is_authenticated:
                    for role in current_user.roles:
                        if role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']:
                            role_ids = []
                            tree = self.record_class.get_index_tree()
                            break
                        else:
                            role_ids.append(role.id)
                if role_ids:
                    from invenio_communities.models import Community
                    comm_list = Community.query.filter(
                        Community.id_role.in_(role_ids)
                    ).all()
                    check_list = []
                    for comm in comm_list:
                        indexes = [
                            i.id for i in Indexes.get_all_parent_indexes(comm.root_node_id)
                            if i.parent == 0
                        ]
                        for index_id in indexes:
                            if index_id not in check_list:
                                tree += self.record_class.get_index_tree(index_id)
                                check_list.append(index_id)
            return make_response(jsonify(tree), 200)
        except Exception as ex:
            current_app.logger.error('IndexTree Action Exception: ', ex)
            raise InvalidDataRESTError()

    @need_record_permission('update_permission_factory')
    def put(self, index_id, **kwargs):
        """Move a index."""
        from weko_search_ui.tasks import is_import_running

        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()

        msg = ''
        status = 200
        check = is_import_running()
        if check == "is_import_running":
            status = 202
            msg = _('The index cannot be moved becase '
                    'import is in progress.')
        else:
            # Moving
            moved = self.record_class.move(index_id, **data)
            if not moved or not moved.get('is_ok'):
                status = 202
                msg = moved.get('msg')
            else:
                status = 201
                msg = _('Index moved successfully.')
            langs = AdminLangSettings.get_registered_language()
            if "ja" in [lang["lang_code"] for lang in langs]:
                    tree_ja = self.record_class.get_index_tree(lang="ja")
            tree = self.record_class.get_index_tree(lang="other_lang")
            for lang in langs:
                lang_code = lang["lang_code"]
                if lang_code == "ja":
                        save_index_trees_to_redis(tree_ja, lang=lang_code)
                else:
                    save_index_trees_to_redis(tree, lang=lang_code)
        return make_response(
            jsonify({'status': status, 'message': msg}), status)
