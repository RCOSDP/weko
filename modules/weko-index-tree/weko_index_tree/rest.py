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
import inspect
import json
import time
import traceback
from functools import wraps
from datetime import date, datetime, timezone, timedelta

from flask import (
    Blueprint, abort, current_app, jsonify, make_response,
    request, Response
)
from flask_babelex import gettext as _
from flask_babelex import get_locale as get_current_locale
from flask_login import current_user
from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest
from werkzeug.http import generate_etag

from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_records_rest.utils import obj_or_import_string
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.errors import SameContentException, RESTException

from weko_accounts.utils import limiter, roles_required
from weko_admin.config import (
    WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
    WEKO_ADMIN_PERMISSION_ROLE_REPO,
    WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY,
)
from weko_admin.models import AdminLangSettings

from .api import Indexes
from .errors import (
    IndexAddedRESTError, IndexBaseRESTError, IndexDeletedRESTError, IndexNotFoundRESTError, IndexUpdatedRESTError,
    InvalidDataRESTError, VersionNotFoundRESTError, InternalServerError,
    PermissionError, IndexNotFound404Error
)
from .models import Index
from .scopes import (
    create_index_scope, read_index_scope, update_index_scope, delete_index_scope
)
from .utils import (
    check_doi_in_index, check_index_permissions, can_admin_access_index,
    is_index_locked, perform_delete_index, save_index_trees_to_redis, reset_tree
)
from .schema import IndexCreateRequestSchema, IndexUpdateRequestSchema

JST = timezone(timedelta(hours=+9), 'JST')

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

        itg = GetIndex.as_view(
            GetIndex.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        itp = GetParentIndex.as_view(
            GetParentIndex.view_name.format(endpoint),
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

        ima = IndexManagementAPI.as_view(
            f"{IndexManagementAPI.view_name}_{endpoint}",
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )


        blueprint.add_url_rule(
            options.get('index_route'),
            view_func=iar,
            methods=['GET', 'PUT', 'POST', 'DELETE'],
        )

        blueprint.add_url_rule(
            options.get('get_index_tree'),
            view_func=itg,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('api_get_all_index_jp_en'),
            view_func=ima,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('api_get_index_tree'),
            view_func=ima,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('api_create_index'),
            view_func=ima,
            methods=['POST'],
        )

        blueprint.add_url_rule(
            options.get('api_update_index'),
            view_func=ima,
            methods=['PUT'],
        )

        blueprint.add_url_rule(
            options.get('api_delete_index'),
            view_func=ima,
            methods=['DELETE'],
        )

        blueprint.add_url_rule(
            options.get('get_index_root_tree'),
            view_func=itg,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('get_parent_index_tree'),
            view_func=itp,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('tree_route'),
            view_func=ita,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('item_tree_route'),
            view_func=ita,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('index_move_route'),
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
                    or_(
                        Community.group_id.in_(role_ids),
                        Community.id_role.in_(role_ids)
                    )
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

        def _is_decendent(index_node_id, possible_ancestor_ids):
            """Check if the index_node_id is a descendant of any node in possible_ancestor_ids.
            Args:
                index_node_id (int): The ID of the index node to check.
                possible_ancestor_ids (list): A list of possible ancestor node IDs.
            Returns:
                bool: True if index_node_id is a descendant of any node in possible_ancestor_ids, False otherwise.
            """
            target_node = self.record_class.get_index(index_node_id)
            parent_node_id = target_node.parent
            while parent_node_id is not None and parent_node_id != 0:
                # If the parent node is one of possible ancestors, return True
                if parent_node_id in possible_ancestor_ids:
                    return True
                # Move to the next parent node
                target_node = self.record_class.get_index(parent_node_id)
                if target_node is None:
                    break
                parent_node_id = target_node.parent
            return False

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
                if pid == "item_registration":
                    tree = self.record_class.get_browsing_tree()
                elif comm_id:
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
                    communities = Community.get_by_user(
                        role_ids, with_deleted=True
                    ).all()
                    top_community_nodes = []
                    if len (communities) < 2:
                        top_community_nodes = communities
                    else:
                        for community in communities:
                            possible_ancestor_ids = [
                                c.root_node_id for c in communities
                                if c.id != community.id
                            ]
                            if not _is_decendent(
                                community.root_node_id, possible_ancestor_ids
                            ):
                                top_community_nodes.append(community)
                    
                    check_list = []
                    for comm in top_community_nodes:
                        top_index_node_ids = [comm.root_node_id]
                        for index_id in top_index_node_ids:
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


class GetIndex(ContentNegotiatedMethodView):
    """Get Index Tree API."""

    view_name = '{0}_get_index_tree'

    def __init__(self, ctx, record_serializers=None, default_media_type=None, **kwargs):
        """Constructor."""
        super(GetIndex, self).__init__(
            method_serializers={
                'GET': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(read_index_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get tree json."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        try:
            pid = kwargs.get('index_id')

            # Get update time
            if pid and pid != 0:
                index = self.record_class.get_index(pid)
                if not index:
                    raise IndexNotFound404Error()
                updated = index.updated
            else:
                all_indexes = self.record_class.get_all_indexes()
                all_indexes = sorted(all_indexes, key=lambda x: x.updated, reverse=True)
                updated = all_indexes[0].updated if len(all_indexes) > 0 else datetime.now()

            # Check Etag
            hash_str = str(pid) + updated.strftime("%a, %d %b %Y %H:%M:%S GMT")
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check Last-Modified
            if not request.if_none_match:
                self.check_if_modified_since(dt=updated)

            # Language setting
            language = request.headers.get('Accept-Language')
            if language == 'ja':
                get_current_locale().language = language

            # Get index tree
            if pid and pid != 0:
                tree = self.record_class.get_index_tree(pid)
                reset_tree(tree=tree)
                if len(tree) == 0:
                    raise PermissionError()
                result_tree = dict(
                    index=tree[0]
                )
            else:
                tree = self.record_class.get_index_tree(pid=0)
                reset_tree(tree=tree)
                result_tree = dict(
                    index=dict(
                        children=tree,
                        cid=0,
                        name='Root-index',
                        id='0',
                        public_state=True,
                        value='Root-index'
                    )
                )

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            # Create Response
            res = Response(
                response=json.dumps(result_tree, indent=indent),
                status=200,
                content_type='application/json')
            res.set_etag(etag)
            res.last_modified = updated
            return res

        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()


class GetParentIndex(ContentNegotiatedMethodView):
    """Get Parent Index Tree API."""

    view_name = '{0}_get_parent_index_tree'

    def __init__(self, ctx, record_serializers=None, default_media_type=None, **kwargs):
        """Constructor."""
        super(GetParentIndex, self).__init__(
            method_serializers={
                'GET': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    def getParents(self, pid):
        parents = []
        index = self.record_class.get_index(pid)
        parents.append(index)
        if index.parent and index.parent != 0:
            parents = parents + self.getParents(index.parent)
        return parents

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(read_index_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get tree json."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        try:
            pid = kwargs.get('index_id')

            index = self.record_class.get_index(pid)
            if not index:
                raise IndexNotFound404Error()

            # Get update time
            updated = index.updated

            # Check Etag
            hash_str = str(pid) + updated.strftime("%a, %d %b %Y %H:%M:%S GMT")
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check Last-Modified
            if not request.if_none_match:
                self.check_if_modified_since(dt=updated)

            # Language setting
            language = request.headers.get('Accept-Language')
            if language == 'ja':
                get_current_locale().language = language

            # Get index tree
            tree = self.record_class.get_index_tree(pid=0)
            reset_tree(tree=tree)

            # Get parent
            parents = self.getParents(pid)

            # Get index from tree
            parent_nodes = []
            for parent in reversed(parents):
                child = next(iter(filter(lambda child: child['cid'] == parent.id, tree)), None)
                if child is None:
                    raise PermissionError()
                parent_nodes.append(child)
                tree = child.pop('children')

            # Connect parent node
            parent_tree = None
            current_parent = None
            for parent in reversed(parent_nodes):
                if parent_tree is None:
                    parent_tree = parent
                else:
                    current_parent['parent'] = parent
                current_parent = parent
            result_tree = dict(
                index=parent_tree
            )

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            # Setting Response
            res = Response(
                response=json.dumps(result_tree, indent=indent),
                status=200,
                content_type='application/json')
            res.set_etag(etag)
            res.last_modified = updated
            return res

        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()


class IndexManagementAPI(ContentNegotiatedMethodView):
    """Get Index Tree API.

        WEKO_INDEX_TREE_REST_ENDPOINTS = dict(
            tid=dict(
                record_class='weko_index_tree.api:Indexes',
                api_get_all_index_jp_en='/<string:version>/tree',
                api_get_index_tree='/<string:version>/tree/<int:index_id>',
                api_create_index='/<string:version>/tree/index',
                api_update_index='/<string:version>/tree/index/<int:index_id>',
                api_delete_index='/<string:version>/tree/index/<int:index_id>',
            )
        )

    """

    view_name = '{0}_index_management_api'

    def __init__(self, ctx, record_serializers=None, default_media_type=None, **kwargs):
        """Constructor."""
        super(IndexManagementAPI, self).__init__(
            method_serializers={
                'GET': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(read_index_scope.id)
    @roles_required([], allow_anonymous=True)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get index tree."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    @require_api_auth(allow_anonymous=False)
    @roles_required([
        WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
        WEKO_ADMIN_PERMISSION_ROLE_REPO,
        WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY
    ])
    @require_oauth_scopes(create_index_scope.id)
    @limiter.limit('')
    def post(self, **kwargs):
        """Create a new index tree node."""
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    @require_api_auth(allow_anonymous=False)
    @roles_required([
        WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
        WEKO_ADMIN_PERMISSION_ROLE_REPO,
        WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY
    ])
    @require_oauth_scopes(update_index_scope.id)
    @limiter.limit('')
    def put(self, **kwargs):
        """Update an existing index tree node."""
        current_app.logger.info("Updating an existing index tree node")
        version = kwargs.get('version')
        func_name = f'put_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    @require_api_auth(allow_anonymous=False)
    @roles_required([
        WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,
        WEKO_ADMIN_PERMISSION_ROLE_REPO,
        WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY
    ])
    @require_oauth_scopes(delete_index_scope.id)
    @limiter.limit('')
    def delete(self, **kwargs):
        """Delete an existing index tree node."""
        version = kwargs.get('version')
        func_name = f'delete_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()


    def get_v1(self, **kwargs):
        """Get index tree."""

        def json_serialize(obj):
            """Serialize object to JSON.

            Args:
                obj: The object to serialize.

            Returns:
                str: The serialized JSON string.
            """
            if isinstance(obj, (datetime, date)):
                return obj.strftime("%Y%m%d")
            else:
                return str(obj)

        try:
            pid = kwargs.get('index_id')

            # Get update time
            if pid and pid != 0:
                index = self.record_class.get_index(pid)
                if not index:
                    raise IndexNotFound404Error()
                updated = index.updated
            else:
                all_indexes = self.record_class.get_all_indexes()
                current_app.logger.info(all_indexes)
                all_indexes = sorted(all_indexes, key=lambda x: x.updated, reverse=True)
                updated = all_indexes[0].updated if len(all_indexes) > 0 else datetime.now()

            # Check Etag
            hash_str = str(pid) + updated.strftime("%a, %d %b %Y %H:%M:%S GMT")
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check Last-Modified
            if not request.if_none_match:
                self.check_if_modified_since(dt=updated)

            # Get index tree
            if pid and pid != 0:
                tree = self.record_class.get_index_tree(pid, lang="ja")
                reset_tree(tree=tree)
                if len(tree) == 0:
                    raise PermissionError()
                result_tree_ja = dict(
                    index=tree[0]
                )

                tree = self.record_class.get_index_tree(pid, lang="en")
                reset_tree(tree=tree)
                result_tree_en = dict(
                    index=tree[0]
                )
            else:
                tree = self.record_class.get_index_tree(pid=0, lang="ja")
                current_app.logger.error(tree)

                reset_tree(tree=tree)
                current_app.logger.error(tree)
                result_tree_ja = dict(
                    index=dict(
                        children=tree,
                        cid=0,
                        name='Root-index',
                        id='0',
                        public_state=True,
                        value='Root-index'
                    )
                )

                tree = self.record_class.get_index_tree(pid=0, lang="en")
                reset_tree(tree=tree)
                result_tree_en = dict(
                    index=dict(
                        children=tree,
                        cid=0,
                        name='Root-index',
                        id='0',
                        public_state=True,
                        value='Root-index'
                    )
                )

            merged_tree = self.merge_index_trees(result_tree_ja, result_tree_en)

            indent = 4 if request.args.get('pretty') == 'true' else None

            res = Response(
                response=json.dumps(merged_tree, indent=indent, default=json_serialize),
                status=200,
                content_type='application/json'
            )
            res.set_etag(etag)
            res.last_modified = updated
            return res

        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()

    def merge_index_trees(self, tree_ja, tree_en):
        """Merge Japanese and English index trees."""
        def merge_nodes(node_ja, node_en):
            merged_node = node_ja.copy()
            merged_node.update({
                "index_name": merged_node.get("value", ""),
                "index_name_english": node_en.get("value", ""),
                "index_link_name_english": node_en.get("index_link_name", ""),
                "value_english": node_en.get("value", ""),
            })

            # Merge children recursively
            children_ja = {child["cid"]: child for child in node_ja.get("children", [])}
            children_en = {child["cid"]: child for child in node_en.get("children", [])}
            merged_children = []
            for cid in set(children_ja.keys()).union(children_en.keys()):
                merged_children.append(merge_nodes(children_ja.get(cid), children_en.get(cid)))
            merged_node["children"] = merged_children

            return merged_node

        return {"index": merge_nodes(tree_ja["index"], tree_en["index"])}

    def post_v1(self, **kwargs):
        """Create a new index tree node.

        API endpoint to create a new index tree node. <br>
        Payload should be in JSON format and include the following fields: <br>
            - index: Dictionary containing the index information.
        """
        request_data = self.validate_request(request, IndexCreateRequestSchema)

        index_info = request_data.get("index")
        parent_id = index_info.get("parent")
        self.check_index_accessible(parent_id)

        # Create new index
        index_id = int(time.time() * 1000)
        indexes = {
            "id": index_id,
            "value": "New Index",
        }
        try:
            create_result = self.record_class.create(
                pid=parent_id, indexes=indexes
            )

            if not create_result:
                current_app.logger.error(f"Failed to create index: {index_id}")
                raise InternalServerError(
                    description=f"Internal Server Error: Failed to create index."
                )

            current_app.logger.info(f"Create new index: {index_id}")

        except SQLAlchemyError as ex:
            db.session.rollback()
            current_app.logger.error(
                f"Error occurred in DB while creating index: {ex}"
            )
            traceback.print_exc()
            raise InternalServerError(
                description=f"Internal Server Error: Failed to create index."
            ) from ex

        # Update new index with provided data
        try:
            new_index = self.record_class.get_index(index_id)

            index_data = {
                **index_info,
                **self._get_allowed_group_roles(index_info)
            }

            updated_index = self.record_class.update(index_id, **index_data)

            if not updated_index:
                current_app.logger.error(
                    f"Failed to update new index: {index_id}. Delete it."
                )
                raise InternalServerError(
                    description=f"Internal Server Error: Failed to update new index {index_id}."
                )

            current_app.logger.info(f"Update info new index: {index_id}")

        except InternalServerError:
            db.session.delete(new_index)
            db.session.commit()
            raise

        except SQLAlchemyError as ex:
            db.session.rollback()
            db.session.delete(new_index)
            db.session.commit()
            current_app.logger.error(
                f"Failed to update new index: {index_id}. Database error. "
                "Delete it."
            )
            traceback.print_exc()
            raise InternalServerError(
                description=f"Database Error: Failed to create index."
            ) from ex

        except Exception as ex:
            db.session.rollback()
            db.session.delete(new_index)
            db.session.commit()
            current_app.logger.error(
                f"Failed to update new index: {index_id}. Unexpected error. "
                "Delete it."
            )
            traceback.print_exc()
            raise InternalServerError(
                description=f"Internal Server Error: Failed to create index."
            ) from ex

        # Update index tree in Redis all languages
        self.save_redis()

        response_data = {
            "index": {
                **{
                    column.name: getattr(updated_index, column.name)
                    for column in updated_index.__table__.columns
                },
                "created": updated_index.created.isoformat(),
                "updated": updated_index.updated.isoformat(),
                **{
                    "public_date": updated_index.public_date.strftime("%Y%m%d")
                    if updated_index.public_date
                    else {}
                },
            }
        }

        return make_response(jsonify(response_data), 201)


    def put_v1(self, index_id, **kwargs):
        """ Update an existing index tree node.

        API endpoint to update an existing index tree node. <br>
        Payload should be in JSON format and include the following fields: <br>
            - index: Dictionary containing the index information.

        Args:
            index_id (int): The ID of the index to be updated.
        """
        if index_id == 0:
            current_app.logger.error("Bad Request: Cannot update root index.")
            raise IndexBaseRESTError(
                description="Bad Request: Cannot update root index."
            )
        self.check_index_accessible(index_id)

        request_data = self.validate_request(request, IndexUpdateRequestSchema)

        index_info = request_data.get("index")
        parent_id = index_info.get("parent")
        self.check_index_accessible(parent_id)

        try:
            index_data = {
                **index_info,
                **self._get_allowed_group_roles(index_info)
            }

            index = self.record_class.get_index(index_id)
            parent = parent_id if parent_id is not None else index.parent
            position = (
                index_data.get("position")
                if index_data.get("position") is not None else index.position
            )

            if parent != index.parent or position != index.position:
                # Move index if parent or position changed
                # Change int to string if parent is root node
                arg_parent = parent if parent > 0 else "0"
                arg_pre_parent = index.parent if index.parent > 0 else "0"
                moved = self.record_class.move(
                    index_id, pre_parent=arg_pre_parent,
                    parent=arg_parent, position=position
                )
                index_data.pop("parent", None)
                if not moved or not moved.get("is_ok"):
                    msg = moved.get("msg")
                    current_app.logger.error(
                        f"Failed to move index {index_id}: {msg}."
                    )
                    raise IndexUpdatedRESTError(
                        description=f"Failed to move index {index_id}: {msg}"
                    )

            updated_index = self.record_class.update(index_id, **index_data)

            if not updated_index:
                msg = f"Failed to update index {index_id}."
                current_app.logger.error(msg)
                raise InternalServerError(
                    description=f"Internal Server Error: {msg}"
                )

            current_app.logger.info(f"Update index: {index_id}")

        except SQLAlchemyError as ex:
            db.session.rollback()
            current_app.logger.error(
                f"Failed to update index: {index_id}. Database error.")
            traceback.print_exc()
            raise InternalServerError(
                description=f"Database Error: Failed to update index {index_id}."
            ) from ex
        except IndexUpdatedRESTError as ex:
            db.session.rollback()
            current_app.logger.error(
                f"Failed to update index: {index_id}. Index updated error.")
            traceback.print_exc()
            raise
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                f"Failed to update index: {index_id}. Unexpected error.")
            traceback.print_exc()
            raise InternalServerError(
                description=f"Internal Server Error: Failed to update index {index_id}."
            ) from ex

        # Update index tree in Redis all languages
        self.save_redis()

        response_data = {
            "index": {
                **{
                    column.name: getattr(updated_index, column.name)
                    for column in updated_index.__table__.columns
                },
                "created": updated_index.created.isoformat(),
                "updated": updated_index.updated.isoformat(),
                **{
                    "public_date": updated_index.public_date.strftime("%Y%m%d")
                    if updated_index.public_date
                    else {}
                },
            }
        }

        return make_response(jsonify(response_data), 200)


    def delete_v1(self, index_id, **kwargs):
        """Delete an existing index tree node.

        Args:
            index_id (int): The ID of the index to be deleted.
        """
        if index_id == 0:
            current_app.logger.error("Bad Request: Cannot update root index.")
            raise IndexBaseRESTError(
                description="Bad Request: Cannot update root index."
            )
        self.check_index_accessible(index_id)

        try:
            from weko_search_ui.tasks import is_import_running
            check = is_import_running()
            if check == "is_import_running":
                current_app.logger.error(
                    f"Failed to delete index: {index_id}. Import is in progress."
                )
                raise IndexBaseRESTError(
                    description="Bad Request: Failed to delete index. "
                                "Import is in progress."
                )

            msg, errors = perform_delete_index(index_id, self.record_class, "all")
            if errors:
                current_app.logger.error(
                    f"Failed to delete index: {index_id}. Errors: {errors}"
                )
                raise IndexBaseRESTError(
                    description=f"Failed to delete index: {errors}"
                )
            if "Failed" in msg:
                raise InternalServerError(description=f"Unexpected Error: {msg}")

            self.save_redis()

        except RESTException as ex:
            traceback.print_exc()
            raise

        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.error(
                f"Database error occurred while deleting index: {index_id}"
            )
            traceback.print_exc()
            raise InternalServerError(
                description="Database Error: Failed to delete index."
            )

        except Exception:
            current_app.logger.error(
                f"Unexpected error occurred while deleting index: {index_id}"
            )
            traceback.print_exc()
            raise InternalServerError(
                description="Internal Server Error: Failed to delete index."
            )

        return make_response(jsonify(status=204), 204)


    def validate_request(self, request, schema):
        """Validate the request.

        Args:
            request (Request): The incoming request.
            schema (Schema): The schema to validate against.

        Returns:
            dict: The validated data.

        Raises:
            InvalidDataRESTError: If the request data is invalid.
            IndexBaseRESTError: If the Content-Type is not application/json.

        """
        if request.headers.get("Content-Type") != "application/json":
            current_app.logger.error("Invalid Content-Type for index creation.")
            raise IndexBaseRESTError(
                description="Bad Request: Content-Type must be application/json."
            )

        try:
            request_data = schema().load(request.json).data
        except ValidationError as ex:
            current_app.logger.error("Invalid payload for index creation.")
            traceback.print_exc()
            raise InvalidDataRESTError(
                description=f"Bad Request: Invalid payload, {ex}"
            ) from ex

        except BadRequest as ex:
            current_app.logger.error("Failed to parse JSON data for index creation.")
            traceback.print_exc()
            raise InvalidDataRESTError(
                description=f"Bad Request: Failed to parse provided."
            ) from ex

        return request_data


    def check_index_accessible(self, id):
        """Check if the user has access to the index.

        Args:
            id (int): The ID of the index.

        Returns:
            Index: The index object if the user has access.

        Raises:
            IndexNotFound404Error: If the index is not found.
            IndexDeletedRESTError: If the index is deleted.
            PermissionError: If the user does not have access to the index.

        """
        if not id:
            if (
                id == 0
                and any(
                    role.name == current_app.config.get(
                        "WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY"
                    )
                    for role in getattr(current_user, 'roles', [])
                )
            ):
                msg = "Community Administrators cannot access root index."
                current_app.logger.error(msg)
                raise PermissionError(
                    description=f"Permission denied: {msg}"
                )
            return None

        index = self.record_class.get_index(id, with_deleted=True)
        if not index:
            msg = f"Index not found: {id}."
            current_app.logger.error(msg)
            raise IndexNotFound404Error(description=msg)
        if index.is_deleted:
            msg = f"Index is deleted: {id}."
            current_app.logger.error(msg)
            raise IndexNotFound404Error(description=msg)

        lst = {
            column.name: getattr(index, column.name)
            for column in index.__table__.columns
        }
        if not can_admin_access_index(lst):
            current_app.logger.error(
                f"User does not have access to index: {id}"
            )
            raise PermissionError(
                description=f"Permission denied: Cannot access index {id}"
            )

        return index


    def save_redis(self):
        """Save index tree to Redis."""
        langs = AdminLangSettings.get_registered_language()
        tree = self.record_class.get_index_tree(lang="other_lang")
        for lang in langs:
            lang_code = lang["lang_code"]
            if lang_code == "ja":
                tree_ja = self.record_class.get_index_tree(lang="ja")
                save_index_trees_to_redis(tree_ja, lang=lang_code)
            else:
                save_index_trees_to_redis(tree, lang=lang_code)


    def _get_allowed_group_roles(self, index_info):
        """Convert group strings to allowed group roles.
        Args:
            index_info (dict): The index information containing group strings.
        Returns:
            dict: A dictionary with allowed group roles.
        """
        def _get_allowed_list(self, group_str): 
            """Convert group string to allowed group roles."""
            return {
                "allow": [{"id": role} for role in group_str.split(",")]
            } if group_str else {}

        # Convert group strings to allowed group roles
        allowed_roles_groups = {}
        if "browsing_group" in index_info:
            allowed_roles_groups["browsing_group"] = _get_allowed_list(
                self, index_info["browsing_group"]
            )
        if "contribute_group" in index_info:
            allowed_roles_groups["contribute_group"] = _get_allowed_list(
                self, index_info["contribute_group"]
            )
        if "browsing_role" in index_info:
            allowed_roles_groups["browsing_role"] = _get_allowed_list(
                self, index_info["browsing_role"]
            )
        if "contribute_role" in index_info:
            allowed_roles_groups["contribute_role"] = _get_allowed_list(
                self, index_info["contribute_role"]
            )
        return allowed_roles_groups
